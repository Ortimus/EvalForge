"""
Smoke Test: DeterministicScorer
Run from EvalForge/ root: python3 tests/smoke/smoke_scoring_deterministic.py
"""
from scoring.deterministic import DeterministicScorer

s = DeterministicScorer()

print("=" * 50)
print("DeterministicScorer — Smoke Test")
print("=" * 50)

# --- exact_match ---
print("\n[exact_match]")

result = s.score_exact("YES", "YES")
assert result["score"] == 1.0, f"FAIL: {result}"
print(f"  ✅ 'YES' vs 'YES'  → score: {result['score']}")

result = s.score_exact("No", "YES")
assert result["score"] == 0.0, f"FAIL: {result}"
print(f"  ✅ 'No'  vs 'YES'  → score: {result['score']}")

result = s.score_exact("yes", "YES")   # case-insensitive
assert result["score"] == 1.0, f"FAIL: {result}"
print(f"  ✅ 'yes' vs 'YES'  → score: {result['score']}  (case-insensitive)")

# --- regex ---
print("\n[regex]")

result = s.score_regex("The project name is Orion.", "(?i)orion")
assert result["score"] == 1.0, f"FAIL: {result}"
print(f"  ✅ 'Orion' found    → score: {result['score']}")

result = s.score_regex("The project name is Phoenix.", "(?i)orion")
assert result["score"] == 0.0, f"FAIL: {result}"
print(f"  ✅ 'Orion' missing  → score: {result['score']}")

print("\n✅ All deterministic scorer tests passed.\n")
