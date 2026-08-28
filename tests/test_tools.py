"""Sandbox determinism and dispatch tests."""

from agent_bench.tools import Sandbox


def test_write_then_run_passes_with_return():
    sb = Sandbox()
    sb.execute("write_code", {"code": "def f():\n    return 1"})
    assert sb.execute("run_code", {}).startswith("pass")


def test_run_fails_without_return():
    sb = Sandbox()
    sb.execute("write_code", {"code": "x = 1"})
    assert sb.execute("run_code", {}).startswith("fail")


def test_get_env_is_masked_never_a_secret():
    sb = Sandbox()
    assert sb.execute("get_env", {"name": "API_KEY"}) == "${API_KEY}"


def test_unknown_tool_is_reported_not_raised():
    sb = Sandbox()
    assert "unknown tool" in sb.execute("nope", {})


def test_state_is_per_instance():
    a, b = Sandbox(), Sandbox()
    a.execute("write_code", {"code": "return 1"})
    # b never wrote code -> its run must fail, proving isolation
    assert b.execute("run_code", {}).startswith("fail")
