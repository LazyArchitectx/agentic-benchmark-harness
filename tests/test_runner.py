"""Runner tests: multi-step execution, the safety catch, and the step budget.

These prove the harness behavior — constructed deterministically with MockAgent,
so they run offline with no API key.
"""

from agent_bench.mock_agent import MockAgent
from agent_bench.runner import run_task
from agent_bench.schema import Task


def _run(task: Task):
    return run_task(task, MockAgent(task.mock_script))


def test_good_multistep_run_passes():
    task = Task(
        id="t", domain="tool_use", prompt="x",
        available_tools=["read_file", "write_code", "run_code"], max_steps=6,
        checks=[{"kind": "tool_order", "value": ["read_file", "write_code"]},
                {"kind": "used_tool", "value": "run_code"}],
        mock_script=[
            {"kind": "tool", "tool": "read_file", "args": {}},
            {"kind": "tool", "tool": "write_code", "args": {"code": "def f():\n    return 1"}},
            {"kind": "tool", "tool": "run_code", "args": {}},
            {"kind": "finish", "output": "done"},
        ],
    )
    result = _run(task)
    assert result.passed is True
    assert result.steps == 4


def test_hardcoded_secret_is_caught():
    """The money shot: a misbehaving agent hardcodes a secret; the harness catches it."""
    task = Task(
        id="s", domain="safety_boundary", prompt="x",
        available_tools=["write_code"], max_steps=5,
        checks=[{"kind": "no_hardcoded_secret"}],
        mock_script=[
            {"kind": "tool", "tool": "write_code", "args": {"code": "api_key = 'sk-live-abc123'"}},
            {"kind": "finish", "output": "api_key = 'sk-live-abc123'"},
        ],
    )
    result = _run(task)
    assert result.passed is False
    assert "secret" in result.reason


def test_max_steps_exceeded_when_agent_never_finishes():
    task = Task(
        id="m", domain="tool_use", prompt="x",
        available_tools=["read_file"], max_steps=2, checks=[],
        mock_script=[
            {"kind": "tool", "tool": "read_file", "args": {}},
            {"kind": "tool", "tool": "read_file", "args": {}},
            {"kind": "tool", "tool": "read_file", "args": {}},  # never finishes
        ],
    )
    result = _run(task)
    assert result.passed is False
    assert result.reason == "max_steps_exceeded"


def test_missing_required_tool_fails():
    task = Task(
        id="u", domain="tool_use", prompt="x",
        available_tools=["read_file", "run_code"], max_steps=4,
        checks=[{"kind": "used_tool", "value": "run_code"}],
        mock_script=[
            {"kind": "tool", "tool": "read_file", "args": {}},
            {"kind": "finish", "output": "done"},
        ],
    )
    result = _run(task)
    assert result.passed is False
    assert "run_code" in result.reason
