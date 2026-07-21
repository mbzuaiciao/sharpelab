"""Recorded free-form specialized-agent recommendations for Phase 4B."""

from __future__ import annotations

from pydantic import Field, JsonValue

from sharpelab.agents.schemas import AgentModel


class FreeFormRoleMessage(AgentModel):
    role: str = Field(min_length=1)
    recommendation: str = Field(min_length=1, max_length=4_000)


class UnconstrainedOutput(AgentModel):
    role_messages: tuple[FreeFormRoleMessage, ...] = Field(min_length=1)
    diagnostic_requests: tuple[str, ...] = ()
    provenance_interpretation: dict[str, JsonValue] = Field(default_factory=dict)
    method_recommendation: str | None = Field(default=None, min_length=1)
    abstain: bool
    report: str = Field(min_length=1, max_length=4_000)
    evidence_references: tuple[str, ...] = ()


def validate_unconstrained_output(payload: object) -> UnconstrainedOutput:
    """Record a free reasoning layer without granting arbitrary execution."""
    return UnconstrainedOutput.model_validate(payload)
