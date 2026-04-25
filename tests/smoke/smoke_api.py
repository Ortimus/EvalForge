"""
Smoke Test: FastAPI endpoints
Requires uvicorn to be running: uvicorn api.main:app --reload --port 8000
Run from EvalForge/ root: python3 tests/smoke/smoke_api.py
"""
import sys
import requests

BASE = "http://localhost:8000"

print("=" * 50)
print("FastAPI Endpoints — Smoke Test")
print("=" * 50)

# --- Preflight: is the server up? ---
try:
    requests.get(BASE, timeout=3)
except requests.ConnectionError:
    print("\n❌ FastAPI is not running.")
    print("   Start it with: uvicorn api.main:app --reload --port 8000")
    sys.exit(1)

# --- /health ---
print("\n[GET /health]")
r = requests.get(f"{BASE}/health")
assert r.status_code == 200, f"Expected 200, got {r.status_code}"
data = r.json()
assert data["status"] == "ok"
print(f"  Response: {data}")
print("  ✅ Passed")

# --- /leaderboard ---
print("\n[GET /leaderboard]")
r = requests.get(f"{BASE}/leaderboard/")
assert r.status_code == 200, f"Expected 200, got {r.status_code}"
data = r.json()
assert "leaderboard" in data
print(f"  Response: {data}")
print("  ✅ Passed")

# --- /results/{run_id} ---
print("\n[GET /results/test-run-123]")
r = requests.get(f"{BASE}/results/test-run-123")
assert r.status_code == 200, f"Expected 200, got {r.status_code}"
data = r.json()
assert "run_id" in data
print(f"  Response: {data}")
print("  ✅ Passed")

# --- POST /evaluate ---
print("\n[POST /evaluate]")
payload = {
    "provider": "anthropic",
    "model_id": "claude-sonnet-4-20250514",
    "task_set": "default",
}
r = requests.post(f"{BASE}/evaluate/", json=payload)
assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
data = r.json()
assert "run_id" in data
print(f"  Response: {data}")
print("  ✅ Passed")

# --- POST /tasks ---
print("\n[POST /tasks]")
task = {
    "task_id": "smoke_test_task_001",
    "category": "logical_deduction",
    "difficulty": "easy",
    "prompt_template": "Is 2 + 2 = 4? Answer YES or NO.",
    "expected_answer": "YES",
    "evaluation_type": "exact_match",
}
r = requests.post(f"{BASE}/tasks/", json=task)
assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
data = r.json()
print(f"  Response: {data}")
print("  ✅ Passed")

print("\n✅ All FastAPI endpoint smoke tests passed.\n")
