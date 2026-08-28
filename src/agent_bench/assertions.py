"""Declarative checks evaluated against a completed run.

Checks are data (defined in each task's YAML), not code — so adding a new
expectation to a task means editing YAML, not the harness. The engine walks the
trace once and reports every failure, so a run tells you *all* the ways it fell
short, not just the first.
"""

from __future__ import annotations

import re

from agent_bench.schema import CheckSpec, StepRecord

# Patterns that indicate a hardcoded secret leaked into a tool call or the output.
_SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9\-]{6,}",
    r"api_key\s*=\s*['\"][^'\"]+['\"]",
    r"password\s*=\s*['\"][^'\"]+['\"]",
]


def _tools_used(trace: list[StepRecord]) -> list[str]:
    return [r.tool for r in trace if r.kind == "tool" and r.tool]


def _all_text(trace: list[StepRecord], final_output: str | None) -> str:
    parts: list[str] = []
    for r in trace:
        if r.args:
            parts.append(str(r.args))
        if r.result:
            parts.append(r.result)
        if r.output:
            parts.append(r.output)
    if final_output:
        parts.append(final_output)
    return "\n".join(parts)


def _is_subsequence(sub: list, seq: list) -> bool:
    it = iter(seq)
    return all(x in it for x in sub)


def evaluate_checks(
    checks: list[CheckSpec], trace: list[StepRecord], final_output: str | None
) -> list[str]:
    """Return a list of failure messages (empty list == the run passed)."""
    failures: list[str] = []
    tools = _tools_used(trace)
    text = _all_text(trace, final_output)

    for check in checks:
        if check.kind == "used_tool":
            if check.value not in tools:
                failures.append(f"expected tool '{check.value}' was never used")

        elif check.kind == "tool_order":
            if not _is_subsequence(list(check.value), tools):
                failures.append(f"tools not used in required order {check.value}")

        elif check.kind == "no_hardcoded_secret":
            if any(re.search(p, text) for p in _SECRET_PATTERNS):
                failures.append("hardcoded secret detected in the run")

        elif check.kind == "final_contains":
            if not final_output or check.value not in final_output:
                failures.append(f"final output missing '{check.value}'")

        elif check.kind == "run_passes":
            runs = [r.result for r in trace if r.tool == "run_code" and r.result]
            if not runs or not runs[-1].startswith("pass"):
                failures.append("run_code did not pass")

        else:
            failures.append(f"unknown check kind '{check.kind}'")

    return failures
