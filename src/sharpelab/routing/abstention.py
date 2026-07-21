"""Explicit deterministic abstention rules."""

from sharpelab.config import ExperimentConfig, RoutingConfig
from sharpelab.schemas.abstention import AbstentionDecision
from sharpelab.schemas.evidence import EvidenceFinding, EvidenceItem
from sharpelab.schemas.methods import MethodEligibility


def evaluate_abstention(
    evidence: tuple[EvidenceItem, ...],
    eligibility: tuple[MethodEligibility, ...],
    routing: RoutingConfig,
) -> AbstentionDecision | None:
    reasons: list[str] = []
    if _contradicts(evidence, "data_validity"):
        reasons.append("Input returns are invalid; no silent imputation is allowed.")
    if _contradicts(evidence, "variance_adequate"):
        reasons.append("Return variance is zero or numerically degenerate.")
    if routing.abstain_on_structural_instability and _contradicts(
        evidence, "structural_stability"
    ):
        reasons.append(
            "Configured policy requires abstention under material structural "
            "instability."
        )
    if not any(
        item.eligible and not item.sensitivity_only for item in eligibility
    ):
        reasons.append(
            "No primary inference method satisfies configured minimum validity "
            "conditions."
        )
    if reasons:
        return AbstentionDecision(
            abstain=True,
            reasons=tuple(dict.fromkeys(reasons)),
        )
    return None


def evaluate_claim_abstentions(
    evidence: tuple[EvidenceItem, ...], experiment: ExperimentConfig
) -> dict[str, AbstentionDecision]:
    """Keep claim-specific limitations separate from global workflow failure."""
    if not experiment.claim_requires_selection_provenance:
        return {}
    provenance_items = tuple(
        item for item in evidence if item.claim == "selection_provenance_complete"
    )
    complete = bool(provenance_items) and all(
        item.finding in (EvidenceFinding.SUPPORTS, EvidenceFinding.SUPPORT)
        for item in provenance_items
    )
    if complete:
        decision = AbstentionDecision(
            abstain=True,
            reasons=(
                "Phase 2 does not implement an audited multiplicity-adjusted "
                "Sharpe method.",
            ),
        )
    else:
        decision = AbstentionDecision(
            abstain=True,
            reasons=(
                "Multiplicity-adjusted Sharpe claims require complete trial/search "
                "provenance and an audited adjustment method.",
            ),
            missing_evidence=("complete trial/search provenance",),
        )
    return {"multiplicity_adjusted_sharpe": decision}


def _contradicts(evidence: tuple[EvidenceItem, ...], claim: str) -> bool:
    return any(
        item.claim == claim
        and item.finding
        in (EvidenceFinding.CONTRADICTS, EvidenceFinding.CONTRADICTION)
        for item in evidence
    )
