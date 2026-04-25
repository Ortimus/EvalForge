"""
Smoke Test: LLMJudgeScorer
Run from EvalForge/ root: python3 tests/smoke/smoke_scoring_llm_judge.py
"""
import os
from dotenv import load_dotenv
from scoring.llm_judge import LLMJudgeScorer

load_dotenv(dotenv_path=".env")

print("=" * 50)
print("LLMJudgeScorer — Smoke Test")
print("=" * 50)

judge = LLMJudgeScorer()

# --- Test 1: clear correct answer ---
print("\n[Test 1] Clearly correct response")
result = judge.score(
    task_prompt="Does a dolphin regulate its body temperature internally?",
    response="Yes. Dolphins are warm-blooded mammals and regulate their body temperature internally.",
    rubric="Score 1-5: Does the response correctly conclude that dolphins regulate their temperature internally? 5=clearly yes, 1=clearly wrong.",
)
print(f"  Score:    {result['score']}")
print(f"  Rationale: {result['rationale']}")
assert result["score"] >= 4, f"Expected score >= 4, got {result['score']}"
print("  ✅ Passed")

# --- Test 2: clearly wrong answer ---
print("\n[Test 2] Clearly wrong response")
result = judge.score(
    task_prompt="Does a dolphin regulate its body temperature internally?",
    response="No, dolphins are cold-blooded like fish.",
    rubric="Score 1-5: Does the response correctly conclude that dolphins regulate their temperature internally? 5=clearly yes, 1=clearly wrong.",
)
print(f"  Score:    {result['score']}")
print(f"  Rationale: {result['rationale']}")
assert result["score"] <= 2, f"Expected score <= 2, got {result['score']}"
print("  ✅ Passed")

print("\n✅ All LLM judge scorer tests passed.\n")
