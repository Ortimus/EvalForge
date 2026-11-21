"""
Task generator — writes the tiered benchmark into tasks/generated/.

Run from the repo root:
    python -m tasks.generate

Generation is seeded, so the output is reproducible and the YAML files are
committed as the benchmark of record. Re-running with the same SEED and the
same code produces byte-identical files; change SEED or counts deliberately,
because that changes the benchmark and makes old runs incomparable.

Categories
    logical_deduction      transitive ordering; depth and distractors scale with tier
    working_memory         key-value recall; list length and in-place corrections scale
    instruction_following  verifiable constraints (programmatic checks, no judge)
    analogical_reasoning   curated analogies with a set of accepted answers

Every generated task ends with an 'Answer: <x>' line and is scored by an
anchored regex (the LAST answer line must be correct), except instruction
following, which uses programmatic constraint checks.
"""
from __future__ import annotations
import random
import re
import shutil
from pathlib import Path

import yaml

OUT_DIR = Path(__file__).parent / "generated"
SEED = 20261120
TASKS_PER_TIER = 6
EXPERT_TASKS_PER_CATEGORY = 6     # expert tier: logic, memory, instruction (no analogies)
TIERS = ("easy", "medium", "hard")

ANSWER_SUFFIX = (
    "\n\nKeep any reasoning brief. End your response with a final line of the "
    "form 'Answer: <answer>'."
)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def answer_regex(expected: str) -> str:
    """Match 'Answer: <expected>' as the FINAL thing in the response (markdown/punctuation tolerant)."""
    return rf"(?is)answer:\W*{re.escape(expected)}\W*\Z"


def answer_regex_any(options: list[str]) -> str:
    """
    Accept any listed answer, optionally followed by ONE parenthetical gloss,
    e.g. 'Answer: Electric potential (voltage)'. Verbose-but-correct models would
    otherwise score 0, measuring terseness instead of reasoning. The leading
    answer must still match, and only a single (...) group is allowed.
    """
    alts = "|".join(re.escape(o) for o in options)
    return rf"(?is)answer:\W*(?:(?:a|an|the)\s+)?(?:{alts})(?:\s*\([^)\n]*\))?\W*\Z"


