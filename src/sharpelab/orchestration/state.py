"""Complete typed state and rejected-proposal records."""

from pydantic import BaseModel, ConfigDict, Field

from sharpelab.agents.schemas import (
    PlannerOutput,
    ProvenanceOutput,
    ReportOutput,
    ReviewerOutput,
)
from sharpelab.agents.semantic_validation import PlannerSemanticValidationResult
from sharpelab.orchestration.audit import AuditEvent
from sharpelab.schemas.evidence import EvidenceItem
from sharpelab.schemas.inference import InferenceResult
from sharpelab.schemas.methods import MethodDecision


class RejectedProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    proposal_type: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class AgenticWorkflowState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    mode: str
    example_id: str | None = None
    input_frequency: str = Field(min_length=1)
    input_sample_size: int | None = Field(default=None, ge=1)
    input_data_fingerprint: str | None = Field(default=None, min_length=1)
    fallback_used: bool
    evidence: tuple[EvidenceItem, ...]
    provenance_output: ProvenanceOutput | None = None
    planner_output: PlannerOutput
    planner_semantic_validation: PlannerSemanticValidationResult
    initial_decision: MethodDecision
    reviewer_output: ReviewerOutput
    final_decision: MethodDecision
    inference_results: tuple[InferenceResult, ...] = ()
    report: ReportOutput
    rejected_proposals: tuple[RejectedProposal, ...] = ()
    accepted_agent_requests: tuple[str, ...] = ()
    budget_usage: dict[str, object]
    audit_events: tuple[AuditEvent, ...]
