"""Multi-step agentic benchmark harness.

Runs an agent (an LLM, or a deterministic mock) through multi-step, tool-using
tasks across four domains — tool use, code generation, constraint adherence, and
safety-boundary testing — and applies declarative checks to each run to surface
failure modes that single-turn prompt tests would miss.
"""

from agent_bench.runner import run_task
from agent_bench.schema import Action, Task, TaskResult
from agent_bench.tasks import load_tasks

__all__ = ["Action", "Task", "TaskResult", "load_tasks", "run_task"]
__version__ = "1.0.0"
