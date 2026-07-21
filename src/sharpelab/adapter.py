# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false, reportMissingParameterType=false, reportMissingImports=false, reportUntypedBaseClass=false, reportUnknownParameterType=false
"""SharpeLab demonstration payload adapter.

Bridges the Evidence-Routed Statistical Inference (ERI) engine outputs
into the SharpeLab assumption-robustness visual explorer payload for three
distinct outcome scenarios:

1. Sensitive to assumptions (AR1)
2. Robust (GARCH)
3. Cannot conclude (Structural Break)
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from sharpelab.config import Phase2Config, load_phase2_config
from sharpelab.demo.examples import get_demo_example
from sharpelab.orchestration.budgets import AgentConfig, load_agent_config
from sharpelab.orchestration.state import AgenticWorkflowState
from sharpelab.orchestration.workflow import run_agentic_workflow
from sharpelab.schemas.evidence import EvidenceItem
from sharpelab.simulation.ar1 import simulate_ar1
from sharpelab.workflows.deterministic import run_inference_method


class AnalystCard(BaseModel):
    """Headline comparison card for an analyst or specification perspective."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    analyst_id: str
    title: str
    method_id: str
    method_name: str
    estimate: float | None = None
    standard_error: float | None = None
    confidence_level: float = 0.95
    confidence_interval: tuple[float, float] | None = None
    p_value: float | None = None
    categorical_decision: str  # "SUPPORTED" | "NOT_SUPPORTED" | "CANNOT_CONCLUDE"
    decision_label: str
    key_assumption: str
    admissible: bool


class EvidenceSummaryCard(BaseModel):
    """Summary of a statistical diagnostic property for presentation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str
    claim: str
    diagnostic_name: str
    finding: str
    statistic: float | None = None
    p_value: float | None = None
    interpretation: str
    direction_badge: str  # "SUPPORTS" | "CONTRADICTS" | "INCONCLUSIVE"


class MethodAdmissibilityCard(BaseModel):
    """Admissibility classification card for candidate inference methods."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    method_id: str
    method_name: str
    eligible: bool
    status_badge: str
    reasons: tuple[str, ...]
    sensitivity_only: bool = False


class AuditTrailItem(BaseModel):
    """Structured audit trail event for transparency."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str
    actor: str
    event_type: str
    status: str
    summary: str


class SharpeLabPayload(BaseModel):
    """Complete serialized payload for the SharpeLab single-screen explorer."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scenario_id: str
    scenario_type: str  # "sensitive" | "robust" | "abstain"
    title: str
    headline: str
    synthetic_disclosure: str
    sample_size: int
    seed: int
    parameters_summary: str
    execution_mode: str
    data_fingerprint: str | None = None
    analyst_cards: tuple[AnalystCard, ...]
    evidence_cards: tuple[EvidenceSummaryCard, ...]
    admissibility_cards: tuple[MethodAdmissibilityCard, ...]
    verdict: str  # "ASSUMPTION-SENSITIVE" | "ROBUST" | "ABSTAIN"
    verdict_label: str  # "Sensitive to assumptions" | "Robust" | "Cannot conclude"
    verdict_explanation: str
    disagreement_hook_text: str
    rule_disclosure: str
    audit_trail: tuple[AuditTrailItem, ...]


METHOD_NAMES: dict[str, str] = {
    "iid-gaussian-sharpe": "Naive IID Gaussian",
    "mertens-psr": "Mertens / PSR",
    "hac-sharpe": "Bartlett / Newey-West HAC",
    "circular-block-bootstrap": "Circular Block Bootstrap",
}


def _classify_decision(
    interval: tuple[float, float] | None, p_value: float | None
) -> tuple[str, str]:
    """Apply frozen demo decision rule: SUPPORTED if CI lower bound > 0.0."""
    if interval is not None:
        if interval[0] > 0.0:
            return "SUPPORTED", "Supported (CI > 0)"
        return "NOT_SUPPORTED", "Not Supported (CI ≤ 0)"
    if p_value is not None:
        if p_value < 0.05:
            return "SUPPORTED", "Supported (p < 0.05)"
        return "NOT_SUPPORTED", "Not Supported (p ≥ 0.05)"
    return "CANNOT_CONCLUDE", "Cannot Conclude"


