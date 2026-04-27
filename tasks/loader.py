"""
TaskLoader — reads YAML task files from the tasks/ directory and returns
typed TaskConfig dataclasses. The eval loop never touches raw dicts.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import yaml


TASKS_DIR = Path(__file__).parent.parent / "tasks"


@dataclass
class TaskConfig:
    task_id: str
    category: str
    difficulty: str
    prompt_template: str
    evaluation_type: str          # exact_match | regex | llm_judge
    description: str = ""
    expected_answer: str = ""     # for exact_match
    answer_pattern: str = ""      # for regex
    judge_rubric: str = ""        # for llm_judge


def load_all_tasks() -> list[TaskConfig]:
    """Load every YAML file in the tasks/ directory."""
    tasks = []
    for path in sorted(TASKS_DIR.glob("*.yaml")):
        tasks.append(_parse(path))
    return tasks


def load_task(task_id: str) -> TaskConfig:
    """Load a single task by its task_id."""
    for path in TASKS_DIR.glob("*.yaml"):
        raw = yaml.safe_load(path.read_text())
        if raw.get("task_id") == task_id:
            return _parse(path)
    raise FileNotFoundError(f"No task found with task_id='{task_id}'")


def load_task_set(task_set: str) -> list[TaskConfig]:
    """
    Load tasks by task_set name.
    'default' returns all tasks.
    Any other name filters by category matching the task_set string.
    """
    all_tasks = load_all_tasks()
    if task_set == "default":
        return all_tasks
    return [t for t in all_tasks if t.category == task_set]


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
    )
