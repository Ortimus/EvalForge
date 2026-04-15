"""GET /results/{run_id} — fetch per-task breakdown for a run."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/{run_id}")
def get_results(run_id: str):
    # TODO: query MLflow by run_id
    return {"run_id": run_id, "results": []}
