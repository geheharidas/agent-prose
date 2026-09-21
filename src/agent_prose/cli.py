"""
Command-line interface for agent-prose.
Created and maintained by Nitivra.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Sequence

from agent_prose import __version__
from agent_prose.engine import Finding, ProseEngine, ScanResult
from agent_prose.profiles import resolve_locale

SCANNABLE_EXTENSIONS = {".md", ".txt", ".html"}
DEFAULT_EXCLUDES = {
    ".git", "node_modules", ".venv", "venv", "__pycache__",
    "site-packages", "dist", "build", ".pytest_cache", "fixtures",
}


def should_scan_file(filepath: Path) -> bool:
    """Determine whether a file should be scanned based on extension and path."""
    if filepath.suffix.lower() not in SCANNABLE_EXTENSIONS:
        return False
    for part in filepath.parts:
        if part in DEFAULT_EXCLUDES:
            return False
    return True


def collect_files(targets: Sequence[str]) -> List[Path]:
    """Resolve file and directory targets into a unique list of paths."""
    collected: List[Path] = []
    for target in targets:
        p = Path(target).resolve()
        if p.is_file():
            collected.append(p)
        elif p.is_dir():
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDES]
                for file in files:
                    file_path = Path(root) / file
                    if should_scan_file(file_path):
                        collected.append(file_path)
    return collected


def format_text_output(result: ScanResult, filepath_display: str) -> str:
    """Format scan results for standard terminal display."""
    if result.is_exempt:
        return f"{filepath_display}: [EXEMPT] Opted out of stylometric scan"
    if not result.findings:
        return f"{filepath_display}: [PASSED] Clean"

    lines = [f"{filepath_display} (Locale: {result.profile_code}):"]
    for finding in result.findings:
        loc = f"L{finding.line_number}: " if finding.line_number else ""
        lines.append(f"  [{finding.severity}] {loc}{finding.message}")
    return "\n".join(lines)


def run_scan(
    paths: Sequence[str],
    locale_override: str | None = None,
    strict: bool = False,
    advisory_threshold: int = 4,
    json_mode: bool = False,
    quiet: bool = False,
) -> int:
    """Execute scan across targeted paths and return the process exit code."""
    profile = resolve_locale(locale_override)
    engine = ProseEngine(profile=profile, strict=strict, advisory_threshold=advisory_threshold)

    # Stdin handling if requested via '-'
    if len(paths) == 1 and paths[0] == "-":
        content = sys.stdin.read()
        lines = content.splitlines()
        res = engine.check(lines, filepath="stdin.md")
        if json_mode:
            payload = {
                "file": "stdin",
                "locale": res.profile_code,
                "passed": res.passed,
                "exit_code": res.exit_code,
                "findings": [
                    {
                        "check_id": f.check_id,
                        "severity": f.severity,
                        "line": f.line_number,
                        "message": f.message,
                    }
                    for f in res.findings
                ],
            }
            print(json.dumps(payload, indent=2))
        else:
            print(format_text_output(res, "stdin"))
        return res.exit_code

    targets = paths if paths else ["."]
    files = collect_files(targets)

    if not files:
        if not quiet:
            print("No matching files found to scan.")
        return 0

    worst_exit_code = 0
    total_findings = 0
    results_payload = []

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except (IOError, UnicodeDecodeError) as err:
            if not quiet:
                print(f"Error reading {file_path}: {err}", file=sys.stderr)
            worst_exit_code = max(worst_exit_code, 1)
            continue

        res = engine.check(lines, filepath=str(file_path))
        total_findings += len(res.findings)
        worst_exit_code = max(worst_exit_code, res.exit_code)

        if json_mode:
            results_payload.append({
                "file": str(file_path),
                "locale": res.profile_code,
                "passed": res.passed,
                "exit_code": res.exit_code,
                "findings": [
                    {
                        "check_id": f.check_id,
                        "severity": f.severity,
                        "line": f.line_number,
                        "message": f.message,
                    }
                    for f in res.findings
                ],
            })
        else:
            if not res.passed or not quiet:
                print(format_text_output(res, str(file_path)))

    if json_mode:
        summary = {
            "version": __version__,
            "files_scanned": len(files),
            "worst_exit_code": worst_exit_code,
            "results": results_payload,
        }
        print(json.dumps(summary, indent=2))
    elif not quiet:
        status = "PASSED" if worst_exit_code == 0 else f"FAILED (code {worst_exit_code})"
        print(f"\nScan complete: {len(files)} file(s) evaluated. Status: {status}.")

    return worst_exit_code


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point for agent-prose."""
    parser = argparse.ArgumentParser(
        prog="agent-prose",
        description="Deterministic Anti-RLHF Stylometric Gate for Autonomous Agents by Nitivra.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Paths to markdown, text, or HTML files and directories (use '-' for stdin).",
    )
    parser.add_argument(
        "-l", "--locale",
        help="Dialect profile override (e.g. en-AU, en-US, en-GB).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enforce strict mode: promote all advisory warnings to blocking failures (exit code 1).",
    )
    parser.add_argument(
        "--advisory-threshold",
        type=int,
        default=4,
        help="Number of advisory warnings required to trigger exit code 2 (default: 4).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON results.",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress output for passing files.",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"agent-prose {__version__}",
    )

    args = parser.parse_args(argv)
    code = run_scan(
        paths=args.paths,
        locale_override=args.locale,
        strict=args.strict,
        advisory_threshold=args.advisory_threshold,
        json_mode=args.json,
        quiet=args.quiet,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
