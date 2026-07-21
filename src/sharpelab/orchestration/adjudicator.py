"""Deterministic validation and execution of bounded agent requests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType

from sharpelab.agents.schemas import PlannerOutput, ReviewerOutput
from sharpelab.agents.semantic_validation import (
    DiagnosticPermission,
    PlannerSemanticContext,
    PlannerSemanticValidationResult,
    normalize_identifier,
    planner_output_fingerprint,
    registered_alias_target,
)
from sharpelab.config import IMPLEMENTED_METHOD_IDS, Phase2Config
from sharpelab.data.returns import ReturnInput
from sharpelab.diagnostics.provenance import ResearchProvenance
from sharpelab.diagnostics.registry import run_named_diagnostic
from sharpelab.orchestration.audit import AuditTrail
from sharpelab.orchestration.budgets import BudgetExceeded, BudgetLedger
from sharpelab.orchestration.state import RejectedProposal
from sharpelab.schemas.evidence import EvidenceItem
from sharpelab.schemas.methods import MethodDecision


@dataclass(frozen=True, slots=True)
class ToolSpec:
    tool_id: str
    description: str
    kind: str
    diagnostic_name: str | None = None
    configuration_field: str | None = None
    configuration_ids: tuple[str, ...] = ("default",)
    claim_ids: tuple[str, ...] = ()


TOOL_REGISTRY: Mapping[str, ToolSpec] = MappingProxyType(
    {
        "data-quality-summary": ToolSpec(
            "data-quality-summary",
            "Validate and summarize return data quality.",
            "diagnostic",
            diagnostic_name="data-quality",
            configuration_field="data_quality",
            claim_ids=(
                "data_validity",
                "sample_size_adequate",
                "variance_adequate",
                "return_concentration_risk",
                "timestamp_quality",
            ),
        ),
        "return-dependence": ToolSpec(
            "return-dependence",
            "Evaluate linear return dependence.",
            "diagnostic",
            diagnostic_name="linear-dependence",
            configuration_field="linear_dependence",
            claim_ids=(
                "linear_independence",
                "claim:return-dependence-unresolved",
            ),
        ),
        "squared-return-dependence": ToolSpec(
            "squared-return-dependence",
            "Evaluate dependence in squared returns.",
            "diagnostic",
            diagnostic_name="squared-return-dependence",
            configuration_field="squared_dependence",
            claim_ids=(
                "absence_of_squared_return_dependence",
                "claim:squared-return-dependence-unresolved",
            ),
        ),
        "distribution-diagnostic": ToolSpec(
            "distribution-diagnostic",
            "Evaluate skewness, kurtosis, and Gaussian shape.",
            "diagnostic",
            diagnostic_name="distribution-shape",
            configuration_field="distribution",
            claim_ids=("gaussian_shape", "finite_fourth_moment_plausible"),
        ),
        "stability-diagnostic": ToolSpec(
            "stability-diagnostic",
            "Evaluate split-sample structural stability.",
            "diagnostic",
            diagnostic_name="split-sample-stability",
            configuration_field="stability",
            claim_ids=(
                "structural_stability",
                "claim:structural-stability-unresolved",
            ),
        ),
        "iid-gaussian-sharpe": ToolSpec(
            "iid-gaussian-sharpe", "Audited IID Gaussian Sharpe inference.", "inference"
        ),
        "mertens-psr": ToolSpec(
            "mertens-psr", "Audited Mertens variance and frequentist PSR.", "inference"
        ),
        "hac-sharpe": ToolSpec(
            "hac-sharpe", "Audited HAC Sharpe inference.", "inference"
        ),
        "circular-block-bootstrap": ToolSpec(
            "circular-block-bootstrap", "Audited circular-block bootstrap.", "inference"
        ),
        "sensitivity-comparison": ToolSpec(
            "sensitivity-comparison",
            "Compare typed conclusions across eligible methods.",
            "comparison",
        ),
    }
)


def build_planner_semantic_context(
    request_visible_ids: Sequence[str],
    *,
    allowed_evidence_references: Sequence[str],
) -> PlannerSemanticContext:
    """Bind semantic validation to the exact allowlist shown to the planner."""
    permissions: list[DiagnosticPermission] = []
    canonical_seen: set[str] = set()
    for visible_id in request_visible_ids:
        normalized = normalize_identifier(visible_id)
        canonical = registered_alias_target(normalized) or normalized
        spec = TOOL_REGISTRY.get(canonical)
        if spec is None or spec.kind != "diagnostic":
            raise ValueError(
                f"planner-visible diagnostic is not registered: {visible_id}"
            )
        if canonical in canonical_seen:
            raise ValueError(
                f"planner allowlist has duplicate canonical ID: {canonical}"
            )
        canonical_seen.add(canonical)
        permissions.append(
            DiagnosticPermission(
                request_visible_id=visible_id,
                canonical_id=canonical,
                configuration_ids=spec.configuration_ids,
            )
        )
    return PlannerSemanticContext(
        permissions=tuple(permissions),
        allowed_evidence_references=tuple(allowed_evidence_references),
    )


class DeterministicAdjudicator:
    def __init__(
        self,
        budget: BudgetLedger,
        audit: AuditTrail,
        *,
        allow_unobserved_diagnostic_claims: bool = False,
    ) -> None:
        self.budget = budget
        self.audit = audit
        self.called_requests: set[str] = set()
        self.allow_unobserved_diagnostic_claims = allow_unobserved_diagnostic_claims

    def execute_planner_requests(
        self,
        output: PlannerOutput,
        *,
        semantic_validation: PlannerSemanticValidationResult,
        returns: ReturnInput,
        config: Phase2Config,
        provenance: ResearchProvenance | None,
        evidence: tuple[EvidenceItem, ...],
        timestamps: Sequence[datetime | None] | None = None,
    ) -> tuple[tuple[EvidenceItem, ...], tuple[str, ...], tuple[RejectedProposal, ...]]:
        if semantic_validation.source_fingerprint != planner_output_fingerprint(output):
            raise ValueError("planner semantic result does not match parsed output")
        self.audit.append(
            "planner-semantic-validation",
            "deterministic-semantic-validator",
            semantic_validation.model_dump(mode="json"),
        )
        if not semantic_validation.valid:
            reason = "semantic-validation:" + ",".join(
                item.value for item in semantic_validation.failure_categories
            )
            proposal_ids = tuple(
                f"{item.diagnostic_id}:{item.configuration_id}"
                for item in output.requested_diagnostics
            ) or ("planner-output",)
            semantic_rejected = tuple(
                RejectedProposal(
                    proposal_type="diagnostic",
                    proposal_id=proposal_id,
                    reason=reason,
                )
                for proposal_id in proposal_ids
            )
            for item in semantic_rejected:
                self.audit.append(
                    "proposal-rejected",
                    "deterministic-adjudicator",
                    {
                        "proposal_id": item.proposal_id,
                        "status": "rejected",
                        "reason": item.reason,
                        "semantic_validation_status": (
                            semantic_validation.overall_status.value
                        ),
                        "budget_before": self.budget.snapshot(),
                        "budget_after": self.budget.snapshot(),
                    },
                )
            return evidence, (), semantic_rejected
        normalized = semantic_validation.normalized_output
        if normalized is None:
            raise ValueError("valid planner semantic result lacks normalized output")
        accepted: list[str] = []
        rejected: list[RejectedProposal] = []
        combined = list(evidence)
        evidence_claims = {item.claim for item in evidence}
        for request in sorted(
            normalized.requested_diagnostics, key=lambda item: item.priority
        ):
            key = f"{request.diagnostic_id}:{request.configuration_id}"
            spec = TOOL_REGISTRY.get(request.diagnostic_id)
            budget_before = self.budget.snapshot()
            reason: str | None = None
            if spec is None or spec.kind != "diagnostic":
                reason = "unknown or non-diagnostic tool ID"
            elif request.configuration_id not in spec.configuration_ids:
                reason = "unknown diagnostic configuration ID"
            elif not self.allow_unobserved_diagnostic_claims and not set(
                request.unresolved_claims
            ).issubset(evidence_claims):
                reason = "diagnostic request cites an unknown unresolved claim"
            elif not set(request.unresolved_claims).issubset(spec.claim_ids):
                reason = "diagnostic request is not tied to that tool's claims"
            elif key in self.called_requests:
                reason = "duplicate diagnostic request"
            else:
                try:
                    self.budget.consume_request(key, sensitivity=False)
                except BudgetExceeded as error:
                    reason = str(error)
            if reason is not None:
                rejected.append(
                    RejectedProposal(
                        proposal_type="diagnostic", proposal_id=key, reason=reason
                    )
                )
                self.audit.append(
                    "proposal-rejected",
                    "deterministic-adjudicator",
                    {
                        "proposal_id": key,
                        "status": "rejected",
                        "reason": reason,
                        "budget_before": budget_before,
                        "budget_after": self.budget.snapshot(),
                    },
                )
                continue
            self.called_requests.add(key)
            assert spec is not None and spec.diagnostic_name is not None
            produced = run_named_diagnostic(
                spec.diagnostic_name,
                returns,
                config.diagnostics,
                timestamps=timestamps,
                provenance=provenance,
            )
            existing_ids = {item.evidence_id for item in combined}
            added_ids: list[str] = []
            for item in produced:
                if item.evidence_id not in existing_ids:
                    combined.append(item)
                    existing_ids.add(item.evidence_id)
                    added_ids.append(item.evidence_id)
            accepted.append(key)
            assert spec.configuration_field is not None
            self.audit.append(
                "diagnostic-executed",
                "deterministic-adjudicator",
                {
                    "proposal_id": key,
                    "status": "accepted",
                    "tool_id": spec.tool_id,
                    "configuration_id": request.configuration_id,
                    "configuration": getattr(
                        config.diagnostics, spec.configuration_field
                    ).model_dump(mode="json"),
                    "evidence_ids": [item.evidence_id for item in produced],
                    "new_evidence_ids": added_ids,
                    "budget_before": budget_before,
                    "budget_after": self.budget.snapshot(),
                },
            )
        return tuple(combined), tuple(accepted), tuple(rejected)

    def validate_review(
        self,
        output: ReviewerOutput,
        *,
        evidence: tuple[EvidenceItem, ...],
        decision: MethodDecision,
    ) -> tuple[tuple[str, ...], tuple[RejectedProposal, ...]]:
        evidence_ids = {item.evidence_id for item in evidence}
        eligible = {item.method_id for item in decision.eligibility if item.eligible}
        rejected: list[RejectedProposal] = []
        for challenge in output.supported_challenges:
            unknown_evidence = set(challenge.evidence_references) - evidence_ids
            unknown_methods = set(challenge.method_ids) - IMPLEMENTED_METHOD_IDS
            if unknown_evidence or unknown_methods:
                reason = (
                    f"unknown references: evidence={sorted(unknown_evidence)}, "
                    f"methods={sorted(unknown_methods)}"
                )
                rejected.append(
                    RejectedProposal(
                        proposal_type="challenge",
                        proposal_id=challenge.challenge_id,
                        reason=reason,
                    )
                )
                self.audit.append(
                    "proposal-rejected",
                    "deterministic-adjudicator",
                    {
                        "proposal_id": challenge.challenge_id,
                        "status": "rejected",
                        "reason": reason,
                        "evidence_references": list(challenge.evidence_references),
                        "method_ids": list(challenge.method_ids),
                    },
                )
            else:
                self.audit.append(
                    "challenge-accepted",
                    "deterministic-adjudicator",
                    {
                        "proposal_id": challenge.challenge_id,
                        "status": "accepted",
                        "evidence_references": list(challenge.evidence_references),
                        "method_ids": list(challenge.method_ids),
                    },
                )
        accepted: list[str] = []
        for method_id in output.requested_sensitivity_methods:
            budget_before = self.budget.snapshot()
            reason: str | None = None
            if method_id not in IMPLEMENTED_METHOD_IDS:
                reason = "unknown sensitivity method"
            elif method_id not in eligible:
                reason = "agent cannot override deterministic ineligibility"
            elif decision.selected_method is None:
                reason = "sensitivity request cannot bypass deterministic abstention"
            elif method_id not in decision.sensitivity_methods:
                reason = "method is not a deterministic sensitivity option"
            else:
                try:
                    self.budget.consume_request(method_id, sensitivity=True)
                except BudgetExceeded as error:
                    reason = str(error)
            if reason is not None:
                rejected.append(
                    RejectedProposal(
                        proposal_type="sensitivity",
                        proposal_id=method_id,
                        reason=reason,
                    )
                )
                self.audit.append(
                    "proposal-rejected",
                    "deterministic-adjudicator",
                    {
                        "proposal_id": method_id,
                        "status": "rejected",
                        "reason": reason,
                        "budget_before": budget_before,
                        "budget_after": self.budget.snapshot(),
                    },
                )
            else:
                accepted.append(method_id)
                self.audit.append(
                    "sensitivity-accepted",
                    "deterministic-adjudicator",
                    {
                        "proposal_id": method_id,
                        "status": "accepted",
                        "method_id": method_id,
                        "budget_before": budget_before,
                        "budget_after": self.budget.snapshot(),
                    },
                )
        return tuple(accepted), tuple(rejected)
