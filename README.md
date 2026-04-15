# EvalForge 🔬

**LLM Evaluation Intelligence Platform** — systematic, reproducible cognitive profiling of language models across a curated task taxonomy.

## Architecture

```
Task Registry (YAML) → Model Adapter → Scoring Engine → MLflow → FastAPI → Streamlit
```

## Cognitive Categories

| Category | Evaluation Type |
|---|---|
| Logical Deduction | exact_match |
| Working Memory | regex |
| Instruction Following | llm_judge |
| Calibration | statistical |
| Analogical Reasoning | llm_judge |

## Quick Start

```bash
cp .env.example .env          # add your API keys
docker compose up --build     # starts mlflow + api + ui
```

- FastAPI docs: http://localhost:8000/docs
- MLflow UI:    http://localhost:5000
- Streamlit:    http://localhost:8501

## Project Structure

```
adapters/     Model provider adapters (Anthropic, OpenAI, HuggingFace, Ollama)
tasks/        YAML task registry
scoring/      Deterministic + LLM-judge scoring engines
api/          FastAPI application
ui/           Streamlit dashboard
tracking/     MLflow helpers
configs/      Model and scoring configuration
tests/        Unit and integration tests
docker/       Dockerfiles
```
