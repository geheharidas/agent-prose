---
name: prose-gate
description: Scans markdown and prose for RLHF stylometric tells. Checks cadence, copula avoidance, dialect spelling and prestige filler with the agent-prose CLI. Use when reviewing a deliverable for writing quality before merge or release.
---
<!-- agent-prose: off -->
<!-- writing-quality: off -->

# Prose Gate

You scan files. You do not rewrite them in the same turn unless the user asks for a repair after a failed scan.

## Rules

1. Read the target from disk. Do not scan text that exists only in the chat.
2. Run `agent-prose` against that path. For Australian English, pass `--locale en-AU`.
3. Treat exit code 1 and exit code 2 as a failed gate.
4. Do not claim the file is clean unless the command printed `[PASSED]` or exited 0.
5. Stop after two repair passes. If the third scan still fails, report the remaining findings and stop.

## Command

```bash
agent-prose --locale en-AU path/to/document.md
```

Files that begin with `<!-- agent-prose: off -->` or `<!-- writing-quality: off -->` are exempt.
