"""American English (en-US) Dialect Profile for agent-prose.

Standard: Chicago Manual of Style / AP Style.
- Serial comma: Allowed / standard.
- Spelling: -ize, color, center, license (noun) allowed.
- Cadence: Anti-RLHF burstiness, direct copulas, and buzzword bans strictly enforced.
"""
from __future__ import annotations

from agent_prose.profiles.base import DialectProfile
from agent_prose.profiles.en_au import (
    EN_AU_STEM_WORDS,
    EN_AU_EXACT_PHRASES,
    EN_AU_CONTEXT_EXEMPTIONS,
)

# For US English, filter out British/Australian spelling stems like utilize/utilise
EN_US_STEM_WORDS = [w for w in EN_AU_STEM_WORDS if w not in ("utilise", "revolutionise")]

PROFILE_EN_US = DialectProfile(
    code="en-US",
    name="American English (Chicago / AP)",
    allow_serial_comma=True,
    allow_ize_spelling=True,
    banned_stem_words=EN_US_STEM_WORDS,
    banned_exact_phrases=EN_AU_EXACT_PHRASES,
    context_exemptions=EN_AU_CONTEXT_EXEMPTIONS,
)
