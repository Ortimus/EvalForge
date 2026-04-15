"""
DeterministicScorer — exact_match and regex evaluation.
No API calls, fully reproducible.
"""
import re


class DeterministicScorer:

    def score_exact(self, response: str, expected: str) -> dict:
        match = response.strip().upper() == expected.strip().upper()
        return {"score": 1.0 if match else 0.0, "match": match, "type": "exact_match"}

    def score_regex(self, response: str, pattern: str) -> dict:
        match = bool(re.search(pattern, response))
        return {"score": 1.0 if match else 0.0, "match": match, "type": "regex"}
