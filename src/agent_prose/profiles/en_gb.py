"""British English (en-GB) Dialect Profile for agent-prose.

Standard: Oxford / Cambridge Standard UK English.
- Serial comma: Banned in general lists (unless required for ambiguity).
- Spelling: -ise preferred, colour, centre, programme.
"""
from __future__ import annotations

from agent_prose.profiles.base import DialectProfile
from agent_prose.profiles.en_au import (
    EN_AU_STEM_WORDS,
    EN_AU_EXACT_PHRASES,
    EN_AU_CONTEXT_EXEMPTIONS,
)

PROFILE_EN_GB = DialectProfile(
    code="en-GB",
    name="British English (Oxford / UK Standard)",
    allow_serial_comma=False,
    allow_ize_spelling=False,
    banned_stem_words=EN_AU_STEM_WORDS,
    banned_exact_phrases=EN_AU_EXACT_PHRASES,
    context_exemptions=EN_AU_CONTEXT_EXEMPTIONS,
)
