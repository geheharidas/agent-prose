"""Tests for CLI arguments, exit code promotion, and JSON reporting in agent-prose."""
from __future__ import annotations

import json
from pathlib import Path
from agent_prose.cli import run_scan


def test_clean_file_exits_zero(tmp_path: Path) -> None:
    """A clean markdown file must exit with code 0."""
    clean_file = tmp_path / "clean.md"
    clean_file.write_text(
        "# Architecture Overview\n\n"
        "The system processes incoming queue messages synchronously.\n\n"
        "Each message undergoes schema validation before persistence.\n",
        encoding="utf-8",
    )
    code = run_scan([str(clean_file)], locale_override="en-US", quiet=True)
    assert code == 0


def test_blocking_violation_exits_one(tmp_path: Path) -> None:
    """A blocking violation (such as contractions or non-ASCII characters) must exit with code 1."""
    violating_file = tmp_path / "blocking.md"
    violating_file.write_text(
        "# Status\n\n"
        "It's essential that we verify all database queries.\n",
        encoding="utf-8",
    )
    code = run_scan([str(violating_file)], locale_override="en-US", quiet=True)
    assert code == 1


def test_single_advisory_below_threshold_exits_zero(tmp_path: Path) -> None:
    """A single advisory warning must not trigger process failure in default mode."""
    advisory_file = tmp_path / "single_advisory.md"
    # 'crucial' is an advisory warning
    advisory_file.write_text(
        "# Design Decision\n\n"
        "This configuration setting is crucial for queue performance.\n",
        encoding="utf-8",
    )
    code = run_scan([str(advisory_file)], locale_override="en-US", quiet=True)
    assert code == 0


def test_four_advisories_promotes_to_exit_two(tmp_path: Path) -> None:
    """Accumulating 4 advisory warnings must promote the scan failure to exit code 2."""
    multi_advisory_file = tmp_path / "four_advisories.md"
    multi_advisory_file.write_text(
        "# Assessment\n\n"
        "This setting is crucial for throughput.\n\n"
        "The server serves as a relay.\n\n"
        "I hope this email finds you well.\n\n"
        "The worker flushed the queue, confirming that records were processed.\n",
        encoding="utf-8",
    )
    code = run_scan([str(multi_advisory_file)], locale_override="en-US", quiet=True)
    assert code == 2


def test_strict_mode_promotes_single_advisory_to_exit_one(tmp_path: Path) -> None:
    """Strict mode must promote any advisory warning to exit code 1."""
    advisory_file = tmp_path / "strict_advisory.md"
    advisory_file.write_text(
        "# Design Decision\n\n"
        "This configuration setting is crucial for queue performance.\n",
        encoding="utf-8",
    )
    code = run_scan([str(advisory_file)], locale_override="en-US", strict=True, quiet=True)
    assert code == 1


def test_json_mode_output(tmp_path: Path, capsys) -> None:
    """JSON mode must emit structured machine-readable payload."""
    test_file = tmp_path / "report.md"
    test_file.write_text(
        "# Security Audit\n\n"
        "The server serves as a relay.\n",
        encoding="utf-8",
    )
    run_scan([str(test_file)], locale_override="en-US", json_mode=True)
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert "version" in payload
    assert "results" in payload
    assert len(payload["results"]) == 1
    assert payload["results"][0]["file"] == str(test_file)
    assert payload["results"][0]["locale"] == "en-US"
