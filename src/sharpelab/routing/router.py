"""Top-level deterministic evidence router."""

from sharpelab.config import ExperimentConfig, RoutingConfig
from sharpelab.routing.abstention import evaluate_abstention, evaluate_claim_abstentions
from sharpelab.routing.eligibility import evaluate_eligibility
from sharpelab.routing.policy import select_primary
from sharpelab.schemas.evidence import EvidenceFinding, EvidenceItem
from sharpelab.schemas.methods import MethodDecision


def route_methods(
    evidence: tuple[EvidenceItem, ...],
    routing: RoutingConfig,
    experiment: ExperimentConfig,
) -> MethodDecision:
    eligibility = evaluate_eligibility(evidence, routing, experiment)
    abstention = evaluate_abstention(evidence, eligibility, routing)
    claim_abstentions = evaluate_claim_abstentions(evidence, experiment)
    eligible_ids = tuple(item.method_id for item in eligibility if item.eligible)
    conflicts = _unresolved_conflicts(evidence)
    info = tuple(
        dict.fromkeys(
            "Provide complete trial/search provenance."
            for item in evidence
            if item.claim == "selection_provenance_complete"
            and item.finding is EvidenceFinding.INCONCLUSIVE
        )
    )
    warnings = tuple(
        dict.fromkeys(warning for item in evidence for warning in item.warnings)
    )
    references = tuple(item.evidence_id for item in evidence)
    if abstention is not None:
        return MethodDecision(
            selected_method=None,
            rationale="Deterministic abstention rules were triggered.",
            eligibility=eligibility,
            alternatives=eligible_ids,
            abstention=abstention,
            claim_abstentions=claim_abstentions,
            unresolved_conflicts=conflicts,
            information_requests=info,
            warnings=warnings,
            evidence_references=references,
            tie_break_rule="configured method priority",
        )
    primary = select_primary(eligibility, routing)
    if primary is None:
        raise RuntimeError(
            "eligible methods exist but configured priority selects none"
        )
    sensitivity = tuple(
        method_id
        for method_id in routing.method_priority
        if method_id in eligible_ids and method_id != primary
    )
    return MethodDecision(
        selected_method=primary,
        rationale=(
            "Selected by explicit configured priority among eligible, "
            "non-sensitivity-only methods."
        ),
        eligibility=eligibility,
        sensitivity_methods=sensitivity,
        alternatives=tuple(
            method_id for method_id in eligible_ids if method_id != primary
        ),
        claim_abstentions=claim_abstentions,
        unresolved_conflicts=conflicts,
        information_requests=info,
        warnings=warnings,
        evidence_references=references,
        tie_break_rule="first eligible method in routing.method_priority",
    )


def _unresolved_conflicts(evidence: tuple[EvidenceItem, ...]) -> tuple[str, ...]:
    grouped: dict[str, set[EvidenceFinding]] = {}
    for item in evidence:
        grouped.setdefault(item.claim, set()).add(item.finding)
    conflicts = [
        f"Conflicting evidence remains for claim: {claim}"
        for claim, findings in grouped.items()
        if any(
            value in findings
            for value in (EvidenceFinding.SUPPORTS, EvidenceFinding.SUPPORT)
        )
        and any(
            value in findings
            for value in (EvidenceFinding.CONTRADICTS, EvidenceFinding.CONTRADICTION)
        )
    ]
    return tuple(conflicts)
