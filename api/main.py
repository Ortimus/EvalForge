"""
EvalForge FastAPI application entry point.
"""
#from dotenv import load_dotenv
#load_dotenv(dotenv_path=".env")   # must be before other imports

# Searches up the tree until it finds .env
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from fastapi import FastAPI
from api.routers import evaluate, results, leaderboard, tasks

import os
print("API KEY FOUND:", bool(os.getenv("ANTHROPIC_API_KEY")))

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