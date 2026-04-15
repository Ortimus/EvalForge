"""GET /leaderboard — ranked model comparison across all runs."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_leaderboard():
    # TODO: aggregate MLflow runs into ranked table
    return {"leaderboard": []}
