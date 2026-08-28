"""The core loop: drive an agent through a task, record the trace, apply checks.

    step until finish or max_steps:
        ask the agent for the next action
        if finish -> stop
        else execute the tool in the sandbox, record the step, feed it back

    then evaluate the task's declarative checks against the full trace.

Depends only on the `Agent` Protocol, so it runs identically with a mock or a
real LLM.
"""

from __future__ import annotations

from agent_bench.agent import Agent
from agent_bench.assertions import evaluate_checks
from agent_bench.schema import StepRecord, Task, TaskResult
from agent_bench.tools import Sandbox


def run_task(
    task: Task, agent: Agent, sandbox: Sandbox | None = None, max_steps: int | None = None
) -> TaskResult:
    sandbox = sandbox or Sandbox()
    budget = max_steps or task.max_steps
    trace: list[StepRecord] = []
    history: list[dict] = []
    final_output: str | None = None
    finished = False

    for step in range(budget):
        action = agent.next_action(task, history)

        if action.kind == "finish":
            final_output = action.output or ""
            trace.append(StepRecord(step=step, kind="finish", output=final_output))
            finished = True
            break

        result = sandbox.execute(action.tool or "", action.args)
        record = StepRecord(
            step=step, kind="tool", tool=action.tool, args=action.args, result=result
        )
        trace.append(record)
        history.append(
            {"step": step, "tool": action.tool, "args": action.args, "result": result}
        )

    if not finished:
        return TaskResult(
            task_id=task.id,
            domain=task.domain,
            passed=False,
            steps=len(trace),
            reason="max_steps_exceeded",
            trace=trace,
        )

    failures = evaluate_checks(task.checks, trace, final_output)
    return TaskResult(
        task_id=task.id,
        domain=task.domain,
        passed=not failures,
        steps=len(trace),
        reason="passed" if not failures else "; ".join(failures),
        final_output=final_output,
        trace=trace,
    )
