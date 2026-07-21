"""Constrained Phase 4A agent input and output contracts."""

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sharpelab.diagnostics.provenance import ProvenanceCompleteness, ResearchProvenance


class AgentModel(BaseModel):
    """Immutable strict base for every agent-visible structure."""

    model_config = ConfigDict(extra="forbid", frozen=True)


Identifier = Annotated[str, Field(min_length=1, max_length=128)]
ConciseText = Annotated[str, Field(min_length=1, max_length=1_000)]
ReportText = Annotated[str, Field(min_length=1, max_length=4_000)]
ProvenanceField = Literal[
    "trials",
    "parameter_searches",
    "markets_or_universes",
    "start_dates_or_windows",
    "failed_trials_retained",
    "trial_dependence_known",
]


class AgentRole(StrEnum):
    DIAGNOSTIC_PLANNER = "diagnostic-planner"
    PROVENANCE = "provenance"
    SKEPTICAL_REVIEWER = "skeptical-reviewer"
    REPORT = "report"


class InformationGain(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConfidenceCategory(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReviewRecommendation(StrEnum):
    ACCEPT = "accept"
    RERUN_DIAGNOSTICS = "re-run-permitted-diagnostics"
    RUN_SENSITIVITY = "run-sensitivity-methods"
    ABSTAIN_OR_QUALIFY = "abstain-or-qualify"


class ProviderMessage(AgentModel):
    role: Identifier
    content: str = Field(min_length=1)


class DiagnosticRequest(AgentModel):
    diagnostic_id: Identifier
    configuration_id: Identifier = "default"
    rationale: ConciseText
    unresolved_claims: tuple[Identifier, ...] = Field(min_length=1)
    priority: int = Field(ge=1, le=5)
    expected_information_gain: InformationGain


class PlannerOutput(AgentModel):
    requested_diagnostics: tuple[DiagnosticRequest, ...] = ()
    rationale: ConciseText
    stop_recommendation: bool

    @model_validator(mode="after")
    def unique_requests(self) -> Self:
        keys = [
            (item.diagnostic_id, item.configuration_id)
            for item in self.requested_diagnostics
        ]
        if len(keys) != len(set(keys)):
            raise ValueError("planner requests must be unique")
        return self


class SourceSupport(AgentModel):
    field_name: ProvenanceField
    exact_excerpt: str = Field(min_length=1, max_length=2_000)


class ProvenanceOutput(AgentModel):
    proposed_provenance: ResearchProvenance
    source_support: tuple[SourceSupport, ...] = ()
    confidence: ConfidenceCategory
    unresolved_fields: tuple[ProvenanceField, ...] = ()
    questions_for_user: tuple[ConciseText, ...] = ()

    @model_validator(mode="after")
    def complete_requires_no_unresolved_fields(self) -> Self:
        if (
            self.proposed_provenance.completeness is ProvenanceCompleteness.COMPLETE
            and self.unresolved_fields
        ):
            raise ValueError("complete provenance cannot retain unresolved fields")
        if len(self.unresolved_fields) != len(set(self.unresolved_fields)):
            raise ValueError("unresolved provenance fields must be unique")
        if self.unresolved_fields and not self.questions_for_user:
            raise ValueError("unresolved provenance requires a user question")
        support_keys = [
            (item.field_name, item.exact_excerpt) for item in self.source_support
        ]
        if len(support_keys) != len(set(support_keys)):
            raise ValueError("provenance support entries must be unique")
        return self


class SupportedChallenge(AgentModel):
    challenge_id: Identifier
    statement: ConciseText
    evidence_references: tuple[Identifier, ...] = Field(min_length=1)
    method_ids: tuple[Identifier, ...] = ()


class ReviewerOutput(AgentModel):
    supported_challenges: tuple[SupportedChallenge, ...] = ()
    requested_sensitivity_methods: tuple[Identifier, ...] = ()
    unresolved_contradictions: tuple[ConciseText, ...] = ()
    recommendation: ReviewRecommendation
    rationale: ConciseText

    @model_validator(mode="after")
    def unique_sensitivities(self) -> Self:
        if len(self.requested_sensitivity_methods) != len(
            set(self.requested_sensitivity_methods)
        ):
            raise ValueError("reviewer sensitivity requests must be unique")
        challenge_ids = [item.challenge_id for item in self.supported_challenges]
        if len(challenge_ids) != len(set(challenge_ids)):
            raise ValueError("reviewer challenge IDs must be unique")
        if any(
            len(item.method_ids) != len(set(item.method_ids))
            for item in self.supported_challenges
        ):
            raise ValueError("challenge method IDs must be unique")
        return self


class ReportOutput(AgentModel):
    estimate: ReportText
    selected_method: Identifier
    eligibility_explanation: ReportText
    rejected_or_weakened_methods: ReportText
    uncertainty: ReportText
    sensitivity_findings: ReportText
    provenance_limitations: ReportText
    abstention_or_qualifications: ReportText
    audit_trace_summary: ReportText
    evidence_references: tuple[Identifier, ...] = ()
    result_references: tuple[Identifier, ...] = ()


AgentOutput = PlannerOutput | ProvenanceOutput | ReviewerOutput | ReportOutput
