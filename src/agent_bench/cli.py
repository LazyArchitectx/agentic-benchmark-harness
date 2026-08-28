"""Command-line interface.

Examples
--------
Offline (no API key — deterministic mock agent):
    agent-bench run --mock
    agent-bench run --mock --domain safety_boundary

Real LLM agent (needs an API key set):
    export OPENAI_API_KEY=...
    agent-bench run
"""

from __future__ import annotations

import argparse
import json
import sys

from agent_bench.agent import LLMAgent
from agent_bench.mock_agent import MockAgent
from agent_bench.runner import run_task
from agent_bench.tasks import load_tasks


def _run(args: argparse.Namespace) -> int:
    tasks = load_tasks(args.tasks, domain=args.domain)
    if not tasks:
        print(f"no tasks found under {args.tasks!r}", file=sys.stderr)
        return 2

    passed = 0
    for task in tasks:
        agent = (
            MockAgent(task.mock_script)
            if args.mock
            else LLMAgent(model=args.model, base_url=args.base_url)
        )
        result = run_task(task, agent)
        passed += int(result.passed)
        print(
            json.dumps(
                {
                    "task": result.task_id,
                    "domain": result.domain,
                    "passed": result.passed,
                    "steps": result.steps,
                    "reason": result.reason,
                }
            )
        )

    print(json.dumps({"summary": {"passed": passed, "total": len(tasks)}}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent-bench", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run the benchmark suite")
    run.add_argument("--tasks", default="tasks", help="tasks directory")
    run.add_argument("--domain", default=None, help="filter to one domain")
    run.add_argument("--mock", action="store_true", help="use the offline mock agent")
    run.add_argument("--model", default=None, help="model name (else LLM_MODEL)")
    run.add_argument("--base-url", default=None, help="OpenAI-compatible endpoint (else LLM_BASE_URL)")
    run.set_defaults(func=_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
