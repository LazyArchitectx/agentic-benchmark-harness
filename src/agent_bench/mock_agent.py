"""A deterministic agent for tests and the offline demo — no API key needed.

It replays the `mock_script` defined on each task. This lets the harness run
end-to-end (and every check fire) with fully predictable behavior, including a
task whose script deliberately misbehaves so the safety checks can be shown
catching it.
"""

from __future__ import annotations

from agent_bench.schema import Action, Task


class MockAgent:
    def __init__(self, script: list[dict]) -> None:
        self._script = list(script)
        self._i = 0

    def next_action(self, task: Task, history: list[dict]) -> Action:
        if self._i >= len(self._script):
            return Action(kind="finish", output="(script exhausted)")
        action = Action(**self._script[self._i])
        self._i += 1
        return action
