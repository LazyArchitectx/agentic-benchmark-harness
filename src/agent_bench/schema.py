"""Validated data models for the harness.

A `Task` is a multi-step benchmark spec loaded from YAML. An `Action` is one move
an agent makes (call a tool, or finish). A `StepRecord` is one line of the trace.
A `TaskResult` is the verdict plus the full trace — the trace is the real output,
because it's what tells you *how* a task failed, not just that it did.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CheckSpec(BaseModel):
    """One declarative assertion applied to a completed run.

    kind is one of: used_tool | tool_order | no_hardcoded_secret |
    final_contains | run_passes. `value` carries the argument where relevant.
    """

    kind: str
    value: Any = None


class Task(BaseModel):
    id: str
    domain: str
    prompt: str
    available_tools: list[str] = Field(default_factory=list)
    max_steps: int = 10
    checks: list[CheckSpec] = Field(default_factory=list)
    # Scripted actions the MockAgent replays (offline demo + tests). Ignored by LLMAgent.
    mock_script: list[dict[str, Any]] = Field(default_factory=list)


class Action(BaseModel):
    kind: Literal["tool", "finish"]
    tool: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)
    output: str | None = None


class StepRecord(BaseModel):
    step: int
    kind: str
    tool: str | None = None
    args: dict[str, Any] = Field(default_factory=dict)
    result: str | None = None
    output: str | None = None


class TaskResult(BaseModel):
    task_id: str
    domain: str
    passed: bool
    steps: int
    reason: str
    final_output: str | None = None
    trace: list[StepRecord] = Field(default_factory=list)
