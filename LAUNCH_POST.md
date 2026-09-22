<!-- writing-quality: off -->
<!-- agent-prose: off -->
# Announcing agent-prose: Deterministic Stylometric Gate for AI-Generated Text

Teams that let autonomous agents write documentation meet the same quiet failure. The page reads like a press release. The sentences are uniform, evasive and over-hedged. A spelling check passes. A human reader still marks it as machine text.

The habits are consistent across model families trained with Reinforcement Learning from Human Feedback.

**Monotone cadence.** Four or five consecutive sentences land within a few words of each other. The reader feels the rhythm before they name it.

**Copula avoidance.** Instead of "X is Y", the model substitutes an evasive linking phrase. The substitution is reflexive.

**Prestige scaffolding.** Academic filler clusters together. The words add no information. They perform seriousness.

**Synthetic balance.** Clauses are forced into a symmetry the ideas do not have.

**Trailing participial tails.** A sentence that should end acquires ", ensuring..." or ", enabling...". The clause adds nothing.

When those habits reach production documentation, they cost credibility with the readers who notice. Those are the readers who matter.

Today, Nitivra releases `agent-prose`.

`agent-prose` is a zero-dependency Python quality gate and pre-commit hook. It detects the five habits above with the Python standard library. It runs in CI or as a pre-commit hook. Dialect packs cover Australian, American and British English.

Install it:

    pip install agent-prose

Or run without a permanent install:

    uv tool run agent-prose README.md

Repository: https://github.com/geheharidas/agent-prose

Which agent platform produces the most consistent prestige scaffolding in your docs, and has anything fixed it at generation time?