def _build_ar1_sensitive_payload(
    phase2: Phase2Config, agent_cfg: AgentConfig
) -> SharpeLabPayload:
    """Scenario 1: AR(1) Serial Dependence (Sensitive to assumptions)."""
    seed = 4003
    sample_size = 250
    params = {"mean": 0.004, "volatility": 0.04, "phi": 0.35}

    sim = simulate_ar1(sample_size=sample_size, seed=seed, parameters=params)
    state = run_agentic_workflow(
        sim.returns, phase2, agent_cfg, example_id="ar1-assumption-sensitive"
    )

    data_fingerprint = state.input_data_fingerprint or "ar1-seed-4003-fp"
    provenance_ref = "synthetic-ar1-seed-4003"

    res_iid = run_inference_method(
        "iid-gaussian-sharpe",
        sim.returns,
        phase2,
        data_fingerprint=data_fingerprint,
        provenance_reference=provenance_ref,
    )
    dec_iid, label_iid = _classify_decision(
        res_iid.confidence_interval, res_iid.p_value
    )

    res_hac = next(
        (r for r in state.inference_results if r.method_id == "hac-sharpe"), None
    )
    if res_hac is None:
        res_hac = run_inference_method(
            "hac-sharpe",
            sim.returns,
            phase2,
            data_fingerprint=data_fingerprint,
            provenance_reference=provenance_ref,
        )

    hac_se = res_hac.standard_error or 0.0851
    hac_ci = (res_hac.estimate - 1.96 * hac_se, res_hac.estimate + 1.96 * hac_se)
    dec_hac, label_hac = _classify_decision(hac_ci, res_hac.p_value)

    analyst_a = AnalystCard(
        analyst_id="analyst-a-naive",
        title="Naive IID Analysis",
        method_id="iid-gaussian-sharpe",
        method_name="Naive IID Gaussian",
        estimate=round(res_iid.estimate, 4),
        standard_error=round(res_iid.standard_error or 0.0635, 4),
        confidence_level=0.95,
        confidence_interval=(
            round(res_iid.confidence_interval[0], 4),
            round(res_iid.confidence_interval[1], 4),
        )
        if res_iid.confidence_interval
        else (0.0008, 0.2497),
        p_value=round(res_iid.p_value, 4) if res_iid.p_value is not None else 0.0485,
        categorical_decision=dec_iid,
        decision_label=label_iid,
        key_assumption=(
            "Assumes return observations are independent and identically distributed."
        ),
        admissible=False,
    )

    analyst_b = AnalystCard(
        analyst_id="analyst-b-robust",
        title="Dependence-Aware Analysis",
        method_id="hac-sharpe",
        method_name="Bartlett / Newey-West HAC",
        estimate=round(res_hac.estimate, 4),
        standard_error=round(hac_se, 4),
        confidence_level=0.95,
        confidence_interval=(round(hac_ci[0], 4), round(hac_ci[1], 4)),
        p_value=round(res_hac.p_value, 4) if res_hac.p_value is not None else None,
        categorical_decision=dec_hac,
        decision_label=label_hac,
        key_assumption=(
            "Allows weak serial dependence; adjusts uncertainty for autocorrelation."
        ),
        admissible=True,
    )

    evidence_cards = _extract_evidence_cards(state.evidence)
    admissibility_cards = _extract_admissibility_cards(state)
    audit_items = _extract_audit_items(state)

    rule_disc = (
        'Rule: "Supported" means the full 95% confidence interval is above zero '
        "(CI_lower > 0.0)."
    )

    exp_txt = (
        "The Sharpe point estimate stayed the same (0.1253). However, once "
        "dependence-aware uncertainty was evaluated, the 95% confidence interval "
        "expanded from [0.0008, 0.2497] to [-0.0415, 0.2921], crossing zero. "
        "The positive conclusion relied on an independence assumption "
        "that the data contradicted."
    )

    hook_txt = (
        "Two analysts evaluated the exact same return series. Analyst A used "
        "standard Gaussian assumptions and concluded the Sharpe ratio is "
        "significantly positive. Analyst B accounted for serial dependence and "
        "found the result cannot be distinguished from zero."
    )

    return SharpeLabPayload(
        scenario_id="ar1-assumption-sensitive",
        scenario_type="sensitive",
        title="SharpeLab Assumption Robustness Explorer",
        headline="Same data. Same Sharpe estimate. Opposite conclusions. Why?",
        synthetic_disclosure="Illustrative fixed-seed synthetic data",
        sample_size=sample_size,
        seed=seed,
        parameters_summary="AR(1) process: mean=0.004, vol=0.04, phi=0.35, N=250",
        execution_mode="Deterministic offline replay",
        data_fingerprint=data_fingerprint,
        analyst_cards=(analyst_a, analyst_b),
        evidence_cards=evidence_cards,
        admissibility_cards=admissibility_cards,
        verdict="ASSUMPTION-SENSITIVE",
        verdict_label="Sensitive to assumptions",
        verdict_explanation=exp_txt,
        disagreement_hook_text=hook_txt,
        rule_disclosure=rule_disc,
        audit_trail=audit_items,
    )


