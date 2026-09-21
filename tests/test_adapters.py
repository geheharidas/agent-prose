"""Tests for model-specific prompt priming adapters and dynamic calibration generation."""
from __future__ import annotations

from agent_prose.adapters import get_adapter_prompt
from agent_prose.profiles.en_au import PROFILE_EN_AU
from agent_prose.profiles.en_us import PROFILE_EN_US


def test_claude_adapter_prompt() -> None:
    """Claude adapter prompt must target prestige words and synthetic balance."""
    prompt = get_adapter_prompt("claude", profile=PROFILE_EN_AU)
    assert "crucial" in prompt
    assert "nuance" in prompt
    assert "not only X, but also Y" in prompt
    assert "Australian English" in prompt
    assert "-ise" in prompt


def test_gemini_adapter_prompt() -> None:
    """Gemini adapter prompt must target burstiness and trailing participial clauses."""
    prompt = get_adapter_prompt("gemini", profile=PROFILE_EN_AU)
    assert "sentence lengths" in prompt
    assert "trailing participial" in prompt


def test_grok_adapter_prompt() -> None:
    """Grok adapter prompt must target conversational swagger and flow arrows."""
    prompt = get_adapter_prompt("grok", profile=PROFILE_EN_AU)
    assert "flow arrows" in prompt
    assert "swagger" in prompt


def test_copilot_adapter_prompt() -> None:
    """Copilot adapter prompt must target corporate fluff and greetings."""
    prompt = get_adapter_prompt("copilot", profile=PROFILE_EN_AU)
    assert "corporate marketing fluff" in prompt
    assert "customer-service" in prompt


def test_muse_adapter_prompt() -> None:
    """Muse adapter prompt must target straight ASCII and contractions."""
    prompt = get_adapter_prompt("muse", profile=PROFILE_EN_AU)
    assert "ASCII" in prompt
    assert "Contractions are prohibited" in prompt


def test_unknown_model_fallback() -> None:
    """Unknown model names must receive the safe universal default priming block."""
    prompt = get_adapter_prompt("unknown-experimental-model", profile=PROFILE_EN_US)
    assert "American English" in prompt
    assert "ASCII characters only" in prompt
    assert "Contractions are prohibited" in prompt


def test_dialect_adaptation_us_vs_au() -> None:
    """Dialect profile must alter the orthography instruction in the prompt."""
    prompt_au = get_adapter_prompt("claude", profile=PROFILE_EN_AU)
    assert "-ise" in prompt_au
    assert "Oxford comma" in prompt_au

    prompt_us = get_adapter_prompt("claude", profile=PROFILE_EN_US)
    assert "American English" in prompt_us
    assert "-ise spellings" not in prompt_us
    assert "Do not use the Oxford comma" not in prompt_us
