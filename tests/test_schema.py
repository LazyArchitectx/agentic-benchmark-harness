"""Schema validation tests."""

import pytest
from pydantic import ValidationError

from agent_bench.schema import Action, Task


def test_task_loads_minimal():
    task = Task(id="t", domain="tool_use", prompt="do it")
    assert task.max_steps == 10
    assert task.available_tools == []


def test_action_tool_and_finish():
    tool = Action(kind="tool", tool="read_file", args={"path": "x"})
    finish = Action(kind="finish", output="done")
    assert tool.tool == "read_file"
    assert finish.output == "done"


def test_action_kind_is_constrained():
    with pytest.raises(ValidationError):
        Action(kind="jump")  # not tool|finish
