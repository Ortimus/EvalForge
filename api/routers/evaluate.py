"""POST /evaluate — submit a model + task_set for evaluation."""
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()


class EvaluateRequest(BaseModel):
    provider: str          # "anthropic" | "openai" | "huggingface" | "ollama"
    model_id: str
    task_set: str = "default"
    api_key: str | None = None


@router.post("/")
def submit_evaluation(request: EvaluateRequest, background_tasks: BackgroundTasks):
    # TODO: wire up adapter factory + scoring pipeline
    run_id = "placeholder_run_id"
    return {"run_id": run_id, "status": "queued"}
