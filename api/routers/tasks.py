"""POST /tasks — register a new task into the YAML registry."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/")
def register_task(task: dict):
    # TODO: validate + write to tasks/ directory
    return {"status": "registered"}
