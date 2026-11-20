"""
TaskLoader — reads YAML task files from the tasks/ directory (including the
tasks/generated/ subfolder) and returns typed TaskConfig dataclasses.
The eval loop never touches raw dicts.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import yaml


TASKS_DIR = Path(__file__).parent
DIFFICULTIES = ("easy", "medium", "hard", "expert")


@dataclass
class TaskConfig:
    task_id: str
    category: str
    difficulty: str               # easy | medium | hard | expert
    prompt_template: str
    evaluation_type: str          # exact_match | regex | checks | llm_judge
    description: str = ""
    expected_answer: str = ""     # for exact_match
    answer_pattern: str = ""      # for regex
    judge_rubric: str = ""        # for llm_judge
    checks: list[dict] = field(default_factory=list)   # for checks


def _task_paths() -> list[Path]:
    return sorted(TASKS_DIR.rglob("*.yaml"))


def load_all_tasks() -> list[TaskConfig]:
    """Load every YAML task file under tasks/ (recursively)."""
    return [_parse(p) for p in _task_paths()]


def load_task(task_id: str) -> TaskConfig:
    """Load a single task by its task_id."""
    for path in _task_paths():
        raw = yaml.safe_load(path.read_text())
        if raw.get("task_id") == task_id:
            return _parse(path)
    raise FileNotFoundError(f"No task found with task_id='{task_id}'")


def load_task_set(task_set: str) -> list[TaskConfig]:
    """
    Select tasks by task_set string:
      'default'                  every task
      'difficulty:<tier>'        all categories at one tier, e.g. 'difficulty:hard'
      '<category>'               one category, e.g. 'working_memory'
      '<category>:<tier>'        one category at one tier, e.g. 'working_memory:hard'
    """
    tasks = load_all_tasks()
    if task_set == "default":
        return tasks

    head, _, tail = task_set.partition(":")
    if head == "difficulty":
        return [t for t in tasks if t.difficulty == tail]
    if tail:
        return [t for t in tasks if t.category == head and t.difficulty == tail]
    return [t for t in tasks if t.category == head]


def _parse(path: Path) -> TaskConfig:
    raw = yaml.safe_load(path.read_text())
    return TaskConfig(
        task_id=raw["task_id"],
        category=raw["category"],
        difficulty=raw.get("difficulty", "medium"),
        prompt_template=raw["prompt_template"],
        evaluation_type=raw["evaluation_type"],
        description=raw.get("description", ""),
        expected_answer=raw.get("expected_answer", ""),
        answer_pattern=raw.get("answer_pattern", ""),
        judge_rubric=raw.get("judge_rubric", ""),
        checks=raw.get("checks", []),
    )
