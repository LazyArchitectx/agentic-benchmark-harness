"""Load benchmark tasks from a directory tree of YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml

from agent_bench.schema import Task


def load_tasks(tasks_dir: str | Path, domain: str | None = None) -> list[Task]:
    """Load every *.yaml under tasks_dir (recursively), optionally filtered by domain."""
    root = Path(tasks_dir)
    tasks: list[Task] = []
    for path in sorted(root.rglob("*.yaml")):
        task = Task.model_validate(yaml.safe_load(path.read_text()))
        if domain is None or task.domain == domain:
            tasks.append(task)
    return tasks
