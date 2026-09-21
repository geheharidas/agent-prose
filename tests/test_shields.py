"""Tests for technical shielding, code fences, whitelists, and in-band opt-out markers."""
from __future__ import annotations

import pytest
from agent_prose.engine import ProseEngine
from agent_prose.profiles.en_au import PROFILE_EN_AU


@pytest.fixture
def engine() -> ProseEngine:
    """Return an isolated ProseEngine instance configured for Australian English."""
    return ProseEngine(profile=PROFILE_EN_AU)


def test_fenced_code_blocks_shielded(engine: ProseEngine) -> None:
    """Banned stems, arrows, and contractions inside fenced code blocks must be shielded."""
    text = (
        "# System Script\n\n"
        "Here is the deployment script:\n\n"
        "```python\n"
        "# leverage existing session\n"
        "def route_traffic(req) -> dict:\n"
        "    if not req.is_valid:\n"
        "        raise ValueError(\"it's broken\")\n"
        "    return {\"status\": \"ok\"}\n"
        "```\n\n"
        "The script executes cleanly.\n"
    )
    res = engine.check_text(text)
    # The banned word, arrow, and contraction inside the code fence must not trigger findings
    assert "banned_words" not in [f.check_id for f in res.findings]
    assert "flow_arrows" not in [f.check_id for f in res.findings]
    assert "contractions" not in [f.check_id for f in res.findings]


def test_inline_code_arrow_shielded(engine: ProseEngine) -> None:
    """Type annotations containing '->' inside inline code backticks must not trigger flow_arrows."""
    text = "The signature `def run() -> int:` defines an integer exit code."
    res = engine.check_text(text)
    assert "flow_arrows" not in [f.check_id for f in res.findings]


def test_markdown_tables_shielded(engine: ProseEngine) -> None:
    """Table rows must not trigger burstiness or headline triad false positives."""
    text = (
        "# Metrics Summary\n\n"
        "| Service | Status | Latency |\n"
        "| :--- | :--- | :--- |\n"
        "| Auth | Active | 12ms |\n"
        "| Queue | Active | 4ms |\n"
        "| DB | Active | 8ms |\n\n"
        "The cluster latency is within bounds.\n"
    )
    res = engine.check_text(text)
    assert "rule_of_three" not in [f.check_id for f in res.findings]


def test_yaml_frontmatter_shielded(engine: ProseEngine) -> None:
    """YAML frontmatter metadata must be skipped during segmentation."""
    text = (
        "---\n"
        "title: System Architecture\n"
        "category: cloud-infrastructure\n"
        "tags: [api, gateway, cluster]\n"
        "---\n\n"
        "# Architecture Overview\n\n"
        "The architecture consists of three stateless gateways.\n"
    )
    res = engine.check_text(text)
    assert len(res.findings) == 0


def test_spelling_whitelist_exceptions(engine: ProseEngine) -> None:
    """Legitimate English words ending in -ize must not be flagged in en-AU."""
    text = (
        "The file size is normal.\n\n"
        "We sized the storage cluster accordingly.\n\n"
        "Authorities will seize illicit assets.\n\n"
        "The team earned the annual innovation prize.\n"
    )
    res = engine.check_text(text)
    assert "ize_spelling" not in [f.check_id for f in res.findings]


def test_participial_whitelist_exceptions(engine: ProseEngine) -> None:
    """Sentences ending in legitimate participial prepositions must not be flagged."""
    text_including = "The team verified all subsystems, including the ingress router."
    res_including = engine.check_text(text_including)
    assert "trailing_participial" not in [f.check_id for f in res_including.findings]

    text_using = "We authenticated the external request, using asymmetric keys."
    res_using = engine.check_text(text_using)
    assert "trailing_participial" not in [f.check_id for f in res_using.findings]


def test_copula_context_exemptions(engine: ProseEngine) -> None:
    """Legitimate legal, member, and risk copula phrases must not be flagged."""
    text = "The counsel represents a client in the dispute."
    res = engine.check_text(text)
    assert "copula_avoidance" not in [f.check_id for f in res.findings]

    text_risk = "The configuration represents a risk to network stability."
    res_risk = engine.check_text(text_risk)
    assert "copula_avoidance" not in [f.check_id for f in res_risk.findings]


def test_in_band_opt_out_markers(engine: ProseEngine) -> None:
    """Files with in-band opt-out markers must bypass scanning cleanly."""
    text_agent_prose = (
        "<!-- agent-prose: off -->\n"
        "# Raw Notes\n\n"
        "It's crucial that we leverage synergy.\n"
    )
    res_prose = engine.check_text(text_agent_prose)
    assert res_prose.is_exempt is True
    assert res_prose.passed is True
    assert len(res_prose.findings) == 0

    text_writing_quality = (
        "<!-- writing-quality: off -->\n"
        "# Raw Notes\n\n"
        "It's crucial that we leverage synergy.\n"
    )
    res_wq = engine.check_text(text_writing_quality)
    assert res_wq.is_exempt is True
    assert res_wq.passed is True
    assert len(res_wq.findings) == 0


def test_non_ascii_replacements_reported(engine: ProseEngine) -> None:
    """Non-ASCII characters must be flagged with explicit replacement advice."""
    text = "Status: active \u2014 all systems operational."
    res = engine.check_text(text)
    assert "non_ascii" in [f.check_id for f in res.findings]
    assert any("replace with: --" in f.message for f in res.findings)
