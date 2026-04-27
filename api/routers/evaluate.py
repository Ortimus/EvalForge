"""
POST /evaluate — runs a full evaluation pipeline:
  Adapter Factory → Task Loader → Eval Loop → Scorer Dispatcher → MLflow
"""
from __future__ import annotations
import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from adapters.factory import get_adapter
from tasks.loader import load_task_set
from scoring.dispatcher import ScorerDispatcher
from tracking.mlflow_tracker import EvalTracker

router = APIRouter()
dispatcher = ScorerDispatcher()
tracker = EvalTracker()


class EvaluateRequest(BaseModel):
    provider: str           # "anthropic" | "openai" | "huggingface" | "ollama"
    model_id: str
    task_set: str = "default"
    api_key: str | None = None


class TaskResult(BaseModel):
    task_id: str
    category: str
    score: float
    raw_score: float
    passed: bool
    rationale: str
    latency_ms: float
    response: str


class EvaluateResponse(BaseModel):
    run_id: str
    model_id: str
    provider: str
    task_set: str
    overall_score: float
    category_scores: dict[str, float]
    task_results: list[TaskResult]
    total_tasks: int
    tasks_passed: int


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
        },
        task_set=request.task_set,
    )

    # --- Stage 4: eval loop ---
    task_results = []
    scores_by_category: dict[str, list[float]] = defaultdict(list)

    for task in tasks:
        # Generate response and measure latency
        t0 = time.perf_counter()
        try:
            response = adapter.generate(task.prompt_template)
        except Exception as e:
            response = f"[ERROR: {str(e)}]"
        latency_ms = (time.perf_counter() - t0) * 1000

        # Score
        scored = dispatcher.dispatch(task, response)

        # Log per-task to MLflow
        tracker.log_task_result(
            task_id=task.task_id,
            category=task.category,
            score=scored["score"],
            latency_ms=latency_ms,
        )

        scores_by_category[task.category].append(scored["score"])
        task_results.append(TaskResult(
            task_id=task.task_id,
            category=task.category,
            score=scored["score"],
            raw_score=scored["raw_score"],
            passed=scored["passed"],
            rationale=scored["rationale"],
            latency_ms=round(latency_ms, 2),
            response=response,
        ))

    # --- Stage 5: aggregate + close MLflow run ---
    category_scores = {
        cat: round(sum(scores) / len(scores), 4)
        for cat, scores in scores_by_category.items()
    }
    overall_score = round(
        sum(category_scores.values()) / len(category_scores), 4
    )

    tracker.log_aggregate(category_scores)
    run_id = run.info.run_id
    tracker.end_run()

    return EvaluateResponse(
        run_id=run_id,
        model_id=metadata.model_id,
        provider=metadata.provider,
        task_set=request.task_set,
        overall_score=overall_score,
        category_scores=category_scores,
        task_results=task_results,
        total_tasks=len(task_results),
        tasks_passed=sum(1 for t in task_results if t.passed),
    )
