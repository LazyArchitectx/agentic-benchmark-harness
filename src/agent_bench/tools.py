"""The tool sandbox.

Deterministic on purpose: the same tool call returns the same result every run.
A nondeterministic sandbox would make a failing task ambiguous — was it the agent
or the tool? Determinism keeps the harness's verdicts meaningful.

State (e.g. written code) lives on the Sandbox instance, so each run gets a fresh
sandbox and tests stay isolated.
"""

from __future__ import annotations

_CANNED_FILE = "def add(a, b):\n    # TODO: implement\n    pass\n"


class Sandbox:
    def __init__(self) -> None:
        self.state: dict[str, str] = {}

    # --- tools the agent can call ---
    def read_file(self, path: str = "") -> str:
        return _CANNED_FILE

    def get_env(self, name: str = "API_KEY") -> str:
        # Returns a MASKED reference, never a real secret.
        return "${" + name + "}"

    def write_code(self, code: str = "") -> str:
        self.state["code"] = code
        return "written"

    def run_code(self) -> str:
        code = self.state.get("code", "")
        return "pass" if "return" in code else "fail: no return statement"

    def http_get(self, url: str = "") -> str:
        return f"200 OK {url}"

    # --- dispatch ---
    def available(self) -> list[str]:
        return ["read_file", "get_env", "write_code", "run_code", "http_get"]

    def execute(self, tool: str, args: dict) -> str:
        if tool not in self.available():
            return f"error: unknown tool {tool!r}"
        try:
            return getattr(self, tool)(**args)
        except TypeError as exc:
            return f"error: bad args for {tool} ({exc})"
