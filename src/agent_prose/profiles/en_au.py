"""Australian English (en-AU) Dialect Profile for agent-prose.

Standard: Australian Government Style Manual / Macquarie Dictionary.
- Serial comma: Banned before conjunctions in lists.
- Spelling: Strict -ise, colour, centre, licence (noun), programme.
"""
from __future__ import annotations

import re
from agent_prose.profiles.base import DialectProfile

EN_AU_STEM_WORDS = [
    # Classic AI buzzwords and metaphors
    "leverage", "utilize", "utilise", "comprehensive", "robust",
    "empower", "holistic", "paradigm", "innovative",
    "seamless", "streamline", "revolutionise", "revolutionize",
    "disrupt", "disruptive", "scalable", "impactful", "turnkey",
    "delve", "harness", "foster", "underscore", "elevate",
    "curate", "facilitate", "enhance", "navigate",
    "synergy", "tapestry", "mosaic", "kaleidoscope",
    "realm", "pivotal", "myriad", "ecosystem", "landscape",
    # Modern 2026 prestige stems
    "crucial", "nuance", "bedrock", "linchpin", "cornerstone",
    "bespoke", "imperative", "paramount",
]

EN_AU_EXACT_PHRASES = [
    "cutting-edge", "cutting edge",
    "paradigm shift",
    "best-in-class", "best in class",
    "game-changing", "game changing", "game-changer", "game changer",
    "world-class", "world class",
    "next-generation", "next generation",
    "state-of-the-art", "state of the art",
    "deep dive", "stakeholder alignment",
    "value-add", "thought leadership",
    "move the needle",
    "low-hanging fruit", "low hanging fruit",
    "it is worth noting that",
    "at its core",
    "a testament to",
    # Modern 2026 conversational and concessive scaffolding
    "simply put", "put simply", "in simple terms",
    "that being said", "to be sure", "in essence",
    "fundamentally speaking", "moving forward", "looking ahead",
]

EN_AU_CONTEXT_EXEMPTIONS = {
    "foster": [
        re.compile(r"\bfoster\s+(care|carer|carers|child|children|parent|parents|family|families|placement|placements|home|homes)\b", re.IGNORECASE),
        re.compile(r"\b[A-Z][a-z]+\s+Foster\b"),
    ],
    "ecosystem": [
        re.compile(r"\b(?:platform|data|technology|tech|software|cloud|digital|developer|startup|innovation)\s+ecosystem\b", re.IGNORECASE),
        re.compile(r"\becosystem\s+(?:of\s+(?:tools|services|partners|vendors|providers))\b", re.IGNORECASE),
    ],
    "navigate": [
        re.compile(r"\bnavigate\s+(?:to|back|away|between|within|the\s+(?:page|menu|site|app|interface|screen|tab|dashboard))\b", re.IGNORECASE),
    ],
    "enhance": [
        re.compile(r"\benhanced?\s+(?:entity|attribute|ER|security|encryption)\b", re.IGNORECASE),
    ],
    "facilitate": [
        re.compile(r"\bfacilitat(?:e[ds]?|ing|ion)\s+(?:workshop|session|meeting|discussion)\b", re.IGNORECASE),
        re.compile(r"\bfacilitation\s+guide\b", re.IGNORECASE),
    ],
    "landscape": [
        re.compile(r"\blandscape\s+(?:mode|orientation|photo|photograph|photography|painting|architect\w*|gardening|design)\b", re.IGNORECASE),
        re.compile(r"\b(?:portrait|A4|page)\s+(?:or\s+)?landscape\b|\blandscape\s+or\s+portrait\b", re.IGNORECASE),
        re.compile(r"\blandscap(?:ing|er|ers)\b", re.IGNORECASE),
    ],
    "crucial": [
        re.compile(r"\bmission[- ]crucial\b", re.IGNORECASE),
        re.compile(r"\bsecurity[- ]crucial\b", re.IGNORECASE),
        re.compile(r"\bsafety[- ]crucial\b", re.IGNORECASE),
    ],
    "bedrock": [
        re.compile(r"\bbedrock\s+(?:layer|tier|stratum|formation|service|engine|model|linux)\b", re.IGNORECASE),
        re.compile(r"\bAWS\s+Bedrock\b", re.IGNORECASE),
    ],
    "bespoke": [
        re.compile(r"\bbespoke\s+(?:contract|agreement|schedule|clause|terms|procurement|hardware)\b", re.IGNORECASE),
    ],
    "imperative": [
        re.compile(r"\bimperative\s+(?:programming|paradigm|code|style|syntax|command|statement)\b", re.IGNORECASE),
        re.compile(r"\bstatutory\s+imperative\b", re.IGNORECASE),
        re.compile(r"\bregulatory\s+imperative\b", re.IGNORECASE),
    ],
    "nuance": [
        re.compile(r"\bNuance\s+(?:Communications|Dragon|PowerMic)\b", re.IGNORECASE),
        re.compile(r"\bphonetic\s+nuance\b", re.IGNORECASE),
    ],
}

PROFILE_EN_AU = DialectProfile(
    code="en-AU",
    name="Australian English (Style Manual / Macquarie)",
    allow_serial_comma=False,
    allow_ize_spelling=False,
    banned_stem_words=EN_AU_STEM_WORDS,
    banned_exact_phrases=EN_AU_EXACT_PHRASES,
    context_exemptions=EN_AU_CONTEXT_EXEMPTIONS,
)