def _str_presenter(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.add_representer(str, _str_presenter, Dumper=yaml.SafeDumper)


def write_task(task: dict) -> None:
    path = OUT_DIR / f"{task['task_id']}.yaml"
    path.write_text(yaml.safe_dump(task, sort_keys=False, width=1000, allow_unicode=True))


# --------------------------------------------------------------------------- #
# logical deduction
# --------------------------------------------------------------------------- #
LOGIC_NAMES = ["Alice", "Bruno", "Chen", "Dara", "Elio", "Farah",
               "Gus", "Hana", "Ivo", "Jun", "Kara", "Leo"]
ORDINALS = {2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth"}


def logic_task(rng: random.Random, tier: str, idx: int) -> dict:
    n = {"easy": 3, "medium": 6, "hard": 10}[tier]
    people = rng.sample(LOGIC_NAMES, n)          # people[0] is tallest ... people[-1] shortest

    stmts = []
    for a, b in zip(people, people[1:]):
        if tier == "easy" or rng.random() < 0.5:
            stmts.append(f"{a} is taller than {b}.")
        else:
            stmts.append(f"{b} is shorter than {a}.")

    if tier == "hard":
        # distractors on a different dimension (age), internally consistent
        age_order = rng.sample(people, n)        # age_order[0] is oldest
        for _ in range(3):
            a, b = rng.sample(people, 2)
            older, younger = sorted((a, b), key=age_order.index)
            stmts.append(f"{older} is older than {younger}.")

    rng.shuffle(stmts)

    if tier == "easy":
        question, answer = "Who is the tallest?", people[0]
    elif tier == "medium":
        if rng.random() < 0.5:
            question, answer = "Who is the tallest?", people[0]
        else:
            question, answer = "Who is the shortest?", people[-1]
    else:
        k = rng.randint(3, n - 2)                # a middle rank: needs the whole chain
        question, answer = f"Who is the {ORDINALS[k]} tallest?", people[k - 1]

    prompt = (
        f"Consider these statements about {n} people.\n\n"
        + "\n".join(stmts)
        + f"\n\nAssume only these statements are true. {question}"
        + ANSWER_SUFFIX
    )
    return {
        "task_id": f"logic_{tier}_{idx:02d}",
        "category": "logical_deduction",
        "difficulty": tier,
        "description": f"Transitive height ordering over {n} people",
        "prompt_template": prompt,
        "evaluation_type": "regex",
        "expected_answer": answer,
        "answer_pattern": answer_regex(answer),
    }


# --------------------------------------------------------------------------- #
# working memory
# --------------------------------------------------------------------------- #
FIRST = ["Ada", "Ben", "Cleo", "Dev", "Eli", "Fay", "Gil", "Hugo", "Iris", "Jon",
         "Kai", "Lena", "Milo", "Nora", "Omar", "Pia", "Quinn", "Rae", "Sam", "Tess"]
LAST = ["Abbott", "Brandt", "Castillo", "Dunn", "Ellis", "Foster", "Grant", "Hayes",
        "Ibarra", "Jensen", "Kwon", "Lund", "Mercer", "Nair", "Okafor", "Price",
        "Quist", "Rossi", "Sato", "Tran"]


def memory_task(rng: random.Random, tier: str, idx: int) -> dict:
    n = {"easy": 5, "medium": 25, "hard": 60}[tier]

    names: list[str] = []
    seen = set()
    while len(names) < n:
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        if name not in seen:
            seen.add(name)
            names.append(name)
    numbers = rng.sample(range(1000, 9999), n + 2)       # unique, with spares for corrections
    records = dict(zip(names, numbers))
    spare = numbers[n:]

    target = rng.choice(names)
    answer = records[target]
    lines = [f"- {name}: badge {num}" for name, num in records.items()]
    updates = []

    if tier == "hard":
        # a correction to a non-target record (distractor) ...
        other = rng.choice([nm for nm in names if nm != target])
        updates.append(f"Update: {other}'s badge was reissued; the new number is {spare[0]}.")
        # ... and, half the time, one that changes the answer
        if rng.random() < 0.5:
            answer = spare[1]
            updates.append(f"Update: {target}'s badge was reissued; the new number is {answer}.")
        rng.shuffle(updates)

    prompt = (
        "Here is a staff directory of badge numbers.\n\n"
        + "\n".join(lines)
        + ("\n\n" + "\n".join(updates) if updates else "")
        + f"\n\nWhat is the current badge number of {target}?"
        + ANSWER_SUFFIX
    )
    return {
        "task_id": f"memory_{tier}_{idx:02d}",
        "category": "working_memory",
        "difficulty": tier,
        "description": f"Recall one badge number from {n} records"
                       + (" with in-place updates" if updates else ""),
        "prompt_template": prompt,
        "evaluation_type": "regex",
        "expected_answer": str(answer),
        "answer_pattern": answer_regex(str(answer)),
    }


# --------------------------------------------------------------------------- #
# instruction following (programmatic checks)
# --------------------------------------------------------------------------- #
TOPICS = [
    ("a rainy day", ["rain", "wet", "water"]),
    ("learning to cook", ["food", "recipe", "kitchen"]),
    ("riding a bicycle", ["wheel", "pedal", "road"]),
    ("a quiet library", ["book", "books", "read"]),
    ("the ocean", ["sea", "wave", "water"]),
    ("a mountain hike", ["mountain", "climb", "trail"]),
]
START_WORDS = ["Imagine", "Often", "Consider"]
END_PHRASE = "That is all."

# constraints that cannot appear together
EXCLUSIVE = [
    {"num_bullets", "starts_with"},
    {"num_bullets", "num_sentences"},
    {"num_bullets", "ends_with"},
    {"all_lowercase", "starts_with"},
    {"all_lowercase", "ends_with"},
]
CONSTRAINT_KINDS = ["max_words", "min_words", "forbidden_words", "starts_with",
                    "ends_with", "num_sentences", "num_bullets", "all_lowercase", "contains"]


def _build_constraint(rng: random.Random, kind: str, forbidden_pool: list[str]) -> tuple[str, dict]:
    if kind == "max_words":
        n = rng.choice([50, 70, 90])
        return f"Use at most {n} words.", {"max_words": n}
    if kind == "min_words":
        n = rng.choice([25, 35])
        return f"Use at least {n} words.", {"min_words": n}
    if kind == "forbidden_words":
        words = rng.sample(forbidden_pool, 2)
        return f"Do not use the words '{words[0]}' or '{words[1]}'.", {"forbidden_words": words}
    if kind == "starts_with":
        w = rng.choice(START_WORDS)
        return f"Begin your response with the word '{w}'.", {"starts_with": w}
    if kind == "ends_with":
        return f"Finish with exactly this sentence: '{END_PHRASE}'", {"ends_with": END_PHRASE}
    if kind == "num_sentences":
        n = rng.choice([2, 3, 4])
        return f"Write exactly {n} sentences.", {"num_sentences": n}
    if kind == "num_bullets":
        n = rng.choice([3, 4])
        return (f"Write exactly {n} bullet points, each starting with '- ', and nothing else.",
                {"num_bullets": n})
    if kind == "all_lowercase":
        return "Write entirely in lowercase letters.", {"all_lowercase": True}
    if kind == "contains":
        return "Include the word 'because'.", {"contains": ["because"]}
    raise ValueError(kind)


def _pick_kinds(rng: random.Random, count: int) -> list[str]:
    for _ in range(200):
        pool = CONSTRAINT_KINDS[:]
        rng.shuffle(pool)
        chosen: list[str] = []
        for kind in pool:
            if len(chosen) == count:
                break
            if any({kind, c} in EXCLUSIVE for c in chosen):
                continue
            chosen.append(kind)
        if len(chosen) == count:
            return chosen
    raise RuntimeError("could not pick a compatible constraint set")


def instruction_task(rng: random.Random, tier: str, idx: int) -> dict:
    count = {"easy": 2, "medium": 4, "hard": 6}[tier]
    topic, forbidden_pool = rng.choice(TOPICS)
    kinds = _pick_kinds(rng, count)
    built = [_build_constraint(rng, k, forbidden_pool) for k in kinds]

    prompt = (
        f"Write a short piece about {topic}. Follow every requirement:\n"
        + "\n".join(f"- {text}" for text, _ in built)
    )
    return {
        "task_id": f"instr_{tier}_{idx:02d}",
        "category": "instruction_following",
        "difficulty": tier,
        "description": f"{count} simultaneous verifiable constraints",
        "prompt_template": prompt,
        "evaluation_type": "checks",
        "checks": [check for _, check in built],
    }


# --------------------------------------------------------------------------- #
# analogical reasoning (curated; ambiguous analogies deliberately excluded)
# --------------------------------------------------------------------------- #
ANALOGIES = [
    # (tier, "A : B :: C : ___", [accepted answers])
    ("easy", "Hot : Cold :: Up : ___", ["down"]),
    ("easy", "Bird : Nest :: Bee : ___", ["hive"]),
    ("easy", "Pen : Write :: Knife : ___", ["cut"]),
    ("easy", "Puppy : Dog :: Kitten : ___", ["cat"]),
    ("easy", "Eye : See :: Ear : ___", ["hear"]),
    ("easy", "Day : Night :: Summer : ___", ["winter"]),
    ("medium", "Thermometer : Temperature :: Barometer : ___", ["pressure", "air pressure", "atmospheric pressure"]),
    ("medium", "Sculptor : Statue :: Author : ___", ["book", "novel", "story"]),
    ("medium", "Chef : Kitchen :: Pilot : ___", ["cockpit", "flight deck"]),
    ("medium", "Cartographer : Map :: Lexicographer : ___", ["dictionary"]),
    ("medium", "Meter : Length :: Liter : ___", ["volume"]),
    ("medium", "Seed : Tree :: Egg : ___", ["bird", "chicken"]),
    ("hard", "Cacophony : Harmony :: Scarcity : ___", ["abundance", "plenty", "surplus"]),
    ("hard", "Benevolent : Malevolent :: Frugal : ___", ["extravagant", "lavish", "wasteful", "profligate", "spendthrift"]),
    ("hard", "Ohm : Resistance :: Volt : ___", ["potential", "voltage", "electric potential", "potential difference"]),
    ("hard", "Sonnet : Fourteen (lines) :: Haiku : ___ (lines)", ["three", "3"]),
    ("hard", "Ampere : Current :: Hertz : ___", ["frequency"]),
    ("hard", "Prologue : Epilogue :: Overture : ___", ["finale", "coda"]),
]


def analogy_tasks() -> list[dict]:
    counters = {t: 0 for t in TIERS}
    tasks = []
    for tier, text, accepted in ANALOGIES:
        counters[tier] += 1
        tasks.append({
            "task_id": f"analogy_{tier}_{counters[tier]:02d}",
            "category": "analogical_reasoning",
            "difficulty": tier,
            "description": "Complete the analogy",
            "prompt_template": f"Complete the analogy with a single word or short phrase.\n\n{text}"
                               + ANSWER_SUFFIX,
            "evaluation_type": "regex",
            "expected_answer": accepted[0],
            "answer_pattern": answer_regex_any(accepted),
        })
    return tasks


# --------------------------------------------------------------------------- #
# EXPERT tier
# Generated from a SEPARATE random stream (SEED + 1) so the easy/medium/hard tasks
# above stay byte-identical when this tier changes. Every answer is unique and
# machine-checkable; difficulty comes from interference and dependency, not length:
#   logic        partial orders: count what is PROVABLY shorter (transitive closure)
#   memory       ordered updates (reissue / swap / copy) that chain through state
#   instruction  7 interacting constraints incl. a narrow word-count window
# --------------------------------------------------------------------------- #
def _closure_counts(n: int, edges: set[tuple[int, int]]) -> list[int]:
    """edges (i, j): i is taller than j. Returns, per i, how many are provably shorter."""
    below = [set() for _ in range(n)]
    changed = True
    while changed:
        changed = False
        for i, j in edges:
            new = {j} | below[j]
            if not new <= below[i]:
                below[i] |= new
                changed = True
    return [len(b) for b in below]


def logic_expert_task(rng: random.Random, idx: int) -> dict:
    n = 12
    people = rng.sample(LOGIC_NAMES, n)            # hidden truth: people[0] tallest
    while True:
        edges: set[tuple[int, int]] = set()
        while len(edges) < 14:                     # fewer edges than a full chain needs plus extras
            i = rng.randrange(n - 1)
            edges.add((i, min(n - 1, i + rng.randint(1, 4))))
        counts = _closure_counts(n, edges)
        # a target whose answer differs from its true rank, so rank-guessing fails
        cands = [i for i in range(n) if 3 <= counts[i] <= 7 and counts[i] != n - 1 - i]
        if cands:
            break
    target = people[rng.choice(cands)]
    answer = counts[people.index(target)]

    stmts = []
    for i, j in sorted(edges):
        a, b = people[i], people[j]
        stmts.append(f"{a} is taller than {b}." if rng.random() < 0.5 else f"{b} is shorter than {a}.")
    age_order = rng.sample(people, n)
    for _ in range(5):                             # distractors on another dimension
        a, b = rng.sample(people, 2)
        older, younger = sorted((a, b), key=age_order.index)
        stmts.append(f"{older} is older than {younger}.")
    rng.shuffle(stmts)

    prompt = (
        f"Consider these statements about {n} people.\n\n" + "\n".join(stmts)
        + f"\n\nAssume only these statements are true. Counting only what is logically "
          f"guaranteed, how many people are shorter than {target}? Answer with a number only."
        + ANSWER_SUFFIX
    )
    return {
        "task_id": f"logic_expert_{idx:02d}", "category": "logical_deduction", "difficulty": "expert",
        "description": f"Count provably-shorter people in a partial order of {n}",
        "prompt_template": prompt, "evaluation_type": "regex",
        "expected_answer": str(answer), "answer_pattern": answer_regex(str(answer)),
    }


def memory_expert_task(rng: random.Random, idx: int) -> dict:
    n, n_ops = 40, 9
    while True:
        names: list[str] = []
        while len(names) < n:
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            if name not in names:
                names.append(name)
        numbers = rng.sample(range(1000, 9999), n + n_ops)
        records = dict(zip(names, numbers))
        spare = iter(numbers[n:])
        target = rng.choice(names)
        hot = [target] + rng.sample([x for x in names if x != target], 5)

        state, ops, touches = dict(records), [], 0
        for _ in range(n_ops):
            pool = hot if rng.random() < 0.75 else names
            a, b = rng.sample(pool, 2)
            kind = rng.choice(["reissue", "swap", "copy"])
            if kind == "reissue":
                num = next(spare)
                state[a] = num
                ops.append(f"Update: {a}'s badge was reissued; the new number is {num}.")
                b = None
            elif kind == "swap":
                state[a], state[b] = state[b], state[a]
                ops.append(f"Swap: {a} and {b} exchanged badge numbers.")
            else:
                state[b] = state[a]
                ops.append(f"Copy: {b} now carries the same badge number that {a} has at this moment.")
            touches += target in (a, b)
        # the target must be in the middle of the action and end up changed
        if touches >= 3 and state[target] != records[target]:
            break

    prompt = (
        "Here is a staff directory of badge numbers.\n\n"
        + "\n".join(f"- {nm}: badge {num}" for nm, num in records.items())
        + "\n\nThe following changes happened in this order:\n" + "\n".join(ops)
        + f"\n\nApply every change in order. What is {target}'s badge number after all changes?"
        + ANSWER_SUFFIX
    )
    return {
        "task_id": f"memory_expert_{idx:02d}", "category": "working_memory", "difficulty": "expert",
        "description": f"Track {n} records through {n_ops} chained updates",
        "prompt_template": prompt, "evaluation_type": "regex",
        "expected_answer": str(state[target]), "answer_pattern": answer_regex(str(state[target])),
    }


def instruction_expert_task(rng: random.Random, idx: int) -> dict:
    topic, pool = rng.choice(TOPICS)
    min_w = rng.choice([40, 45, 50])
    max_w = min_w + 10                              # narrow window: needs real word counting
    n_sent = rng.choice([3, 4])
    start = rng.choice(START_WORDS)
    built = [
        (f"Use at least {min_w} words.", {"min_words": min_w}),
        (f"Use at most {max_w} words.", {"max_words": max_w}),
        (f"Write exactly {n_sent} sentences.", {"num_sentences": n_sent}),
        (f"Begin your response with the word '{start}'.", {"starts_with": start}),
        (f"Finish with exactly this sentence: '{END_PHRASE}'", {"ends_with": END_PHRASE}),
        (f"Do not use the words '{pool[0]}', '{pool[1]}' or '{pool[2]}'.", {"forbidden_words": list(pool)}),
        ("Include the word 'because'.", {"contains": ["because"]}),
    ]
    rng.shuffle(built)
    prompt = (f"Write a short piece about {topic}. Follow every requirement:\n"
              + "\n".join(f"- {text}" for text, _ in built))
    return {
        "task_id": f"instr_expert_{idx:02d}", "category": "instruction_following", "difficulty": "expert",
        "description": "7 interacting constraints with a 10-word window",
        "prompt_template": prompt, "evaluation_type": "checks", "checks": [c for _, c in built],
    }


# --------------------------------------------------------------------------- #
def main() -> None:
    rng = random.Random(SEED)
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)       # generated/ is owned by this script; regenerate cleanly
    OUT_DIR.mkdir(parents=True)

    tasks: list[dict] = []
    for tier in TIERS:
        for i in range(1, TASKS_PER_TIER + 1):
            tasks.append(logic_task(rng, tier, i))
            tasks.append(memory_task(rng, tier, i))
            tasks.append(instruction_task(rng, tier, i))
    tasks.extend(analogy_tasks())

    rng_x = random.Random(SEED + 1)         # separate stream: see EXPERT tier note
    for i in range(1, EXPERT_TASKS_PER_CATEGORY + 1):
        tasks.append(logic_expert_task(rng_x, i))
        tasks.append(memory_expert_task(rng_x, i))
        tasks.append(instruction_expert_task(rng_x, i))

    for task in tasks:
        write_task(task)

    by_cat: dict[str, int] = {}
    for t in tasks:
        by_cat[t["category"]] = by_cat.get(t["category"], 0) + 1
    print(f"Wrote {len(tasks)} tasks to {OUT_DIR}")
    for cat, n in sorted(by_cat.items()):
        print(f"  {cat}: {n}")


if __name__ == "__main__":
    main()
