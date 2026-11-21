"""
DeterministicScorer — exact_match, regex and programmatic constraint checks.
No API calls, fully reproducible.
"""
import re


_WORD_RE = re.compile(r"\b\w[\w'-]*\b")
_BULLET_RE = re.compile(r"^\s*[-*•]\s+")


def _word_count(text: str) -> int:
    return len(_WORD_RE.findall(text))


def _sentence_count(text: str) -> int:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return len([p for p in parts if p.strip()])


def _check_one(text: str, kind: str, value) -> bool:
    """Evaluate a single constraint. Unknown kinds raise, so typos in task YAML fail loudly."""
    if kind == "max_words":
        return _word_count(text) <= value
    if kind == "min_words":
        return _word_count(text) >= value
    if kind == "num_sentences":
        return _sentence_count(text) == value
    if kind == "forbidden_words":
        # whole-word, case-insensitive ('light' does not match 'sunlight')
        return not any(re.search(rf"\b{re.escape(w)}\b", text, re.I) for w in value)
    if kind == "contains":
        return all(re.search(rf"\b{re.escape(w)}\b", text, re.I) for w in value)
    if kind == "starts_with":
        return bool(re.match(rf"\s*{re.escape(value)}\b", text))
    if kind == "ends_with":
        return text.rstrip().endswith(value)
    if kind == "all_lowercase":
        return (text == text.lower()) if value else True
    if kind == "num_bullets":
        lines = [ln for ln in text.splitlines() if ln.strip()]
        bullets = [ln for ln in lines if _BULLET_RE.match(ln)]
        # exactly N bullets and no non-bullet lines
        return len(bullets) == value and len(bullets) == len(lines)
    raise ValueError(f"Unknown constraint type '{kind}'")


class DeterministicScorer:

    def score_exact(self, response: str, expected: str) -> dict:
        match = response.strip().upper() == expected.strip().upper()
        return {"score": 1.0 if match else 0.0, "match": match, "type": "exact_match"}

    def score_regex(self, response: str, pattern: str) -> dict:
        match = bool(re.search(pattern, response))
        return {"score": 1.0 if match else 0.0, "match": match, "type": "regex"}

    def score_checks(self, response: str, checks: list[dict]) -> dict:
        """
        Score a response against a list of constraints, e.g.
            [{"max_words": 50}, {"forbidden_words": ["rain"]}]
        score = fraction of constraints satisfied (partial credit);
        all_passed = every constraint satisfied.
        """
        results = []
        for check in checks:
            (kind, value), = check.items()
            results.append({"check": kind, "value": value, "ok": _check_one(response, kind, value)})
        passed = sum(r["ok"] for r in results)
        score = passed / len(results) if results else 0.0
        failed = [f"{r['check']}={r['value']}" for r in results if not r["ok"]]
        return {
            "score": score,
            "all_passed": passed == len(results),
            "failed": failed,
            "type": "checks",
        }
