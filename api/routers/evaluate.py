"""
POST /evaluate — runs a full evaluation pipeline:
  Adapter Factory → Task Loader → Eval Loop (N samples/task) → Scorer Dispatcher → MLflow

Scoring semantics
- Each task is run `samples` times; the task score is the mean over samples.
- A sample that raises (API failure, unparseable judge output) is an ERROR, not a
  zero: it is excluded from scoring and counted in `errors`. Scoring failures as
  0 would silently penalise a model for our infrastructure problems.
- Category scores average task scores; the 95% CI is computed across tasks.
- Tier scores ('<category>/<difficulty>') are the discriminative view: models that
  tie overall usually separate on the hard tier.
"""
from __future__ import annotations
import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from adapters.factory import get_adapter
from tasks.loader import load_task_set
from scoring.dispatcher import ScorerDispatcher
from scoring.stats import combine_means, mean_ci
from tracking.mlflow_tracker import EvalTracker

router = APIRouter()
dispatcher = ScorerDispatcher()
tracker = EvalTracker()


class EvaluateRequest(BaseModel):
    provider: str           # "anthropic" | "openai" | "huggingface" | "ollama"
    model_id: str | None = None   # omitted → provider default from configs/models.yaml
    task_set: str = "default"     # see tasks.loader.load_task_set for selectors
    samples: int = Field(default=1, ge=1, le=10)   # repeated runs per task
    api_key: str | None = None


class TaskResult(BaseModel):
    task_id: str
    category: str
    difficulty: str
    score: float                  # mean over successful samples
    raw_score: float
    passed: bool                  # pass_rate >= 0.5
    pass_rate: float
    sample_scores: list[float]
    errors: int                   # samples excluded because they raised
    error: str | None = None      # last error message, if any
    rationale: str                # from the first successful sample
    latency_ms: float             # mean over successful samples
    response: str                 # first successful sample's response
    worst_response: str = ""      # response of the lowest-scoring sample (for debugging failures)


class EvaluateResponse(BaseModel):
    run_id: str
    model_id: str
    provider: str
    task_set: str
    samples: int
    overall_score: float
    overall_ci: float             # 95% CI half-width
    category_scores: dict[str, float]
    category_ci: dict[str, float]
    tier_scores: dict[str, float]  # "<category>/<difficulty>" -> mean score
    task_results: list[TaskResult]
    total_tasks: int              # tasks with at least one scored sample
    tasks_passed: int
    total_errors: int
    tasks_skipped: list[str]      # tasks where every sample errored


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


@router.post("/", response_model=EvaluateResponse)
def run_evaluation(request: EvaluateRequest):

    # --- Stage 1: resolve adapter ---
    try:
        adapter = get_adapter(
            provider=request.provider,
            model_id=request.model_id,
            api_key=request.api_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # --- Stage 2: load tasks ---
    tasks = load_task_set(request.task_set)
    if not tasks:
        raise HTTPException(
            status_code=404,
            detail=f"No tasks found for task_set='{request.task_set}'"
        )

    # --- Stage 3: start MLflow run ---
    metadata = adapter.get_metadata()
    run = tracker.start_run(
        model_metadata={
            "provider": metadata.provider,
            "model_id": metadata.model_id,
            "version": metadata.version,
            "samples": request.samples,
        },
        task_set=request.task_set,
    )
    run_id = run.info.run_id

    task_results: list[TaskResult] = []
    skipped: list[str] = []
    last_error = ""

    try:
        # --- Stage 4: eval loop ---
        for task in tasks:
            scores, raws, latencies, passes = [], [], [], []
            errors, task_error = 0, None
            first_response, first_rationale = "", ""
            worst_response, worst_score = "", None

            for _ in range(request.samples):
                t0 = time.perf_counter()
                try:
                    response = adapter.generate(task.prompt_template)
                    latency_ms = (time.perf_counter() - t0) * 1000
                    scored = dispatcher.dispatch(task, response)
                except Exception as e:           # API failure or bad judge output
                    errors += 1
                    task_error = f"{type(e).__name__}: {e}"
                    last_error = task_error
                    continue

                if not scores:
                    first_response, first_rationale = response, scored["rationale"]
                if worst_score is None or scored["score"] < worst_score:
                    worst_score, worst_response = scored["score"], response
                scores.append(scored["score"])
                raws.append(scored["raw_score"])
                latencies.append(latency_ms)
                passes.append(1.0 if scored["passed"] else 0.0)

            if not scores:
                skipped.append(task.task_id)
                task_results.append(TaskResult(
                    task_id=task.task_id, category=task.category, difficulty=task.difficulty,
                    score=0.0, raw_score=0.0, passed=False, pass_rate=0.0, sample_scores=[],
                    errors=errors, error=task_error, rationale="", latency_ms=0.0, response="",
                ))
                continue

            task_score, mean_latency = _mean(scores), _mean(latencies)
            tracker.log_task_result(
                task_id=task.task_id,
                category=task.category,
                score=task_score,
                latency_ms=mean_latency,
            )
            task_results.append(TaskResult(
                task_id=task.task_id, category=task.category, difficulty=task.difficulty,
                score=round(task_score, 4), raw_score=round(_mean(raws), 4),
                passed=_mean(passes) >= 0.5, pass_rate=round(_mean(passes), 4),
                sample_scores=[round(s, 4) for s in scores],
                errors=errors, error=task_error,
                rationale=first_rationale, latency_ms=round(mean_latency, 2),
                response=first_response,
                worst_response=worst_response if min(scores) < 1.0 else "",
            ))

        scored_results = [t for t in task_results if t.sample_scores]
        if not scored_results:
            raise HTTPException(
                status_code=502,
                detail=f"Every sample failed. Last error: {last_error}",
            )

        # --- Stage 5: aggregate ---
        by_cat: dict[str, list[float]] = defaultdict(list)
        by_tier: dict[str, list[float]] = defaultdict(list)
        for t in scored_results:
            by_cat[t.category].append(t.score)
            by_tier[f"{t.category}/{t.difficulty}"].append(t.score)

        cat_stats = {cat: mean_ci(vals) for cat, vals in by_cat.items()}
        category_scores = {c: round(m, 4) for c, (m, _) in cat_stats.items()}
        category_ci = {c: round(h, 4) for c, (_, h) in cat_stats.items()}
        tier_scores = {k: round(_mean(v), 4) for k, v in sorted(by_tier.items())}
        overall, overall_hw = combine_means(list(cat_stats.values()))

        tracker.log_aggregate(
            category_scores,
            category_ci=category_ci,
            tier_scores=tier_scores,
            overall_ci=overall_hw,
        )
    finally:
        tracker.end_run()

    return EvaluateResponse(
        run_id=run_id,
        model_id=metadata.model_id,
        provider=metadata.provider,
        task_set=request.task_set,
        samples=request.samples,
        overall_score=round(overall, 4),
        overall_ci=round(overall_hw, 4),
        category_scores=category_scores,
        category_ci=category_ci,
        tier_scores=tier_scores,
        task_results=task_results,
        total_tasks=len(scored_results),
        tasks_passed=sum(1 for t in scored_results if t.passed),
        total_errors=sum(t.errors for t in task_results),
        tasks_skipped=skipped,
    )
