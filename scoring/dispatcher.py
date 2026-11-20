"""
ScorerDispatcher — routes each task to the correct scorer based on
evaluation_type. The eval loop calls dispatch() and stays scorer-agnostic.
"""
from __future__ import annotations
from tasks.loader import TaskConfig
from scoring.deterministic import DeterministicScorer
from scoring.llm_judge import LLMJudgeScorer


class ScorerDispatcher:

    def __init__(self):
        self._deterministic = DeterministicScorer()
        self._judge = LLMJudgeScorer()          # only calls the API when a task needs it

    def dispatch(self, task: TaskConfig, response: str) -> dict:
        """
        Route to the correct scorer and return a normalised result dict:
        {
            score:      float 0.0–1.0 (llm_judge's 1–5 is rescaled),
            raw_score:  the scorer's native score,
            type:       evaluation_type used,
            rationale:  explanation (llm_judge: rationale; checks: failed constraints),
            passed:     whether the response fully meets the task,
        }
        """
        eval_type = task.evaluation_type

        if eval_type == "exact_match":
            result = self._deterministic.score_exact(response, task.expected_answer)
            return self._normalise(result, eval_type)

        if eval_type == "regex":
            result = self._deterministic.score_regex(response, task.answer_pattern)
            return self._normalise(result, eval_type)

        if eval_type == "checks":
            result = self._deterministic.score_checks(response, task.checks)
            return self._normalise(result, eval_type)

        if eval_type == "llm_judge":
            result = self._judge.score(
                response=response,
                rubric=task.judge_rubric,
                task_prompt=task.prompt_template,
            )
            return self._normalise(result, eval_type)

        raise ValueError(
            f"Unknown evaluation_type '{eval_type}' in task '{task.task_id}'. "
            f"Valid options: exact_match, regex, checks, llm_judge"
        )

    def _normalise(self, result: dict, eval_type: str) -> dict:
        """Ensure every result dict has the same shape regardless of scorer."""
        score = result.get("score", 0.0)

        # llm_judge returns 1-5; rescale to 0.0-1.0 for consistent aggregation
        if eval_type == "llm_judge":
            normalised_score = (score - 1) / 4.0
            passed = normalised_score >= 0.5
            rationale = result.get("rationale", "")
        elif eval_type == "checks":
            normalised_score = float(score)
            passed = bool(result.get("all_passed"))   # partial credit in score, strict pass
            failed = result.get("failed", [])
            rationale = f"failed: {', '.join(failed)}" if failed else ""
        else:
            normalised_score = float(score)
            passed = normalised_score >= 0.5
            rationale = ""

        return {
            "score": normalised_score,
            "raw_score": score,
            "type": eval_type,
            "rationale": rationale,
            "passed": passed,
        }
