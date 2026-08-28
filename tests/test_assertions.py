"""Assertion engine tests — each check kind, in isolation."""

from agent_bench.assertions import evaluate_checks
from agent_bench.schema import CheckSpec, StepRecord


def _trace(*tools):
    return [StepRecord(step=i, kind="tool", tool=t, args={}) for i, t in enumerate(tools)]


def test_used_tool_passes_and_fails():
    trace = _trace("read_file", "write_code")
    assert evaluate_checks([CheckSpec(kind="used_tool", value="write_code")], trace, "") == []
    fails = evaluate_checks([CheckSpec(kind="used_tool", value="run_code")], trace, "")
    assert fails and "run_code" in fails[0]


def test_tool_order_subsequence():
    trace = _trace("read_file", "write_code", "run_code")
    assert evaluate_checks(
        [CheckSpec(kind="tool_order", value=["read_file", "run_code"])], trace, ""
    ) == []
    fails = evaluate_checks(
        [CheckSpec(kind="tool_order", value=["run_code", "read_file"])], trace, ""
    )
    assert fails  # wrong order


def test_no_hardcoded_secret_catches_leak():
    trace = [StepRecord(step=0, kind="tool", tool="write_code",
                        args={"code": "api_key = 'sk-live-xyz123'"})]
    fails = evaluate_checks([CheckSpec(kind="no_hardcoded_secret")], trace, "")
    assert fails and "secret" in fails[0]


def test_no_hardcoded_secret_passes_on_masked_var():
    trace = [StepRecord(step=0, kind="tool", tool="write_code",
                        args={"code": "headers = {'Authorization': env['API_KEY']}"})]
    assert evaluate_checks([CheckSpec(kind="no_hardcoded_secret")], trace, "") == []


def test_final_contains():
    assert evaluate_checks([CheckSpec(kind="final_contains", value="add")], [], "def add()") == []
    assert evaluate_checks([CheckSpec(kind="final_contains", value="add")], [], "nope")


def test_run_passes_reads_last_run_result():
    trace = [StepRecord(step=0, kind="tool", tool="run_code", result="pass")]
    assert evaluate_checks([CheckSpec(kind="run_passes")], trace, "") == []
    trace2 = [StepRecord(step=0, kind="tool", tool="run_code", result="fail: no return")]
    assert evaluate_checks([CheckSpec(kind="run_passes")], trace2, "")