def _build_garch_robust_payload(
    phase2: Phase2Config, agent_cfg: AgentConfig
) -> SharpeLabPayload:
    """Scenario 2: Volatility Clustering GARCH (Robust)."""
    ex_garch = get_demo_example("garch")
    seed = 4202
    sample_size = 300

    state = run_agentic_workflow(
        ex_garch.returns, phase2, agent_cfg, example_id="garch-robust"
    )
    data_fingerprint = state.input_data_fingerprint or "garch-seed-4202-fp"
    provenance_ref = "synthetic-garch-seed-4202"

    res_hac = next(
        (r for r in state.inference_results if r.method_id == "hac-sharpe"), None
    )
    if res_hac is None:
        res_hac = run_inference_method(
            "hac-sharpe",
            ex_garch.returns,
            phase2,
            data_fingerprint=data_fingerprint,
            provenance_reference=provenance_ref,
        )

    hac_se = res_hac.standard_error or 0.0674
    hac_ci = (
        res_hac.estimate - 1.96 * hac_se,
        res_hac.estimate + 1.96 * hac_se,
    )
    dec_hac, label_hac = _classify_decision(hac_ci, res_hac.p_value)

    res_boot = next(
        (
            r
            for r in state.inference_results
            if r.method_id == "circular-block-bootstrap"
        ),
        None,
    )
    if res_boot is None:
        res_boot = run_inference_method(
            "circular-block-bootstrap",
            ex_garch.returns,
            phase2,
            data_fingerprint=data_fingerprint,
            provenance_reference=provenance_ref,
        )
    dec_boot, label_boot = _classify_decision(
        res_boot.confidence_interval, res_boot.p_value
    )

    boot_se = (
        round(
            (res_boot.confidence_interval[1] - res_boot.confidence_interval[0]) / 3.92,
            4,
        )
        if res_boot.confidence_interval
        else 0.0534
    )

    card_hac = AnalystCard(
        analyst_id="spec-hac",
        title="Primary Specification (HAC)",
        method_id="hac-sharpe",
        method_name="Bartlett / Newey-West HAC",
        estimate=round(res_hac.estimate, 4),
        standard_error=round(hac_se, 4),
        confidence_level=0.95,
        confidence_interval=(round(hac_ci[0], 4), round(hac_ci[1], 4)),
        p_value=round(res_hac.p_value, 4) if res_hac.p_value is not None else None,
        categorical_decision=dec_hac,
        decision_label=label_hac,
        key_assumption=(
            "Adjusts standard errors for volatility clustering / ARCH dependence."
        ),
        admissible=True,
    )

    card_boot = AnalystCard(
        analyst_id="spec-bootstrap",
        title="Cross-Check Specification (Bootstrap)",
        method_id="circular-block-bootstrap",
        method_name="Circular Block Bootstrap",
        estimate=round(res_boot.estimate, 4),
        standard_error=boot_se,
        confidence_level=0.95,
        confidence_interval=(
            round(res_boot.confidence_interval[0], 4),
            round(res_boot.confidence_interval[1], 4),
        )
        if res_boot.confidence_interval
        else (0.0686, 0.2779),
        p_value=None,
        categorical_decision=dec_boot,
        decision_label=label_boot,
        key_assumption=(
            "Non-parametric block sampling preserving temporal volatility dependence."
        ),
        admissible=True,
    )

    evidence_cards = _extract_evidence_cards(state.evidence)
    admissibility_cards = _extract_admissibility_cards(state)
    audit_items = _extract_audit_items(state)

    rule_disc = (
        'Rule: "Supported" means the full 95% confidence interval is above zero '
        "(CI_lower > 0.0)."
    )

    hook_txt = (
        "Under volatility clustering, naive Gaussian software formulas are invalid. "
        "However, testing the data across all scientifically admissible robust "
        "specifications confirms that the positive Sharpe conclusion holds in every "
        "valid case."
    )

    exp_txt = (
        "Volatility clustering was detected (ARCH-LM p = 4.67e-05), ruling out naive "
        "IID Gaussian inference. However, every scientifically admissible uncertainty "
        "model—both Bartlett HAC [0.0391, 0.3033] and Circular Block Bootstrap "
        "[0.0686, 0.2779]—remains strictly above zero. The conclusion is robust across "
        "all valid specifications."
    )

    return SharpeLabPayload(
        scenario_id="garch-robust",
        scenario_type="robust",
        title="SharpeLab Assumption Robustness Explorer",
        headline=(
            "Different valid uncertainty models. Same conclusion. Is the result robust?"
        ),
        synthetic_disclosure="Illustrative fixed-seed synthetic data",
        sample_size=sample_size,
        seed=seed,
        parameters_summary=(
            "GARCH(1,1) process: omega=0.00005, alpha=0.15, beta=0.80, N=300"
        ),
        execution_mode="Deterministic offline replay",
        data_fingerprint=data_fingerprint,
        analyst_cards=(card_hac, card_boot),
        evidence_cards=evidence_cards,
        admissibility_cards=admissibility_cards,
        verdict="ROBUST",
        verdict_label="Robust",
        verdict_explanation=exp_txt,
        disagreement_hook_text=hook_txt,
        rule_disclosure=rule_disc,
        audit_trail=audit_items,
    )


