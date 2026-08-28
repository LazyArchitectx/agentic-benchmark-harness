"""CLI runs the real task suite offline, and the suite behaves as designed."""

import json

from agent_bench.cli import main


def _records(capsys):
    out = capsys.readouterr().out.strip().splitlines()
    return [json.loads(line) for line in out]


def test_cli_runs_full_suite_offline(capsys):
    rc = main(["run", "--mock"])
    assert rc == 0
    records = _records(capsys)
    summary = records[-1]["summary"]
    # 5 tasks total; safety-002 is designed to FAIL (secret caught), so 4 pass.
    assert summary["total"] == 5
    assert summary["passed"] == 4


def test_cli_safety_domain_shows_the_catch(capsys):
    rc = main(["run", "--mock", "--domain", "safety_boundary"])
    assert rc == 0
    records = _records(capsys)
    by_id = {r["task"]: r for r in records if "task" in r}
    assert by_id["safety-001"]["passed"] is True          # masked var -> clean
    assert by_id["safety-002"]["passed"] is False          # hardcoded secret -> caught
    assert "secret" in by_id["safety-002"]["reason"]


def test_cli_unknown_tasks_dir_errors(capsys):
    rc = main(["run", "--mock", "--tasks", "does-not-exist"])
    assert rc == 2
