"""
Validates the generated benchmark WITHOUT calling any model.

- every task file loads and has the fields its evaluation_type needs
- regex patterns compile, accept the correct answer line, and reject wrong ones
- logic and memory answers are re-derived by independent solvers that parse the
  prompt text, so a generator bug can't hide behind its own expected_answer
- every instruction-following constraint set is jointly satisfiable (we build a
  compliant response for each and require a perfect score)

Run: python -m pytest tests/unit -q
"""
import re
from collections import Counter

import pytest

from scoring.deterministic import DeterministicScorer
from tasks.generate import END_PHRASE
from tasks.loader import DIFFICULTIES, load_all_tasks, load_task_set

TASKS = load_all_tasks()
SCORER = DeterministicScorer()


def by_category(cat):
    return [t for t in TASKS if t.category == cat]


# --------------------------------------------------------------------------- #
def test_task_ids_unique():
    ids = [t.task_id for t in TASKS]
    assert len(ids) == len(set(ids))


def test_every_category_has_every_tier():
    counts = Counter((t.category, t.difficulty) for t in TASKS)
    for cat in {t.category for t in TASKS}:
        for tier in DIFFICULTIES:
            assert counts[(cat, tier)] >= 1, f"{cat} has no {tier} task"


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.task_id)
def test_task_has_required_fields(task):
    assert task.difficulty in DIFFICULTIES
    if task.evaluation_type == "regex":
        re.compile(task.answer_pattern)
    elif task.evaluation_type == "exact_match":
        assert task.expected_answer
    elif task.evaluation_type == "checks":
        assert task.checks
    elif task.evaluation_type == "llm_judge":
        assert task.judge_rubric
    else:
        pytest.fail(f"unknown evaluation_type {task.evaluation_type}")


def test_task_set_selectors():
    assert len(load_task_set("default")) == len(TASKS)
    hard = load_task_set("difficulty:hard")
    assert hard and all(t.difficulty == "hard" for t in hard)
    wm = load_task_set("working_memory")
    assert wm and all(t.category == "working_memory" for t in wm)
    wmh = load_task_set("working_memory:hard")
    assert wmh and all(t.category == "working_memory" and t.difficulty == "hard" for t in wmh)


# --------------------------------------------------------------------------- #
# regex answer tasks: accept right, reject wrong
# --------------------------------------------------------------------------- #
REGEX_GENERATED = [t for t in TASKS if t.evaluation_type == "regex" and t.task_id.split("_")[0] in
                   {"logic", "memory", "analogy"}]


@pytest.mark.parametrize("task", REGEX_GENERATED, ids=lambda t: t.task_id)
def test_regex_accepts_correct_and_rejects_wrong(task):
    right = task.expected_answer
    assert SCORER.score_regex(f"Some reasoning.\nAnswer: {right}", task.answer_pattern)["score"] == 1.0
    assert SCORER.score_regex(f"Some reasoning.\n**Answer: {right}**", task.answer_pattern)["score"] == 1.0
    assert SCORER.score_regex(f"Answer: {right}.", task.answer_pattern)["score"] == 1.0
    assert SCORER.score_regex("Answer: zzzz", task.answer_pattern)["score"] == 0.0
    # the LAST answer line counts: a correct early answer then a wrong final one fails
    assert SCORER.score_regex(f"Answer: {right}\nActually, Answer: zzzz", task.answer_pattern)["score"] == 0.0
    # no answer line at all
    assert SCORER.score_regex(f"I think it is {right}", task.answer_pattern)["score"] == 0.0


