"""Tests for AI construction patterns, transition padding, sycophancy, and rule of three."""
from __future__ import annotations

import pytest
from agent_prose.engine import ProseEngine
from agent_prose.profiles.en_us import PROFILE_EN_US


@pytest.fixture
def engine() -> ProseEngine:
    """Return an isolated ProseEngine instance configured for American English."""
    return ProseEngine(profile=PROFILE_EN_US)


def test_construction_3_5a_headline_dash(engine: ProseEngine) -> None:
    """Headline with single dash must be flagged (3.5a)."""
    text = "# System Performance -- Core Latency Metrics\n\nDetails follow."
    res = engine.check_text(text)
    assert any("3.5a" in f.message for f in res.findings)


def test_construction_3_5b_not_just_x_but_y(engine: ProseEngine) -> None:
    """False balance 'not just X but Y' must be flagged (3.5b)."""
    text = "The gate is not just a linter, but an enforcement mechanism."
    res = engine.check_text(text)
    assert any("3.5b" in f.message for f in res.findings)


def test_construction_3_5c_it_is_not_x_it_is_y(engine: ProseEngine) -> None:
    """Contrarian balance 'it is not X -- it is Y' must be flagged (3.5c)."""
    text = "It is not speed -- it is correctness that matters."
    res = engine.check_text(text)
    assert any("3.5c" in f.message for f in res.findings)


def test_construction_3_5d_whether_x_or_y(engine: ProseEngine) -> None:
    """Framing dilemma 'whether X or Y' must be flagged (3.5d)."""
    text = "Whether you are a startup or an enterprise, quality matters."
    res = engine.check_text(text)
    assert any("3.5d" in f.message for f in res.findings)


def test_construction_3_5e_from_x_to_y_headline(engine: ProseEngine) -> None:
    """Headline 'From X to Y' must be flagged (3.5e)."""
    text = "# From Concept to Reality\n\nThe project began last quarter."
    res = engine.check_text(text)
    assert any("3.5e" in f.message for f in res.findings)


def test_construction_3_5f_imagine_opener(engine: ProseEngine) -> None:
    """Hypothetical opener 'Imagine [scenario]' must be flagged (3.5f)."""
    text = "Imagine a system that catches all errors immediately."
    res = engine.check_text(text)
    assert any("3.5f" in f.message for f in res.findings)


def test_construction_3_5g_conversational_scaffolding(engine: ProseEngine) -> None:
    """Conversational scaffolding phrases must be flagged (3.5g)."""
    text = "Here is the thing about distributed consensus algorithms."
    res = engine.check_text(text)
    assert any("3.5g" in f.message for f in res.findings)

    text_unpack = "Let me unpack the security ramifications of this protocol."
    res_unpack = engine.check_text(text_unpack)
    assert any("3.5g" in f.message for f in res_unpack.findings)


def test_construction_3_5h_more_than_just(engine: ProseEngine) -> None:
    """Diminishing comparator 'is more than just' must be flagged (3.5h)."""
    text = "Code quality is more than just passing tests."
    res = engine.check_text(text)
    assert any("3.5h" in f.message for f in res.findings)


def test_construction_3_5j_the_reality_is(engine: ProseEngine) -> None:
    """Intensifier 'the reality is that' must be flagged (3.5j)."""
    text = "The reality is that microservices increase network overhead."
    res = engine.check_text(text)
    assert any("3.5j" in f.message for f in res.findings)


def test_construction_3_5k_what_has_changed_is(engine: ProseEngine) -> None:
    """Reframing 'what has changed is' must be flagged (3.5k)."""
    text = "What has changed is that modern clusters scale dynamically."
    res = engine.check_text(text)
    assert any("3.5k" in f.message for f in res.findings)


def test_construction_3_5l_has_historically_meant(engine: ProseEngine) -> None:
    """Historical drama 'has historically meant' must be flagged (3.5l)."""
    text = "Schema migration has historically meant scheduled downtime."
    res = engine.check_text(text)
    assert any("3.5l" in f.message for f in res.findings)


def test_construction_3_5m_triple_em_dash(engine: ProseEngine) -> None:
    """Sentence interrupted by two dashes must be flagged (3.5m)."""
    text = "The primary server -- despite previous failures -- resumed operations."
    res = engine.check_text(text)
    assert any("3.5m" in f.message for f in res.findings)


def test_construction_3_5p_not_only_but_also(engine: ProseEngine) -> None:
    """Synthetic balance 'not only X, but also Y' must be flagged (3.5p)."""
    text = "The cluster not only logs errors, but also alerts engineers immediately."
    res = engine.check_text(text)
    assert any("3.5p" in f.message for f in res.findings)


def test_construction_3_5q_fronted_gerund_opener(engine: ProseEngine) -> None:
    """Paragraph opener starting with 'By ...ing,' must be flagged (3.5q)."""
    text = "By validating schema contracts early, the team avoids regression bugs."
    res = engine.check_text(text)
    assert any("3.5q" in f.message for f in res.findings)


def test_construction_3_5r_performative_signposting(engine: ProseEngine) -> None:
    """Structural narrating phrases must be flagged (3.5r)."""
    text = "In this section, we will analyse the latency benchmarks."
    res = engine.check_text(text)
    assert any("3.5r" in f.message for f in res.findings)


def test_construction_3_5s_concessive_hedge(engine: ProseEngine) -> None:
    """Concessive throat-clearing hedge must be flagged (3.5s)."""
    text = "That being said, we must verify storage capacity."
    res = engine.check_text(text)
    assert any("3.5s" in f.message for f in res.findings)


def test_construction_3_5t_prescriptive_outro(engine: ProseEngine) -> None:
    """Prescriptive outro cliché must be flagged (3.5t)."""
    text = "Moving forward, organisations must monitor latency continuously."
    res = engine.check_text(text)
    assert any("3.5t" in f.message for f in res.findings)


def test_transition_padding_threshold(engine: ProseEngine) -> None:
    """Using 3 or more transition words in one file must trigger transition_padding."""
    text = (
        "The system processes messages.\n\n"
        "Moreover, it persists audits.\n\n"
        "Furthermore, it notifies workers.\n\n"
        "Additionally, it reports metrics.\n"
    )
    res = engine.check_text(text)
    check_ids = [f.check_id for f in res.findings]
    assert "transition_padding" in check_ids


def test_sycophancy_and_performative_openers(engine: ProseEngine) -> None:
    """Customer-service pleasantries and performative openers must be flagged."""
    text_syco = "I hope this email finds you well as you review the results."
    res_syco = engine.check_text(text_syco)
    assert "sycophancy" in [f.check_id for f in res_syco.findings]

    text_opener = "Certainly! The configuration is complete."
    res_opener = engine.check_text(text_opener)
    assert "sycophancy" in [f.check_id for f in res_opener.findings]


def test_rule_of_three_triads(engine: ProseEngine) -> None:
    """Headline triads and adjective triads must be flagged."""
    text_line = "Fast. Scalable. Secure."
    res_line = engine.check_text(text_line)
    assert "rule_of_three" in [f.check_id for f in res_line.findings]

    text_tail = "The service is flexible, scalable, and resilient."
    res_tail = engine.check_text(text_tail)
    assert "rule_of_three" in [f.check_id for f in res_tail.findings]
