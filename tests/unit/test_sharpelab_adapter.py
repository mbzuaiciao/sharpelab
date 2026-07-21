"""Unit tests for the SharpeLab demo adapter across all 3 outcome scenarios."""

from __future__ import annotations

import pytest

from sharpelab.adapter import SharpeLabPayload, build_sharpelab_payload


def test_build_sharpelab_payload_ar1_sensitive() -> None:
    payload = build_sharpelab_payload("ar1-assumption-sensitive")

    assert isinstance(payload, SharpeLabPayload)
    assert payload.scenario_id == "ar1-assumption-sensitive"
    assert payload.scenario_type == "sensitive"
    assert payload.seed == 4003
    assert payload.sample_size == 250
    assert "Illustrative fixed-seed synthetic data" in payload.synthetic_disclosure
    assert "Deterministic offline replay" in payload.execution_mode

    assert payload.verdict == "ASSUMPTION-SENSITIVE"
    assert payload.verdict_label == "Sensitive to assumptions"

    assert len(payload.analyst_cards) == 2
    analyst_a = payload.analyst_cards[0]
    analyst_b = payload.analyst_cards[1]

    assert analyst_a.analyst_id == "analyst-a-naive"
    assert analyst_a.method_id == "iid-gaussian-sharpe"
    assert not analyst_a.admissible
    assert analyst_a.categorical_decision == "SUPPORTED"

    assert analyst_b.analyst_id == "analyst-b-robust"
    assert analyst_b.method_id == "hac-sharpe"
    assert analyst_b.admissible
    assert analyst_b.categorical_decision == "NOT_SUPPORTED"

    # Admissibility
    admissibility_map = {c.method_id: c for c in payload.admissibility_cards}
    assert not admissibility_map["iid-gaussian-sharpe"].eligible
    assert admissibility_map["hac-sharpe"].eligible
    assert admissibility_map["circular-block-bootstrap"].eligible


def test_build_sharpelab_payload_garch_robust() -> None:
    payload = build_sharpelab_payload("garch-robust")

    assert isinstance(payload, SharpeLabPayload)
    assert payload.scenario_id == "garch-robust"
    assert payload.scenario_type == "robust"
    assert payload.seed == 4202
    assert payload.sample_size == 300

    assert payload.verdict == "ROBUST"
    assert payload.verdict_label == "Robust"

    # Evidence: ARCH-LM squared dependence
    arch_ev = next(
        (
            e
            for e in payload.evidence_cards
            if "Volatility Clustering" in e.diagnostic_name
        ),
        None,
    )
    assert arch_ev is not None
    assert arch_ev.direction_badge == "CONTRADICTS"

    # Admissibility
    admissibility_map = {c.method_id: c for c in payload.admissibility_cards}
    assert not admissibility_map["iid-gaussian-sharpe"].eligible
    assert admissibility_map["hac-sharpe"].eligible
    assert admissibility_map["hac-sharpe"].status_badge == "ADMISSIBLE (PRIMARY)"
    assert admissibility_map["circular-block-bootstrap"].eligible
    assert (
        admissibility_map["circular-block-bootstrap"].status_badge
        == "ADMISSIBLE (SENSITIVITY)"
    )

    # Analyst Cards (HAC & Bootstrap) both SUPPORTED
    assert len(payload.analyst_cards) == 2
    assert payload.analyst_cards[0].categorical_decision == "SUPPORTED"
    assert payload.analyst_cards[1].categorical_decision == "SUPPORTED"


def test_build_sharpelab_payload_break_abstain() -> None:
    payload = build_sharpelab_payload("structural-break-abstain")

    assert isinstance(payload, SharpeLabPayload)
    assert payload.scenario_id == "structural-break-abstain"
    assert payload.scenario_type == "abstain"
    assert payload.seed == 4303
    assert payload.sample_size == 300

    assert payload.verdict == "ABSTAIN"
    assert payload.verdict_label == "Cannot conclude"

    # Evidence: Structural stability contradiction
    chow_ev = next(
        (
            e
            for e in payload.evidence_cards
            if "Structural Stability" in e.diagnostic_name
        ),
        None,
    )
    assert chow_ev is not None
    assert chow_ev.direction_badge == "CONTRADICTS"

    # Admissibility: All methods ineligible
    for card in payload.admissibility_cards:
        assert not card.eligible
        assert card.status_badge == "INELIGIBLE"

    # Analyst Card shows Cannot Conclude
    assert len(payload.analyst_cards) == 1
    assert payload.analyst_cards[0].categorical_decision == "CANNOT_CONCLUDE"


def test_build_sharpelab_payload_rejects_unknown_scenario() -> None:
    with pytest.raises(ValueError, match="unsupported SharpeLab scenario"):
        build_sharpelab_payload("unknown-scenario")
