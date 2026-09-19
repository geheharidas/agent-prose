"""Tests for cadence, rhythm, copula validation, and stylometric rules in agent-prose."""
from __future__ import annotations

import pytest
from agent_prose.engine import ProseEngine
from agent_prose.profiles.en_us import PROFILE_EN_US


@pytest.fixture
def engine() -> ProseEngine:
    """Return a standard ProseEngine instance configured for American English to isolate cadence tests."""
    return ProseEngine(profile=PROFILE_EN_US)


def test_sentence_length_cap(engine: ProseEngine) -> None:
    """Sentences exceeding 35 words must trigger a sentence_length finding."""
    long_sentence = (
        "This is an excessively prolonged and rambling sentence constructed with the express "
        "intent of surpassing the thirty-five word maximum threshold established by the stylometric "
        "engine to verify that run-on sentences are flagged appropriately without exception every single time."
    )
    result = engine.check_text(long_sentence)
    check_ids = [f.check_id for f in result.findings]
    assert "sentence_length" in check_ids


def test_uniform_burstiness_flagged(engine: ProseEngine) -> None:
    """Monotone sentence lengths with standard deviation below 6.0 must be flagged."""
    # 6 sentences, each approximately 20 words
    monotone_text = (
        "# Background\n\n"
        "The team deployed the new microservice architecture across the staging cluster yesterday morning with full test verification complete.\n\n"
        "All engineers reviewed the pull request thoroughly before merging changes into the primary integration repository branch for deployment.\n\n"
        "System telemetry confirmed that average response latency remained within acceptable operational boundaries under regular customer traffic load.\n\n"
        "Automated monitoring alerts triggered immediately whenever error rates exceeded the predetermined critical thresholds set by infrastructure teams.\n\n"
        "Database migrations concluded without schema conflicts or record locks during the scheduled maintenance window announced to business users.\n\n"
        "Security personnel validated network security policies across all container nodes before granting final production clearance to the release.\n"
    )
    result = engine.check_text(monotone_text)
    check_ids = [f.check_id for f in result.findings]
    assert "burstiness" in check_ids or "monotone_runs" in check_ids


def test_varied_rhythm_passes(engine: ProseEngine) -> None:
    """Prose with dynamic sentence variation (short and long mixed) must pass rhythm checks."""
    varied_text = (
        "# System Architecture\n\n"
        "Speed matters.\n\n"
        "When microservices communicate across network partitions, serialization delays compound quickly into degraded user experiences.\n\n"
        "We chose binary protocols.\n\n"
        "Benchmark results demonstrate a thirty percent throughput improvement across saturated ingress gateway gateways.\n"
    )
    result = engine.check_text(varied_text)
    burstiness_findings = [f for f in result.findings if f.check_id in ("burstiness", "monotone_runs")]
    assert len(burstiness_findings) == 0


def test_copula_avoidance(engine: ProseEngine) -> None:
    """Evasive copulas like 'serves as' or 'boasts' must be flagged in favor of 'is'."""
    text = "The gateway serves as a barrier against unauthorized traffic."
    result = engine.check_text(text)
    check_ids = [f.check_id for f in result.findings]
    assert "copula_avoidance" in check_ids

    direct_text = "The gateway is a barrier against unauthorized traffic."
    result_direct = engine.check_text(direct_text)
    check_ids_direct = [f.check_id for f in result_direct.findings]
    assert "copula_avoidance" not in check_ids_direct


def test_trailing_participial_clause(engine: ProseEngine) -> None:
    """Sentences with trailing participial clauses must be flagged."""
    text = "The workers completed the background processing job, ensuring that all records were synced."
    result = engine.check_text(text)
    check_ids = [f.check_id for f in result.findings]
    assert "trailing_participial" in check_ids


def test_flow_arrow_prohibited(engine: ProseEngine) -> None:
    """Flow arrows in narrative prose must be flagged as blocking violations."""
    text = "The user submits credentials -> the server issues a session token."
    result = engine.check_text(text)
    check_ids = [f.check_id for f in result.findings]
    assert "flow_arrows" in check_ids
    assert any(f.severity == "BLOCKING" for f in result.findings if f.check_id == "flow_arrows")
