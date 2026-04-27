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
- MLflow UI:    http://localhost:5001
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

## Running with Docker Compose

```bash
docker compose up
```

Wait for this sequence in the logs before making requests:

```
postgres-1  | database system is ready to accept connections
mlflow-1    | Application startup complete.
api-1       | Application startup complete.        ← stack is ready
ui-1        | You can now view your Streamlit app
```

Services:
- FastAPI:  http://localhost:8000/docs
- MLflow:   http://localhost:5001
- Streamlit: http://localhost:8501

## MLflow Experiment Tracking

EvalForge uses MLflow to record every evaluation run. After submitting a run via
`POST /evaluate`, open the MLflow UI at `http://localhost:5001` and navigate to
the **evalforge** experiment to inspect results.

### What to expect in the MLflow UI

EvalForge logs custom metrics directly via the MLflow Tracking API. The built-in
MLflow tabs (Usage, Quality, Tool Calls) are designed for MLflow's native
`mlflow.evaluate()` API and will appear empty — this is expected. 

Navigate to **Experiments → evalforge → Evaluation runs** in the left sidebar
to see your runs. The built-in Usage/Quality/Tool Calls tabs will be empty —
all EvalForge data is in the **Evaluation runs** table and the run detail view.

#### Parameters tab
Records identifying metadata for the run:

| Parameter | Example |
|---|---|
| `provider` | `anthropic` |
| `model_id` | `claude-sonnet-4-20250514` |
| `version` | `unknown` |
| `task_set` | `default` |

#### Metrics tab
Records per-task scores and latencies, plus category and overall aggregates:

| Metric | Description |
|---|---|
| `score_{task_id}` | Normalised 0.0–1.0 score for each task |
| `latency_ms_{task_id}` | Response generation time in milliseconds |
| `avg_{category}` | Mean score across all tasks in a category |
| `overall_score` | Mean score across all categories |

#### Comparing runs
To compare two models side by side, select multiple runs in the experiment view
and click **Compare**. MLflow will render a parallel coordinates chart and metric
table across the selected runs — useful for seeing which cognitive categories
differ most between models or providers.

### Note on experiment deletion
MLflow performs soft deletes — deleting an experiment in the UI marks it as
deleted in the database but does not remove it. Attempting to recreate an
experiment with the same name will fail. If this happens, either restore the
experiment via the MLflow client or permanently remove it from the database
before recreating it.

To delete it from the underlying postgres database, run:
```
docker compose exec postgres psql -U evalforge -d evalforge -c "
  DELETE FROM params WHERE run_uuid IN (SELECT run_uuid FROM runs WHERE experiment_id = 1);
  DELETE FROM latest_metrics WHERE run_uuid IN (SELECT run_uuid FROM runs WHERE experiment_id = 1);
  DELETE FROM metrics WHERE run_uuid IN (SELECT run_uuid FROM runs WHERE experiment_id = 1);
  DELETE FROM tags WHERE run_uuid IN (SELECT run_uuid FROM runs WHERE experiment_id = 1);
  DELETE FROM runs WHERE experiment_id = 1;
  DELETE FROM experiments WHERE experiment_id = 1;
"
```