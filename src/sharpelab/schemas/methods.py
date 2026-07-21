"""Method eligibility and routing decision contracts."""

from typing import Self

from pydantic import Field, model_validator

from sharpelab.schemas._base import SchemaModel
from sharpelab.schemas.abstention import AbstentionDecision
from sharpelab.schemas.diagnostics import DiagnosticResult


class MethodEligibility(SchemaModel):
    """Whether a candidate method is eligible, with auditable reasons."""

    method_id: str = Field(min_length=1)
    eligible: bool
    reasons: tuple[str, ...] = ()
    diagnostics: tuple[DiagnosticResult, ...] = ()
    evidence_references: tuple[str, ...] = ()
    weakened: bool = False
    sensitivity_only: bool = False
    missing_requirements: tuple[str, ...] = ()

    @model_validator(mode="after")
    def explain_ineligibility(self) -> Self:
        """Require an explicit explanation for every rejected method."""
        if not self.eligible and not self.reasons:
            raise ValueError("ineligible methods require at least one reason")
        entries = (
            self.reasons,
            self.evidence_references,
            self.missing_requirements,
        )
        if any(not entry.strip() for values in entries for entry in values):
            raise ValueError("eligibility audit entries must not be blank")
        if self.sensitivity_only and not self.eligible:
            raise ValueError("only eligible methods can be sensitivity-only")
        return self


class MethodDecision(SchemaModel):
    """A selected method or an explicit abstention, with sensitivity methods."""

    selected_method: str | None = Field(default=None, min_length=1)
    rationale: str = Field(min_length=1)
    eligibility: tuple[MethodEligibility, ...] = Field(min_length=1)
    sensitivity_methods: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()
    abstention: AbstentionDecision | None = None
    claim_abstentions: dict[str, AbstentionDecision] = Field(default_factory=dict)
    unresolved_conflicts: tuple[str, ...] = ()
    information_requests: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    tie_break_rule: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def selected_method_is_unique_and_eligible(self) -> Self:
        """Ensure the decision points to exactly one eligible candidate."""
        method_ids = [item.method_id for item in self.eligibility]
        if len(method_ids) != len(set(method_ids)):
            raise ValueError("eligibility entries must have unique method IDs")

        if self.selected_method is None:
            if self.abstention is None or not self.abstention.abstain:
                raise ValueError("no method selection requires an abstention")
        else:
            if self.abstention is not None:
                raise ValueError("a selected method cannot also include an abstention")
            selected = [
                item
                for item in self.eligibility
                if item.method_id == self.selected_method
            ]
            if not selected:
                raise ValueError("selected method must appear in eligibility entries")
            if not selected[0].eligible:
                raise ValueError("selected method must be eligible")

        sensitivity_ids = list(self.sensitivity_methods)
        if len(sensitivity_ids) != len(set(sensitivity_ids)):
            raise ValueError("sensitivity methods must be unique")
        if self.selected_method in sensitivity_ids:
            raise ValueError("selected method cannot also be a sensitivity method")
        eligible_ids = {item.method_id for item in self.eligibility if item.eligible}
        if any(method_id not in eligible_ids for method_id in sensitivity_ids):
            raise ValueError("sensitivity methods must be eligible")
        if any(not method_id.strip() for method_id in sensitivity_ids):
            raise ValueError("sensitivity method IDs must not be blank")
        if any(not alternative.strip() for alternative in self.alternatives):
            raise ValueError("alternative method IDs must not be blank")
        audit_entries = (
            self.unresolved_conflicts,
            self.information_requests,
            self.warnings,
            self.evidence_references,
        )
        if any(not entry.strip() for values in audit_entries for entry in values):
            raise ValueError("method-decision audit entries must not be blank")
        if any(not claim.strip() for claim in self.claim_abstentions):
            raise ValueError("claim-abstention identifiers must not be blank")
        if any(
            not decision.abstain for decision in self.claim_abstentions.values()
        ):
            raise ValueError("claim abstentions must contain abstaining decisions")
        return self