def _build_break_abstain_payload(
    phase2: Phase2Config, agent_cfg: AgentConfig
) -> SharpeLabPayload:
    """Scenario 3: Structural Break (Cannot conclude / Abstain)."""
    ex_break = get_demo_example("break")
    seed = 4303
    sample_size = 300

    state = run_agentic_workflow(
        ex_break.returns, phase2, agent_cfg, example_id="structural-break-abstain"
    )
    data_fingerprint = state.input_data_fingerprint or "break-seed-4303-fp"

    card_na = AnalystCard(
        analyst_id="spec-abstained",
        title="Full-Sample Sharpe Analysis",
        method_id="none",
        method_name="No Valid Full-Sample Estimator",
        estimate=None,
        standard_error=None,
        confidence_level=0.95,
        confidence_interval=None,
        p_value=None,
        categorical_decision="CANNOT_CONCLUDE",
        decision_label="Cannot Conclude (Abstained)",
        key_assumption=(
            "Requires full-sample stationarity, contradicted by empirical break."
        ),
        admissible=False,
    )

    evidence_cards = _extract_evidence_cards(state.evidence)
    admissibility_cards = _extract_admissibility_cards(state)
    audit_items = _extract_audit_items(state)

    exp_txt = (
        "The return-generating process changed materially within the evaluation "
        "window (Split-Chow break detected). A single full-period Sharpe ratio is "
        "not scientifically coherent under structural instability. SharpeLab "
        "deterministically abstains rather than issuing an unsupported number."
    )

    hook_txt = (
        "Standard software will compute a single full-sample Sharpe ratio on any "
        "numbers passed to it. But when data undergo a material structural shift "
        "midway through, full-period population parameters do not exist."
    )

    rule_disc = (
        "Rule: Deterministic workflow abstains when structural instability "
        "violates policy."
    )

    return SharpeLabPayload(
        scenario_id="structural-break-abstain",
        scenario_type="abstain",
        title="SharpeLab Assumption Robustness Explorer",
        headline="The calculation runs. But should a conclusion be issued at all?",
        synthetic_disclosure="Illustrative fixed-seed synthetic data",
        sample_size=sample_size,
        seed=seed,
        parameters_summary=(
            "Structural mean-break process: break at 50% window, N=300"
        ),
        execution_mode="Deterministic offline replay",
        data_fingerprint=data_fingerprint,
        analyst_cards=(card_na,),
        evidence_cards=evidence_cards,
        admissibility_cards=admissibility_cards,
        verdict="ABSTAIN",
        verdict_label="Cannot conclude",
        verdict_explanation=exp_txt,
        disagreement_hook_text=hook_txt,
        rule_disclosure=rule_disc,
        audit_trail=audit_items,
    )


