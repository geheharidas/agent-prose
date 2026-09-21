<!-- agent-prose: off -->
# agent-prose

> Deterministic Anti-RLHF Stylometric Gate for Autonomous Agents.  
> Created and maintained by **Nitivra** (<gehe@nitivra.com.au>).

[![CI](https://github.com/geheharidas/agent-prose/actions/workflows/test.yml/badge.svg)](https://github.com/geheharidas/agent-prose/actions)
[![PyPI](https://img.shields.io/pypi/v/agent-prose.svg)](https://pypi.org/project/agent-prose/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)

Traditional linters check human spelling and punctuation. Large language models rarely make those mistakes.

Human readers identify synthetic writing through deeper structural patterns: **cadence uniformity, evasive linking verbs and artificial balance**.

Foundation models refined through Reinforcement Learning from Human Feedback (RLHF) exhibit predictable stylometric habits:
- **Monotone Sentence Cadence**: Running four or five consecutive sentences of nearly identical word count (18 to 24 words).
- **Copula Avoidance**: Refusing to write direct statements like "X is Y", substituting evasive phrases such as "X serves as Y", "stands as" or "represents a".
- **Prestige Scaffolding Stems**: Overusing academic filler like "crucial", "nuance", "bedrock", "linchpin" and "cornerstone".
- **Synthetic Balance**: Forcing clauses into formulaic balance structures like "not only X, but also Y".
- **Tacked-on Participial Tails**: Appending weak trailing participial phrases to sentence endings (", ensuring that...", ", enabling...").

`agent-prose` is a zero-dependency Python quality gate and pre-commit hook that detects these structural distortions deterministically in under two milliseconds.

---

## Why It Matters

When software engineering teams deploy autonomous agents to generate documentation, pull request summaries, technical specifications and customer communications, text quality directly reflects company credibility.

If your documentation reads like generic corporate boilerplate, readers tune out immediately.

`agent-prose` replaces subjective editorial debates with an automated, reproducible quality gate in your continuous integration pipeline.

---

## What It Evaluates

1. **Sliding-Window Burstiness Analysis**: Measures syntactic variance across five-sentence blocks. Requires sentence length standard deviation to reach at least 6.0, penalising monotone runs.
2. **Direct Copula Enforcement**: Flags evasive linking verbs and restores direct declarative active voice.
3. **Pluggable Dialect Packs**:
   - **Australian English (`en-AU`)**: Australian Government Style Manual and Macquarie standard. Strict `-ise` spellings, British orthography (`colour`, `centre`) and Oxford comma banned.
   - **American English (`en-US`)**: Chicago Manual of Style and AP standard. `-ize` spellings and serial comma permitted.
   - **British English (`en-GB`)**: Oxford UK standard.
4. **Technical Shields**:
   - **Code blocks**: Triple-backtick fenced blocks are shielded against false positives.
   - **Inline code**: Backtick spans are ignored during spelling and banned-word scans.
   - **Markdown tables**: Tabular columns and pipes do not distort sentence cadence statistics.
   - **Frontmatter**: YAML frontmatter headers are bypassed automatically.
5. **Two-Tier Severity Architecture**:
   - **Blocking Defects (Exit Code 1)**: Fatal issues including non-ASCII smart quotes, invalid dialect spellings, contractions and raw flow arrows (`->`) in narrative prose.
   - **Advisory Warnings**: Cadence anomalies, prestige stems and synthetic balance.
   - **Promotion Quota (Exit Code 2)**: Accumulating four or more advisory warnings promotes the scan to a blocking process exit.
6. **Agent Swarm Remediation Bounds**: Includes recommended two-pass repair loop specifications to prevent autonomous agents from getting trapped in circular editing loops.

---

## Installation

Install from PyPI:

```bash
pip install agent-prose
```

Or run instantly without installation using `uv`:

```bash
uv tool run agent-prose path/to/document.md
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/geheharidas/agent-prose.git
```

---

## Quickstart

Scan a single document:

```bash
agent-prose README.md
```

Scan an entire directory recursively:

```bash
agent-prose docs/
```

Pipe standard input directly:

```bash
cat specification.md | agent-prose -
```

Specify a dialect profile:

```bash
# Australian English (strict -ise, colour, Oxford comma banned):
agent-prose --locale en-AU docs/

# American English (-ize, color, Oxford comma permitted):
agent-prose --locale en-US docs/
```

Run in strict mode (all warnings become blocking errors):

```bash
agent-prose --strict docs/
```

Suppress passing files to view only issues:

```bash
agent-prose --quiet docs/
```

Emit machine-readable JSON results for automated CI tooling:

```bash
agent-prose --json docs/
```

---

## Pre-Commit Hook Integration

Add `agent-prose` to your repository `.pre-commit-config.yaml` to gate pull requests automatically:

```yaml
repos:
  - repo: https://github.com/geheharidas/agent-prose
    rev: v1.0.1
    hooks:
      - id: agent-prose
        args: ["--locale", "en-AU"]
```

---

## File Opt-Out Directives

To exclude intentional raw text, negative test fixtures or third-party vendored documentation from evaluation, add an opt-out marker to the first five lines of the file:

```markdown
<!-- agent-prose: off -->
```

Or use the shared alias:

```markdown
<!-- writing-quality: off -->
```

`agent-prose` will mark the file as `[EXEMPT]` and exit cleanly with code 0.

---

## Dialect Resolution Cascade

`agent-prose` resolves your active regional profile through an automated 5-stage cascade:
1. Command-line argument: `--locale <code|path>`
2. Project configuration: `.proserc.json` or `[tool.agent-prose]` in `pyproject.toml`
3. Environment variable: `AGENT_PROSE_LOCALE`
4. Host operating system locale detection: `locale.getlocale()`
5. Fallback baseline: `en-US`

---

## Multi-Agent Swarm Priming Adapters

Preventing errors before generation is faster than remediation. `agent-prose` provides calibration blocks tailored to specific model family failure modes:

- **Anthropic Claude**: Suppresses prestige academic scaffolding (`crucial`, `nuance`, `bedrock`).
- **Google Gemini**: Enforces burstiness variation and eliminates trailing participial clauses.
- **xAI Grok**: Suppresses informal conversational swagger and prose arrows (`->`).
- **Meta Muse / Llama**: Enforces strict dialect orthography and bans contractions.
- **Microsoft Copilot**: Eliminates corporate marketing fluff (`empower`, `seamless`) and conversational customer-service patter.

View adapter templates in `src/agent_prose/adapters/` or generate them dynamically:

```python
from agent_prose.adapters import get_adapter_prompt

claude_prompt = get_adapter_prompt("claude", profile=None)
print(claude_prompt)
```

---

## Zero Dependencies, Sub-2ms Latency

`agent-prose` relies exclusively on Python standard library modules (`re`, `pathlib`, `collections`, `statistics`, `json`, `locale`).

It introduces zero third-party supply chain risks, installs in seconds and scans complete technical specifications in under two milliseconds.

---

## Contributing and Security

- Guidelines for submitting dialect profiles: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Security reporting policy: [`SECURITY.md`](SECURITY.md)
- Direct contact: `gehe@nitivra.com.au`

---

## License

MIT License. Copyright (c) 2026 **Nitivra**.
