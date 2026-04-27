"""
EvalTracker — thin MLflow wrapper that enforces consistent logging schema
across all evaluation runs.

Key design decisions:
- set_tracking_uri() and set_experiment() are called inside start_run(), not
  in __init__(). This avoids a timing race where the module is imported and
  EvalTracker() instantiated before the MLflow server is ready (especially
  relevant in Docker where the api container can start before mlflow is healthy).
- mlflow.end_run() is called defensively at the top of start_run() to clear
  any stale active run left over from a previous failed request.
"""
import os
from datetime import datetime
import mlflow


class EvalTracker:

    def __init__(self, experiment_name: str = "evalforge"):
        self.experiment_name = experiment_name
        # Intentionally no MLflow calls here — server may not be ready yet

    def start_run(self, model_metadata: dict, task_set: str):
        # Resolve tracking URI at request time, not at module load time
        mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "mlruns"))
        mlflow.set_experiment(self.experiment_name)
        mlflow.end_run()  # safety guard: clear any stale active run

        run = mlflow.start_run(
            run_name=f"{model_metadata['model_id']}_{datetime.utcnow():%Y%m%d_%H%M%S}"
        )
        mlflow.log_params(model_metadata)
        mlflow.log_param("task_set", task_set)
        return run

    def log_task_result(self, task_id: str, category: str, score: float, latency_ms: float):
        mlflow.log_metric(f"score_{task_id}", score)
        mlflow.log_metric(f"latency_ms_{task_id}", latency_ms)

    def log_aggregate(self, scores_by_category: dict):
        for category, score in scores_by_category.items():
            mlflow.log_metric(f"avg_{category}", score)
        mlflow.log_metric(
            "overall_score",
            sum(scores_by_category.values()) / len(scores_by_category)
        )

    def end_run(self):
        mlflow.end_run()
