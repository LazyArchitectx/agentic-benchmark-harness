# Design Notes

Deeper rationale behind the choices summarized in the README — written to be defended in
a technical interview.

## Why multi-step, and why the trace is the output

The failure this harness exists to catch is *compounding*: an agent produces a valid step
1 and a valid step 2, but the state step 2 leaves behind makes step 3 wrong. A single-turn
prompt test — one input, one graded output — structurally cannot see this, because there
is no step 2 to depend on. So the harness runs a real loop and keeps the **full trace**.
The verdict (`passed`/`reason`) is the summary; the trace is the substance, because it's
what tells you *how* a task failed — which tool call, in which order, with what result.

## Why the Agent is a Protocol

The runner is the part with real behavior worth testing: the step loop, the budget cutoff,
the point where checks are applied. If the runner called an LLM directly, testing it would
need live API calls — slow, nondeterministic, costly, flaky in CI. By depending only on
the `Agent` Protocol, the runner is driven in tests by a `MockAgent` that replays a
scripted action sequence, so every scenario is exact and offline. The real `LLMAgent` is
then just an adapter; swapping providers touches one method.

This also enables the most useful demo trick: a task whose `mock_script` *deliberately
misbehaves* (hardcodes a secret). Because the agent is swappable and scripted, the harness
can be shown **catching** bad behavior deterministically — no need to coax a real model
into failing.

## Why checks are declarative

Each task's assertions live in its YAML (`used_tool`, `tool_order`,
`no_hardcoded_secret`, `final_contains`, `run_passes`). The engine interprets them; it
doesn't hardcode any one task's expectations. Consequences: a non-engineer can author a
task, the check vocabulary is small and auditable, and the engine reports **every** failure
in a run rather than stopping at the first — so one run tells you all the ways an agent
fell short.

## Why the sandbox is deterministic

If `run_code` or `read_file` returned different results across runs, a failing task would
be ambiguous: the agent, or the tool? Determinism removes that ambiguity — every verdict
is attributable to the agent's choices. Sandbox state (e.g. written code) lives on the
instance, so each run gets a fresh sandbox and tests stay isolated.

## The safety-boundary domain, concretely

The proof case mirrors a real agent failure mode: an update makes a model *faster* and, as
a side effect, *less safe* — it starts writing a literal API key into generated code
instead of referencing a masked environment variable. `safety-001` shows the correct
behavior (uses `get_env`, passes `no_hardcoded_secret`); `safety-002` shows the failure
(hardcodes `sk-live-…`, caught by the same check). Same domain, same check, opposite
outcomes — which is exactly the contrast a benchmark should make visible before release.

## Scope and honesty

This is a from-scratch demonstrator of the pattern, kept intentionally small: the goal is
to show engineering judgment — testability, separation of concerns, data-driven checks,
honest docs — not feature breadth. "What I'd build next" names the real extensions (a
trace viewer, sandboxed real code execution, regression gating), which is where a
production version would go.
