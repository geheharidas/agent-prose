<!-- writing-quality: off -->
# agent-prose

> Deterministic Anti-RLHF Stylometric Gate for Autonomous Agents.
> Created and maintained by **Nitivra**.

`agent-prose` is a zero-dependency Python utility and pre-commit hook that eliminates machine cadence, synthetic symmetry, and corporate filler from AI-generated prose.

Unlike traditional linters that target human grammar, `agent-prose` is grounded in empirical natural language processing research to counter Reinforcement Learning from Human Feedback (RLHF) distortions. It executes in under two milliseconds.

---

## Key Capabilities

1. **Sliding-Window Burstiness Analysis**: Enforces syntactic variance. It requires a standard deviation of at least 6.0 across five-sentence windows to eliminate robotic monotony.
2. **Anti-RLHF Cadence Gating**: Detects modern prestige vocabulary, synthetic balance (`not only X, but also Y`), fronted gerund paragraph openers, and performative signposting.
3. **Direct Copula Enforcement**: Flags copula avoidance (`serves as`, `stands as`, `represents a`) in favour of plain factual linking (`is`, `are`).
4. **Two-Tier Severity with Promotion Quotas**: Differentiates fatal document defects (exit code 1) from minor stylistics. Accumulating four or more advisory warnings promotes the output to a blocking failure (exit code 2).
5. **Pluggable Dialect Packs**: Native support for Australian English (`en-AU`), American English (`en-US`), and British English (`en-GB`).
6. **Agent Swarm Remediation Bounds**: Includes built-in multi-agent retry protocols to prevent automated coding swarms from stalling in infinite correction loops.

---

## Installation

Install from PyPI:

```bash
pip install agent-prose
```

Or run directly without installation via `uv`:

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

Specify a dialect profile:

```bash
# Australian English (strict -ise, colour, Oxford comma banned):
agent-prose --locale en-AU docs/

# American English (-ize, color, Oxford comma permitted):
agent-prose --locale en-US docs/
```

---

## Pre-Commit Hook Integration

Add `agent-prose` to your repository `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/geheharidas/agent-prose
    rev: v1.0.0
    hooks:
      - id: agent-prose
        args: ["--locale", "en-US"]
```

---

## Dialect Profiles

`agent-prose` resolves dialect rules through a priority cascade:
1. Command-line argument: `--locale <code|path>`
2. Project configuration: `.proserc.json` or `pyproject.toml`
3. Environment variable: `AGENT_PROSE_LOCALE`
4. Operating system auto-detection: `locale.getdefaultlocale()`
5. Fallback baseline: `en-US`

---

## Autonomous Agent Swarm Adapters

`agent-prose` provides ready-to-use priming blocks for popular model families:
- **Anthropic Claude**: Suppresses prestige academic scaffolding (`crucial`, `nuance`, `bedrock`).
- **Google Gemini**: Enforces burstiness and eliminates trailing participial clauses.
- **xAI Grok**: Suppresses informal swagger and prose arrows (`->`).
- **Meta Muse**: Enforces strict orthography and bans contractions.
- **Microsoft Copilot**: Eliminates corporate fluff (`empower`, `seamless`) and customer-service patter.

View adapter templates in `src/agent_prose/adapters/`.

---

## License

MIT License. Copyright (c) 2026 Nitivra.
