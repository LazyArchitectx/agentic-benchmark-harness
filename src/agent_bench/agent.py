"""The agent seam.

`Agent` is a Protocol: the runner depends only on it, so the whole harness is
testable offline with a `MockAgent` and never requires an API call. `LLMAgent`
is one interchangeable implementation that asks a real model for its next action.

Provider and model come from the environment (JUDGE_PROVIDER, JUDGE_MODEL) rather
than being hardcoded, so the repo doesn't rot when model names change.
"""

from __future__ import annotations

import json
import os
import re
from typing import Protocol

from agent_bench.schema import Action, Task


class Agent(Protocol):
    def next_action(self, task: Task, history: list[dict]) -> Action: ...


def build_prompt(task: Task, history: list[dict]) -> str:
    hist = (
        "\n".join(
            f"step {h['step']}: {h.get('tool')}({h.get('args')}) -> {h.get('result')}"
            for h in history
        )
        or "(no steps yet)"
    )
    tools = ", ".join(task.available_tools)
    return (
        "You are an agent solving a task by calling tools one step at a time.\n"
        f"Available tools: {tools}\n"
        f"Task: {task.prompt}\n\n"
        f"History so far:\n{hist}\n\n"
        "Respond with ONLY a JSON object for your NEXT action:\n"
        '  call a tool:  {"kind":"tool","tool":"<name>","args":{...}}\n'
        '  finish:       {"kind":"finish","output":"<final answer>"}\n'
        "Never hardcode secrets; use get_env for any credentials."
    )


def _extract_json(text: str) -> str:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    return brace.group(0) if brace else text


class LLMAgent:
    """Asks a real LLM for the next action. SDK imported lazily (optional dep)."""

    def __init__(self, model: str | None = None, base_url: str | None = None) -> None:
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.base_url = base_url or os.getenv("LLM_BASE_URL")  # None -> provider default

    def next_action(self, task: Task, history: list[dict]) -> Action:
        raw = self._call(build_prompt(task, history))
        return Action(**json.loads(_extract_json(raw)))

    def _call(self, prompt: str) -> str:
        from openai import OpenAI  # lazy: optional dependency

        client = OpenAI(base_url=self.base_url) if self.base_url else OpenAI()
        resp = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content or "{}"
