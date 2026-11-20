"""
End-to-end test of POST /evaluate with a stub model and a stub judge:
no network, no API cost. MLflow runs against a temp file store.

Covers: perfect-score aggregation, repeated sampling, error isolation
(failed samples are excluded, not scored as 0), the all-fail path, and that the
MLflow run is always closed.
"""
import mlflow
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from adapters.base import BaseModelAdapter, ModelMetadata
from api.routers import evaluate
from tasks.loader import load_all_tasks
from tests.unit.test_tasks import _compliant_response

TASKS = load_all_tasks()
ORACLE = {}          # prompt -> correct response
WRONG = "Answer: zzzz"
for t in TASKS:
    if t.evaluation_type == "regex":
        ORACLE[t.prompt_template] = f"Answer: {t.expected_answer}"
    elif t.evaluation_type == "exact_match":
        ORACLE[t.prompt_template] = t.expected_answer
    elif t.evaluation_type == "checks":
        ORACLE[t.prompt_template] = _compliant_response(t.checks)
    else:                                   # llm_judge: judge is stubbed
        ORACLE[t.prompt_template] = "whatever"


class StubAdapter(BaseModelAdapter):
    def __init__(self, wrong_every=None, fail_prompt=None):
        self.calls = 0
        self.wrong_every = wrong_every
        self.fail_prompt = fail_prompt

    def generate(self, prompt, **kwargs):
        self.calls += 1
        if prompt == self.fail_prompt:
            raise RuntimeError("simulated API outage")
        if self.wrong_every and self.calls % self.wrong_every == 0:
            return WRONG
        return ORACLE[prompt]

    def get_metadata(self):
        return ModelMetadata(provider="stub", model_id="stub-1")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", str(tmp_path / "mlruns"))
    # recent MLflow versions refuse the file store unless explicitly allowed
    monkeypatch.setenv("MLFLOW_ALLOW_FILE_STORE", "true")
    monkeypatch.setattr(evaluate.dispatcher._judge, "score",
                        lambda **kw: {"score": 5, "rationale": "stub judge"})
    app = FastAPI()
    app.include_router(evaluate.router, prefix="/evaluate")
    return TestClient(app)


def use_adapter(monkeypatch, adapter):
    monkeypatch.setattr(evaluate, "get_adapter", lambda **kw: adapter)


def post(client, **body):
    return client.post("/evaluate/", json={"provider": "stub", **body})


# --------------------------------------------------------------------------- #
def test_perfect_model_scores_one_everywhere(client, monkeypatch):
    use_adapter(monkeypatch, StubAdapter())
    r = post(client)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["overall_score"] == 1.0 and body["overall_ci"] == 0.0
    assert body["total_tasks"] == len(TASKS) and body["total_errors"] == 0
    assert body["tasks_skipped"] == []
    assert all(v == 1.0 for v in body["category_scores"].values())
    assert "working_memory/hard" in body["tier_scores"]
    assert "instruction_following/easy" in body["tier_scores"]
    assert mlflow.active_run() is None


def test_repeated_sampling_gives_fractional_scores_and_ci(client, monkeypatch):
    use_adapter(monkeypatch, StubAdapter(wrong_every=3))     # one wrong sample of every three
    body = post(client, task_set="logical_deduction", samples=3).json()
    regex_tasks = [t for t in body["task_results"] if t["task_id"].startswith("logic_")]
    assert regex_tasks and all(len(t["sample_scores"]) == 3 for t in regex_tasks)
    # exactly one of each task's three consecutive calls is wrong
    assert all(abs(t["score"] - 2 / 3) < 1e-3 for t in regex_tasks)
    assert body["samples"] == 3


def test_failed_samples_are_excluded_not_zeroed(client, monkeypatch):
    victim = next(t for t in TASKS if t.task_id == "logic_hard_01")
    adapter = StubAdapter(fail_prompt=victim.prompt_template)
    use_adapter(monkeypatch, adapter)
    body = post(client, task_set="logical_deduction", samples=2).json()

    assert body["tasks_skipped"] == ["logic_hard_01"]
    assert body["total_errors"] == 2
    skipped = next(t for t in body["task_results"] if t["task_id"] == "logic_hard_01")
    assert skipped["errors"] == 2 and "simulated API outage" in skipped["error"]
    # the outage must not drag the category below a perfect score
    assert body["category_scores"]["logical_deduction"] == 1.0
    assert body["total_tasks"] == len([t for t in TASKS if t.category == "logical_deduction"]) - 1


def test_judge_failure_does_not_crash_the_run(client, monkeypatch):
    use_adapter(monkeypatch, StubAdapter())

    def boom(**kw):
        raise ValueError("judge returned prose, not JSON")
    monkeypatch.setattr(evaluate.dispatcher._judge, "score", boom)

    body = post(client, task_set="instruction_following").json()
    # generated tasks use programmatic checks; only the legacy judge task errors
    assert body["tasks_skipped"] == ["instruction_following_001"]
    assert body["category_scores"]["instruction_following"] == 1.0


def test_all_samples_failing_returns_502_and_closes_run(client, monkeypatch):
    class Down(StubAdapter):
        def generate(self, prompt, **kw):
            raise RuntimeError("down")
    use_adapter(monkeypatch, Down())
    r = post(client, task_set="working_memory:easy")
    assert r.status_code == 502 and "down" in r.json()["detail"]
    assert mlflow.active_run() is None


def test_unknown_task_set_404(client, monkeypatch):
    use_adapter(monkeypatch, StubAdapter())
    assert post(client, task_set="nope").status_code == 404


def test_samples_bounds_validated(client, monkeypatch):
    use_adapter(monkeypatch, StubAdapter())
    assert post(client, samples=0).status_code == 422
    assert post(client, samples=11).status_code == 422
