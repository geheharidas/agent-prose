"""Tests for regional dialect profiles, resolution cascade, and domain context exemptions."""
from __future__ import annotations

import os
from agent_prose.engine import ProseEngine
from agent_prose.profiles import get_profile, resolve_locale
from agent_prose.profiles.en_au import PROFILE_EN_AU
from agent_prose.profiles.en_gb import PROFILE_EN_GB
from agent_prose.profiles.en_us import PROFILE_EN_US


def test_en_au_prohibits_ize_and_serial_comma() -> None:
    """Australian English profile must flag -ize spellings and Oxford commas."""
    engine = ProseEngine(profile=PROFILE_EN_AU)

    # -ize spelling check
    res_ize = engine.check_text("We need to organize the database tables.")
    assert "ize_spelling" in [f.check_id for f in res_ize.findings]
    assert any(f.severity == "BLOCKING" for f in res_ize.findings if f.check_id == "ize_spelling")

    # Oxford comma check
    res_serial = engine.check_text("The report summarizes risks, issues, and decisions from the audit.")
    assert "serial_comma" in [f.check_id for f in res_serial.findings]

    # -ise spelling and non-serial comma pass
    res_clean = engine.check_text("We need to organise the database tables.\n\nThe report summarises risks, issues and decisions.")
    assert "ize_spelling" not in [f.check_id for f in res_clean.findings]
    assert "serial_comma" not in [f.check_id for f in res_clean.findings]


def test_en_us_allows_ize_and_serial_comma() -> None:
    """American English profile must permit -ize spellings and Oxford commas."""
    engine = ProseEngine(profile=PROFILE_EN_US)

    text = "We need to organize the database tables.\n\nThe report summarizes risks, issues, and decisions."
    res = engine.check_text(text)
    check_ids = [f.check_id for f in res.findings]
    assert "ize_spelling" not in check_ids
    assert "serial_comma" not in check_ids


def test_en_gb_prohibits_ize() -> None:
    """British English profile must flag -ize spellings."""
    engine = ProseEngine(profile=PROFILE_EN_GB)

    res = engine.check_text("The organisation decided to prioritize technical security.")
    assert "ize_spelling" in [f.check_id for f in res.findings]


def test_context_exemptions() -> None:
    """Domain context exemptions must prevent false alarms for legitimate terms."""
    engine = ProseEngine(profile=PROFILE_EN_AU)

    # 'foster' is banned as a buzzword, but exempt in 'foster care' or child placement
    res_foster_exempt = engine.check_text("The department manages foster care placements across the state.")
    assert "banned_words" not in [f.check_id for f in res_foster_exempt.findings]

    res_foster_violation = engine.check_text("We must foster innovation across our teams.")
    assert "banned_words" in [f.check_id for f in res_foster_violation.findings]

    # 'ecosystem' is banned as a metaphor, but exempt in 'cloud ecosystem' or 'platform ecosystem'
    res_eco_exempt = engine.check_text("The application connects to the cloud ecosystem through public interfaces.")
    assert "banned_words" not in [f.check_id for f in res_eco_exempt.findings]

    res_eco_violation = engine.check_text("Our vibrant partner ecosystem delivers ongoing value.")
    assert "banned_words" in [f.check_id for f in res_eco_violation.findings]


def test_locale_cascade_resolution(monkeypatch) -> None:
    """Resolution cascade must respect priority: CLI override > env var > default."""
    # 1. Default fallback
    monkeypatch.delenv("AGENT_PROSE_LOCALE", raising=False)
    monkeypatch.delenv("PROSE_LOCALE", raising=False)
    profile = resolve_locale()
    assert profile.code in ("en-US", "en-AU", "en-GB")

    # 2. Environment variable override
    monkeypatch.setenv("AGENT_PROSE_LOCALE", "en-AU")
    profile_env = resolve_locale()
    assert profile_env.code == "en-AU"

    # 3. Explicit argument override
    profile_cli = resolve_locale(cli_override="en-GB")
    assert profile_cli.code == "en-GB"
