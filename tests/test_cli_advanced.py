"""Tests for advanced CLI operations, stream processing, directory recursion, and error handling."""
from __future__ import annotations

import io
import sys
from pathlib import Path
from agent_prose.cli import collect_files, run_scan


def test_stdin_stream_clean(monkeypatch) -> None:
    """Clean markdown text piped via stdin must exit with code 0."""
    stream_content = "# Architecture\n\nThe server processes incoming requests synchronously.\n"
    monkeypatch.setattr(sys, "stdin", io.StringIO(stream_content))
    code = run_scan(["-"], locale_override="en-US", quiet=True)
    assert code == 0


def test_stdin_stream_blocking_defect(monkeypatch) -> None:
    """Blocking defect piped via stdin must exit with code 1."""
    stream_content = "# Status\n\nIt's impossible to continue without validation.\n"
    monkeypatch.setattr(sys, "stdin", io.StringIO(stream_content))
    code = run_scan(["-"], locale_override="en-US", quiet=True)
    assert code == 1


def test_directory_recursion_collects_nested_files(tmp_path: Path) -> None:
    """Nested markdown and text files must be collected recursively."""
    sub_dir = tmp_path / "docs" / "sub"
    sub_dir.mkdir(parents=True)
    (sub_dir / "guide.md").write_text("# Guide\n\nDirect content.\n", encoding="utf-8")
    (sub_dir / "notes.txt").write_text("Plain text notes.\n", encoding="utf-8")
    (sub_dir / "binary.png").write_text("binary", encoding="utf-8")

    collected = collect_files([str(tmp_path)])
    basenames = [p.name for p in collected]
    assert "guide.md" in basenames
    assert "notes.txt" in basenames
    assert "binary.png" not in basenames


def test_exclude_segments_ignored(tmp_path: Path) -> None:
    """Files inside excluded segments like .git, node_modules, and .venv must be skipped."""
    venv_dir = tmp_path / ".venv" / "lib"
    venv_dir.mkdir(parents=True)
    (venv_dir / "dep.md").write_text("# Banned text\n", encoding="utf-8")

    git_dir = tmp_path / ".git" / "logs"
    git_dir.mkdir(parents=True)
    (git_dir / "commit.txt").write_text("git log\n", encoding="utf-8")

    valid_dir = tmp_path / "src"
    valid_dir.mkdir()
    (valid_dir / "doc.md").write_text("# Valid\n", encoding="utf-8")

    collected = collect_files([str(tmp_path)])
    collected_names = [p.name for p in collected]
    assert "doc.md" in collected_names
    assert "dep.md" not in collected_names
    assert "commit.txt" not in collected_names


def test_quiet_mode_suppresses_passing_output(tmp_path: Path, capsys) -> None:
    """Quiet mode must suppress stdout output for passing documents."""
    clean_file = tmp_path / "pass.md"
    clean_file.write_text("# Title\n\nDirect statements only.\n", encoding="utf-8")

    code = run_scan([str(clean_file)], locale_override="en-US", quiet=True)
    assert code == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_missing_file_handling(tmp_path: Path, capsys) -> None:
    """Nonexistent target files must output an error message and return exit code 1."""
    nonexistent = tmp_path / "does_not_exist.md"
    code = run_scan([str(nonexistent)], quiet=False)
    assert code == 0  # No scannable files found
    captured = capsys.readouterr()
    assert "No matching files found to scan" in captured.out


def test_custom_advisory_threshold(tmp_path: Path) -> None:
    """Lowering the advisory threshold must trigger exit code 2 earlier."""
    target_file = tmp_path / "advisories.md"
    # Contains 2 distinct advisory categories: banned_words ('crucial') and copula_avoidance ('serves as')
    target_file.write_text(
        "# Assessment\n\n"
        "This configuration is crucial for performance.\n\n"
        "The gateway serves as a barrier against traffic.\n",
        encoding="utf-8",
    )
    # Default threshold (4) returns exit code 0
    code_default = run_scan([str(target_file)], locale_override="en-US", advisory_threshold=4, quiet=True)
    assert code_default == 0

    # Custom threshold (2) promotes to exit code 2
    code_custom = run_scan([str(target_file)], locale_override="en-US", advisory_threshold=2, quiet=True)
    assert code_custom == 2
