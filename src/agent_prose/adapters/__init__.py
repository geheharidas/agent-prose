"""
Model-specific prompt priming adapters for agent-prose.
Created and maintained by Nitivra.

Provides calibration prompts to eliminate vendor-specific RLHF stylometric tells.
Supported model families:
  - Anthropic Claude
  - Google Gemini
  - xAI Grok
  - Meta Muse / Llama
  - Microsoft Copilot
"""
from __future__ import annotations

from typing import Dict
from agent_prose.profiles.base import DialectProfile
from agent_prose.profiles import resolve_locale

ADAPTER_TEMPLATES: Dict[str, str] = {
    "claude": (
        "[WRITING INVARIANT] Ban prestige filler words: crucial, nuance, bedrock, "
        "linchpin, cornerstone, bespoke, imperative. Do not use 'not only X, but also Y' "
        "synthetic balance. Do not hedge using 'that being said' or 'to be sure'. "
        "State technical trade-offs with numbers and precise dependencies."
    ),
    "gemini": (
        "[WRITING INVARIANT] Vary sentence lengths deliberately (mix 6-word statements "
        "with 24-word complex sentences). Avoid uniform bullet lists. Do not use "
        "trailing participial clauses (', ...ing'). Limit sentences to at most two commas."
    ),
    "grok": (
        "[WRITING INVARIANT] Eliminate informal conversational swagger ('Here is the kicker', "
        "'Let us get into it'). Do not use raw flow arrows (->) in prose; write complete "
        "sentences with active verbs. Maintain rigorous engineering delivery."
    ),
    "muse": (
        "[WRITING INVARIANT] Use straight ASCII characters only (no em dashes or curly quotes). "
        "Contractions are prohibited (write 'do not', 'cannot', 'it is'). "
        "Ban conversational fillers and deliver factual analysis directly."
    ),
    "copilot": (
        "[WRITING INVARIANT] Contractions are prohibited (write 'do not', 'cannot', 'it is'). "
        "Ban corporate marketing fluff (empower, seamless, streamline, leverage). "
        "Do not include customer-service greetings or conversational sign-offs ('Certainly!', 'Happy to help!'). "
        "Use straight ASCII characters only (no em dashes, no curly quotes). State facts directly using 'is' or 'are'."
    ),
}


def get_adapter_prompt(model: str, profile: DialectProfile | None = None) -> str:
    """Generate system prompt priming block for a specified model and dialect."""
    target_profile = profile or resolve_locale()
    key = model.strip().lower()

    base_instruction = ADAPTER_TEMPLATES.get(key)
    if not base_instruction:
        base_instruction = (
            "[WRITING INVARIANT] Use straight ASCII characters only. Contractions are prohibited. "
            "Deliver factual analysis directly without conversational filler or synthetic balance."
        )

    dialect_rule = (
        f"You must write in {target_profile.name}."
    )
    if not target_profile.allow_ize_spelling:
        dialect_rule += " Use -ise spellings (organise, analyse, prioritise) and British/Commonwealth orthography (colour, centre)."
    if not target_profile.allow_serial_comma:
        dialect_rule += " Do not use the Oxford comma before conjunctions in lists."

    return f"{dialect_rule} {base_instruction}"


__all__ = ["get_adapter_prompt", "ADAPTER_TEMPLATES"]