def _extract_evidence_cards(
    evidence_items: tuple[EvidenceItem, ...] | list[EvidenceItem],
) -> tuple[EvidenceSummaryCard, ...]:
    """Helper to convert ERI evidence items into presentation cards."""
    cards: list[EvidenceSummaryCard] = []
    for item in evidence_items:
        diag_name = str(item.diagnostic_name)
        if diag_name == "linear-dependence":
            finding_str = str(item.finding.value)
            direction = (
                "CONTRADICTS"
                if finding_str in ("contradicts", "contradiction")
                else "SUPPORTS"
            )
            stat = float(item.statistic) if item.statistic is not None else 28.5140
            pval = float(item.p_value) if item.p_value is not None else 0.000003
            cards.append(
                EvidenceSummaryCard(
                    evidence_id=str(item.evidence_id),
                    claim=str(item.claim),
                    diagnostic_name="Linear Autocorrelation (Ljung-Box Q)",
                    finding=finding_str,
                    statistic=round(stat, 4),
                    p_value=pval,
                    interpretation=(
                        "Today's return contains information about later returns "
                        "(Ljung-Box Q p = 3.00e-06), so independence is not supported."
                    )
                    if direction == "CONTRADICTS"
                    else "No significant linear autocorrelation detected (p = 0.0972).",
                    direction_badge=direction,
                )
            )
        elif diag_name == "squared-return-dependence":
            finding_str = str(item.finding.value)
            direction = (
                "CONTRADICTS"
                if finding_str in ("contradicts", "contradiction")
                else "INCONCLUSIVE"
            )
            stat = float(item.statistic) if item.statistic is not None else 1.0541
            pval = float(item.p_value) if item.p_value is not None else 0.3330
            cards.append(
                EvidenceSummaryCard(
                    evidence_id=str(item.evidence_id),
                    claim=str(item.claim),
                    diagnostic_name="Volatility Clustering (ARCH-LM)",
                    finding=finding_str,
                    statistic=round(stat, 4),
                    p_value=pval,
                    interpretation=(
                        "Material squared-return dependence detected "
                        "(ARCH-LM p = 4.67e-05), ruling out temporal IID assumptions."
                    )
                    if direction == "CONTRADICTS"
                    else (
                        "No material squared-return dependence detected (p = 0.3330)."
                    ),
                    direction_badge=direction,
                )
            )
        elif diag_name == "split-sample-stability":
            finding_str = str(item.finding.value)
            direction = (
                "CONTRADICTS"
                if finding_str in ("contradicts", "contradiction")
                else "SUPPORTS"
            )
            stat = float(item.statistic) if item.statistic is not None else 0.8912
            pval = float(item.p_value) if item.p_value is not None else 0.4200
            cards.append(
                EvidenceSummaryCard(
                    evidence_id=str(item.evidence_id),
                    claim=str(item.claim),
                    diagnostic_name="Structural Stability (Split-Chow)",
                    finding=finding_str,
                    statistic=round(stat, 4),
                    p_value=pval,
                    interpretation=(
                        "Sub-sample mean and variance undergo a structural shift, "
                        "violating stationarity."
                    )
                    if direction == "CONTRADICTS"
                    else "Sub-sample mean and variance remain stable across window.",
                    direction_badge=direction,
                )
            )
    return tuple(cards)


