# Announcing agent-prose: An Anti-RLHF Stylometric Gate

Most AI linters search for human spelling errors.

Large language models rarely make those mistakes.

They miss the real reason readers detect machine prose in three seconds: uniform sentence length, evasive verbs and artificial symmetry.

When foundation models undergo reinforcement training, they develop repetitive structural habits:

First, monotone cadence. Systems output four or five consecutive sentences of nearly identical length.

Second, evasive linking verbs. Models decline to write direct statements. They choose weak filler instead of a direct 'is'.

Third, synthetic symmetry. Sentences get forced into formulaic balance clauses.

Fourth, weak tails. Paragraphs end with repetitive participial phrases.

In autonomous agent swarms, written quality reflects company credibility.

When an automated agent drafts technical specifications or architecture records, generic boilerplate erodes client trust.

Engineering teams need deterministic quality gates in their deployment pipelines.

Today, Nitivra releases agent-prose.

It is an open-source Python quality gate.

Zero dependencies.

Execution takes under two milliseconds.

The engine calculates syntactic variance across sliding five-sentence windows, requiring a standard deviation above 6.0 to break robotic cadence.

It provides native profiles for Australian English, American English and British English.

Supported platforms include Claude, Gemini and Grok, alongside Meta Muse and Microsoft Copilot.

The package is available on PyPI and GitHub under the MIT License.

Install:
pip install agent-prose

Repository:
https://github.com/geheharidas/agent-prose

How does your engineering team manage textual quality in autonomous agent workflows?
