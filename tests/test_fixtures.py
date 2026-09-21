"""Regression tests running against curated markdown document fixtures."""
from __future__ import annotations

from pathlib import Path
from agent_prose.engine import ProseEngine
from agent_prose.profiles.en_au import PROFILE_EN_AU
from agent_prose.profiles.en_us import PROFILE_EN_US

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_clean_spec_fixture_passes() -> None:
    """Clean specification fixture must pass with zero findings under en-AU and en-US."""
    fixture_path = FIXTURES_DIR / "clean_spec.md"
    lines = fixture_path.read_text(encoding="utf-8").splitlines()

    engine_au = ProseEngine(profile=PROFILE_EN_AU)
    res_au = engine_au.check(lines, filepath=str(fixture_path))
    assert res_au.passed is True
    assert len(res_au.findings) == 0

    engine_us = ProseEngine(profile=PROFILE_EN_US)
    res_us = engine_us.check(lines, filepath=str(fixture_path))
    assert res_us.passed is True
    assert len(res_us.findings) == 0


def test_mixed_violations_fixture_detected() -> None:
    """Fixture with multiple AI tells must detect each distinct defect category."""
    fixture_path = FIXTURES_DIR / "mixed_violations.md"
    lines = fixture_path.read_text(encoding="utf-8").splitlines()

    engine = ProseEngine(profile=PROFILE_EN_US)
    res = engine.check(lines, filepath=str(fixture_path))
    check_ids = [f.check_id for f in res.findings]

    # Verify each anticipated category was caught
    assert "contractions" in check_ids
    assert "copula_avoidance" in check_ids
    assert "banned_words" in check_ids
    assert "construction_patterns" in check_ids
    assert "trailing_participial" in check_ids

    # Contraction is blocking, so exit code must be 1
    assert res.exit_code == 1


def test_code_heavy_fixture_zero_false_positives() -> None:
    """Technical markdown with dense code, tables, and type hints must produce zero findings."""
    fixture_path = FIXTURES_DIR / "code_heavy.md"
    lines = fixture_path.read_text(encoding="utf-8").splitlines()

    engine = ProseEngine(profile=PROFILE_EN_AU)
    res = engine.check(lines, filepath=str(fixture_path))
    assert res.passed is True
    assert len(res.findings) == 0


def test_opt_out_fixture_bypasses_all_checks() -> None:
    """Fixture with in-band marker must bypass all checks despite containing violations."""
    fixture_path = FIXTURES_DIR / "opt_out_file.md"
    lines = fixture_path.read_text(encoding="utf-8").splitlines()

    engine = ProseEngine(profile=PROFILE_EN_AU)
    res = engine.check(lines, filepath=str(fixture_path))
    assert res.is_exempt is True
    assert res.passed is True
    assert len(res.findings) == 0