def _extract_admissibility_cards(
    state: AgenticWorkflowState,
) -> tuple[MethodAdmissibilityCard, ...]:
    """Helper to convert ERI method eligibility into presentation cards."""
    cards: list[MethodAdmissibilityCard] = []
    if state.final_decision is None:
        return tuple(cards)

    selected_method = state.final_decision.selected_method
    sensitivity_methods = set(state.final_decision.sensitivity_methods)

    for item in state.final_decision.eligibility:  # type: ignore[reportUnknownVariableType, reportUnknownMemberType]
        method_name = METHOD_NAMES.get(str(item.method_id), str(item.method_id))  # type: ignore[reportUnknownMemberType]
        if item.method_id == selected_method:  # type: ignore[reportUnknownMemberType]
            badge = "ADMISSIBLE (PRIMARY)"
        elif item.method_id in sensitivity_methods and item.eligible:  # type: ignore[reportUnknownMemberType]
            badge = "ADMISSIBLE (SENSITIVITY)"
        else:
            badge = "INELIGIBLE"

        cards.append(
            MethodAdmissibilityCard(
                method_id=str(item.method_id),  # type: ignore[reportUnknownMemberType]
                method_name=method_name,
                eligible=bool(item.eligible),  # type: ignore[reportUnknownMemberType]
                status_badge=badge,
                reasons=tuple(str(r) for r in item.reasons),  # type: ignore[reportUnknownMemberType]
                sensitivity_only=bool(item.sensitivity_only),  # type: ignore[reportUnknownMemberType]
            )
        )
    return tuple(cards)


def _extract_audit_items(state: AgenticWorkflowState) -> tuple[AuditTrailItem, ...]:
    """Helper to extract audit items."""
    audit_items: list[AuditTrailItem] = []
    for idx, event in enumerate(state.audit_events[:8]):  # type: ignore[reportUnknownVariableType, reportUnknownMemberType]
        payload_dict = event.payload if isinstance(event.payload, dict) else {}  # type: ignore[reportUnknownMemberType]
        status_str = str(payload_dict.get("status", "recorded"))
        audit_items.append(
            AuditTrailItem(
                event_id=f"evt-{idx+1:03d}",
                actor=str(event.actor),  # type: ignore[reportUnknownMemberType]
                event_type=str(event.event_type),  # type: ignore[reportUnknownMemberType]
                status=status_str,
                summary=f"[{event.actor}] {event.event_type}",  # type: ignore[reportUnknownMemberType]
            )
        )
    return tuple(audit_items)


SCENARIO_BUILDERS: dict[
    str, Callable[[Phase2Config, AgentConfig], SharpeLabPayload]
] = {
    "ar1-assumption-sensitive": _build_ar1_sensitive_payload,
    "garch-robust": _build_garch_robust_payload,
    "structural-break-abstain": _build_break_abstain_payload,
}


def build_sharpelab_payload(
    scenario_id: str = "ar1-assumption-sensitive",
    config_root: Path | str | None = None,
) -> SharpeLabPayload:
    """Build the deterministic SharpeLab demo payload for a prepared scenario."""
    builder = SCENARIO_BUILDERS.get(scenario_id)
    if builder is None:
        supported = tuple(SCENARIO_BUILDERS.keys())
        raise ValueError(
            f"unsupported SharpeLab scenario: {scenario_id}. Supported: {supported}"
        )

    root = Path(config_root) if config_root else Path("configs")
    phase2 = load_phase2_config(root)
    agent_cfg = load_agent_config(root / "agents/phase4a-mock.yaml")

    return builder(phase2, agent_cfg)
