"""
EvalForge FastAPI application entry point.
"""
from fastapi import FastAPI
from api.routers import evaluate, results, leaderboard, tasks

app = FastAPI(
    title="EvalForge",
    description="LLM Evaluation Intelligence Platform",
    version="0.1.0",
)

app.include_router(evaluate.router, prefix="/evaluate", tags=["evaluate"])
app.include_router(results.router, prefix="/results", tags=["results"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "evalforge"}