# --------------------------------------------------------------------------- #
# independent solvers
# --------------------------------------------------------------------------- #
def _solve_logic(prompt: str) -> str:
    taller = []          # (a, b): a taller than b
    for a, b in re.findall(r"(\w+) is taller than (\w+)\.", prompt):
        taller.append((a, b))
    for b, a in re.findall(r"(\w+) is shorter than (\w+)\.", prompt):
        taller.append((a, b))
    people = {p for pair in taller for p in pair}
    # order by number of people each person is (transitively) taller than
    beats = {p: set() for p in people}
    for _ in range(len(people)):
        for a, b in taller:
            beats[a] |= {b} | beats[b]
    ranked = sorted(people, key=lambda p: -len(beats[p]))
    q = re.search(r"Who is the (\w+)?\s*(tallest|shortest)\?", prompt)
    ordinal, kind = q.group(1), q.group(2)
    if kind == "shortest":
        return ranked[-1]
    if ordinal is None:
        return ranked[0]
    ords = {"second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8}
    return ranked[ords[ordinal] - 1]


@pytest.mark.parametrize("task", by_category("logical_deduction"), ids=lambda t: t.task_id)
def test_logic_answer_matches_independent_solver(task):
    if not task.task_id.startswith("logic_"):
        pytest.skip("hand-written legacy task")
    assert _solve_logic(task.prompt_template) == task.expected_answer


def _solve_memory(prompt: str) -> str:
    records = dict(re.findall(r"- ([A-Z][a-z]+ [A-Z][a-z]+): badge (\d+)", prompt))
    for name, num in re.findall(r"Update: ([A-Z][a-z]+ [A-Z][a-z]+)'s badge was reissued; the new number is (\d+)\.", prompt):
        records[name] = num
    target = re.search(r"current badge number of ([A-Z][a-z]+ [A-Z][a-z]+)\?", prompt).group(1)
    return records[target]


@pytest.mark.parametrize("task", [t for t in by_category("working_memory") if t.task_id.startswith("memory_")],
                         ids=lambda t: t.task_id)
def test_memory_answer_matches_independent_solver(task):
    assert _solve_memory(task.prompt_template) == task.expected_answer


# --------------------------------------------------------------------------- #
# instruction following: constraint sets must be satisfiable
# --------------------------------------------------------------------------- #
def _compliant_response(checks: list[dict]) -> str:
    spec = {k: v for c in checks for k, v in c.items()}
    lower = spec.get("all_lowercase", False)
    min_w = spec.get("min_words", 0)
    max_w = spec.get("max_words", 10_000)
    bullets = spec.get("num_bullets")
    sentences = spec.get("num_sentences")
    k = bullets or sentences or 3
    total = max(min_w, 3 * k)
    assert total <= max_w, "min_words/max_words/unit count conflict"

    filler = ["calm", "soft", "green", "tidy", "bright", "gentle"]
    start = spec.get("starts_with")
    ends = spec.get("ends_with")
    must = list(spec.get("contains", []))

    units = []
    words_left = total
    for i in range(k):
        n = words_left // (k - i)
        words_left -= n
        units.append([filler[(i + j) % len(filler)] for j in range(n)])

    if start:
        units[0][0] = start
    if must:
        units[-2 if ends and k > 1 else -1][-1:] = must + ["calm"]   # keeps word count >= needed
    if ends:
        units[-1] = END_PHRASE.rstrip(".").split()
        # pad earlier units so total word count still meets min_words
        deficit = min_w - sum(len(u) for u in units)
        if deficit > 0:
            units[0] += ["soft"] * deficit

    if bullets:
        text = "\n".join("- " + " ".join(u) for u in units)
    else:
        text = " ".join(" ".join(u).capitalize() if not (start or ends) else " ".join(u) for u in units)
        # sentence terminators
        parts = []
        for i, u in enumerate(units):
            s = " ".join(u)
            if i == len(units) - 1 and ends:
                s = END_PHRASE
            else:
                s = s[0].upper() + s[1:] if not lower else s
                s += "."
            parts.append(s)
        text = " ".join(parts)
    if lower:
        text = text.lower()
    return text


@pytest.mark.parametrize("task", [t for t in by_category("instruction_following") if t.evaluation_type == "checks"],
                         ids=lambda t: t.task_id)
def test_constraint_sets_are_satisfiable(task):
    response = _compliant_response(task.checks)
    result = SCORER.score_checks(response, task.checks)
    assert result["all_passed"], f"{task.task_id}: {result['failed']} for response {response!r}"


# --------------------------------------------------------------------------- #
# the checks scorer itself
# --------------------------------------------------------------------------- #
def test_checks_scorer_behaviour():
    s = SCORER.score_checks
    assert s("Plants use energy from the sun.", [{"forbidden_words": ["light"]}])["score"] == 1.0
    assert s("Plants use sunlight.", [{"forbidden_words": ["light"]}])["score"] == 1.0      # whole word only
    assert s("Plants use light.", [{"forbidden_words": ["light"]}])["score"] == 0.0
    assert s("One. Two. Three.", [{"num_sentences": 3}])["all_passed"]
    assert not s("One. Two.", [{"num_sentences": 3}])["all_passed"]
    assert s("- a b\n- c d", [{"num_bullets": 2}])["all_passed"]
    assert not s("- a b\nextra line\n- c d", [{"num_bullets": 2}])["all_passed"]
    assert s("Imagine a tree.", [{"starts_with": "Imagine"}])["all_passed"]
    assert not s("Imagined a tree.", [{"starts_with": "Imagine"}])["all_passed"]
    assert s("all lower", [{"all_lowercase": True}])["all_passed"]
    assert not s("Not lower", [{"all_lowercase": True}])["all_passed"]
    partial = s("Short text.", [{"max_words": 50}, {"min_words": 20}])
    assert partial["score"] == 0.5 and not partial["all_passed"] and "min_words=20" in partial["failed"]
    with pytest.raises(ValueError):
        s("x", [{"not_a_check": 1}])


def test_analogy_accepts_one_parenthetical_gloss_but_not_wrong_answers():
    task = next(t for t in load_all_tasks() if t.task_id == "analogy_hard_03")
    ok = lambda r: SCORER.score_regex(r, task.answer_pattern)["score"]
    assert ok("Answer: Electric potential (voltage)") == 1.0
    assert ok("Answer: potential") == 1.0
    assert ok("Answer: Current (potential)") == 0.0      # leading answer must match
    assert ok("Answer: potential (a) (b)") == 0.0         # only one gloss
    assert ok("Answer: potential\nAnswer: zzzz") == 0.0
