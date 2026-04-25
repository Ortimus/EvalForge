"""
EvalForge — Master Smoke Test Runner
Runs all smoke tests in sequence and summarizes results.
Run from EvalForge/ root: python3 tests/smoke/run_all.py
"""
import subprocess
import sys
from pathlib import Path

SMOKE_DIR = Path(__file__).parent

TESTS = [
    ("Deterministic Scorer", "smoke_scoring_deterministic.py"),
    ("LLM Judge Scorer",     "smoke_scoring_llm_judge.py"),
    ("Model Adapters",       "smoke_adapters.py"),
    ("FastAPI Endpoints",    "smoke_api.py"),
]

results = []

print("\n" + "=" * 55)
print("  EvalForge — Smoke Test Suite")
print("=" * 55)

for name, filename in TESTS:
    path = SMOKE_DIR / filename
    print(f"\n▶  Running: {name}")
    print("-" * 55)
    result = subprocess.run(
        [sys.executable, str(path)],
        capture_output=False,   # stream output live
    )
    passed = result.returncode == 0
    results.append((name, passed))

print("\n" + "=" * 55)
print("  Summary")
print("=" * 55)
for name, passed in results:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status}  {name}")

total = len(results)
passed_count = sum(1 for _, p in results if p)
print(f"\n  {passed_count}/{total} tests passed")
print("=" * 55 + "\n")

if passed_count < total:
    sys.exit(1)
