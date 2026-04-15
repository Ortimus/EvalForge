"""
EvalTracker — thin MLflow wrapper that enforces consistent logging schema
across all evaluation runs.
"""
import mlflow
from datetime import datetime


class EvalTracker:

    def __init__(self, experiment_name: str = "evalforge"):
        mlflow.set_experiment(experiment_name)

    def start_run(self, model_metadata: dict, task_set: str):
        run = mlflow.start_run(run_name=f"{model_metadata['model_id']}_{datetime.utcnow():%Y%m%d_%H%M%S}")
        mlflow.log_params(model_metadata)
        mlflow.log_param("task_set", task_set)
        return run

    def log_task_result(self, task_id: str, category: str, score: float, latency_ms: float):
        mlflow.log_metric(f"score_{task_id}", score)
        mlflow.log_metric(f"latency_ms_{task_id}", latency_ms)

    def log_aggregate(self, scores_by_category: dict):
        for category, score in scores_by_category.items():
            mlflow.log_metric(f"avg_{category}", score)
        mlflow.log_metric("overall_score", sum(scores_by_category.values()) / len(scores_by_category))

    def end_run(self):
        mlflow.end_run()
