<!-- writing-quality: off -->
<!-- agent-prose: off -->
# agent-prose

> Deterministic Anti-RLHF Stylometric Gate for Autonomous Agents.
> Created and maintained by **Nitivra** (gehe@nitivra.com.au).

[![CI](https://github.com/geheharidas/agent-prose/actions/workflows/test.yml/badge.svg)](https://github.com/geheharidas/agent-prose/actions)
[![PyPI](https://img.shields.io/pypi/v/agent-prose.svg)](https://pypi.org/project/agent-prose/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)

The GitHub project, the PyPI package and the command are all `agent-prose`.

Traditional linters catch spelling and punctuation. Large language models almost never make those mistakes. The distortions they produce are structural: cadence uniformity, copula avoidance and forced rhetorical balance.

Foundation models trained with Reinforcement Learning from Human Feedback exhibit predictable stylometric habits:

- **Monotone sentence cadence**. Four or five consecutive sentences land at nearly the same word count, often 18 to 24 words.
- **Copula avoidance**. The plain verb "is" is replaced by evasive linking phrases such as "serves as" or "stands as".
- **Prestige scaffolding**. Academic filler (`crucial`, `nuance`, `bedrock`, `linchpin`, `cornerstone`) clusters together and adds no information.
- **Synthetic balance**. Clauses are forced into symmetry the underlying ideas do not have, including "not only X, but also Y".
- **Trailing participial tails**. Sentences acquire a weak ending such as ", ensuring that..." or ", enabling...".

`agent-prose` is a zero-dependency Python quality gate and pre-commit hook. It detects these distortions with the standard library.

---

## Why It Matters

When engineering teams deploy autonomous agents to generate documentation, pull request summaries and customer communications, text quality is part of company credibility.

A reader who meets generic boilerplate disengages. Text that passes a spelling check can still carry structural tells. Readers who notice those tells trust the page less.

`agent-prose` replaces a subjective edit debate with a repeatable gate in CI.

---

## What It Evaluates

1. **Sliding-window burstiness**. Measures sentence-length variance across five-sentence blocks. A standard deviation under 6.0 is a monotone run.
2. **Direct copula check**. Flags evasive linking verbs.
3. **Dialect packs**. Australian English (`en-AU`, Macquarie and the Australian Government Style Manual), American English (`en-US`, Chicago and AP) and British English (`en-GB`).
4. **Technical shields**. Fenced code blocks, inline code, markdown tables and YAML frontmatter are left out of the prose scan.
5. **Two severities**. Blocking defects exit 1. They include non-ASCII punctuation, invalid dialect spellings, contractions and raw flow arrows in narrative prose. Advisory findings cover cadence, prestige stems and synthetic balance. Four or more advisory findings exit 2. `--strict` promotes every advisory finding to a blocking failure.
6. **Repair bound**. The prose-gate skill tells an agent to stop after two repair passes. The scanner itself does not count passes.

---

## Installation

Install from PyPI:

```bash
pip install agent-prose
```

Run without a permanent install:

```bash
uv tool run agent-prose path/to/document.md
```

Install from this repository:

```bash
git clone https://github.com/geheharidas/agent-prose.git
cd agent-prose
pip install -e .
```

There are no third-party runtime dependencies.

---

## Quickstart

```bash
agent-prose README.md
```

A clean file prints:

```text
README.md: [PASSED] Clean

Scan complete: 1 file(s) evaluated. Status: PASSED.
```

Other entry points:

```bash
agent-prose docs/
agent-prose --locale en-AU docs/
agent-prose --locale en-US docs/
agent-prose --strict docs/
agent-prose --quiet docs/
agent-prose --json docs/
```

`--locale en-AU` requires `-ise` spellings and `colour` or `centre`, and it rejects the serial comma. `--locale en-US` permits `-ize`, `color` and the serial comma. Read stdin with `agent-prose -`.

---

## Pre-Commit Hook Integration

Add the hook to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/geheharidas/agent-prose
    rev: v1.0.1
    hooks:
      - id: agent-prose
        args: ["--locale", "en-AU"]
```

---

## File Opt-Out Directive

Put one of these markers in the first five lines:

```markdown
<!-- agent-prose: off -->
```

```markdown
<!-- writing-quality: off -->
```

The file is reported as `[EXEMPT]` and the process exits 0 for that file.

---

## Dialect Resolution Cascade

`agent-prose` picks a dialect in this order:

1. `--locale <code|path>`
2. `.proserc.json` or `[tool.agent-prose]` in `pyproject.toml`
3. The `AGENT_PROSE_LOCALE` environment variable
4. `locale.getlocale()` on the host
5. Fallback: `en-US`

---

## Agent Platform Integrations

### Grok Build

Copy `integrations/grok/prose_gate.rhai` into `.grok/workflows/`. The workflow runs `agent-prose` on a path.

### Claude Code and Cursor

Copy `integrations/claude/SKILL.md` to `~/.claude/skills/prose-gate/SKILL.md`, or the equivalent Cursor skills directory.

### Model priming adapters

Adapter text lives in `src/agent_prose/adapters/`. Load one from Python:

```python
from agent_prose.adapters import get_adapter_prompt

print(get_adapter_prompt("claude", profile=None))
```

The packs are Claude, Gemini, Grok, Muse or Llama, and Copilot. Each pack names the failure mode that family tends to produce. They do not call a model.

---

## Contributing and Security

- Contribution rules, including new dialect profiles: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Security reports: [`SECURITY.md`](SECURITY.md)
- Contact: `gehe@nitivra.com.au`

The sibling gate for epistemic sycophancy is [`agent-sycophancy`](https://github.com/geheharidas/agent-sycophancy).

---

## License

MIT License. Copyright (c) 2026 **Nitivra** (gehe@nitivra.com.au).
