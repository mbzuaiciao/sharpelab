"""Fair free-form monolithic-agent output boundary for Phase 4B."""

from __future__ import annotations

from pydantic import Field, JsonValue, model_validator

from sharpelab.agents.schemas import AgentModel


class MonolithicOutput(AgentModel):
    """Single-response contract; execution is still restricted to registered tools."""

    diagnostic_requests: tuple[str, ...] = ()
    provenance_interpretation: dict[str, JsonValue] = Field(default_factory=dict)
    method_recommendation: str | None = Field(default=None, min_length=1)
    abstain: bool
    report: str = Field(min_length=1, max_length=4_000)
    evidence_references: tuple[str, ...] = ()

    @model_validator(mode="after")
    def coherent_action(self) -> MonolithicOutput:
        if self.abstain and self.method_recommendation is not None:
            raise ValueError(
                "an abstaining monolithic output cannot recommend a method"
            )
        if not self.abstain and self.method_recommendation is None:
            raise ValueError("a non-abstaining monolithic output needs a method")
        if len(self.diagnostic_requests) != len(set(self.diagnostic_requests)):
            raise ValueError("monolithic diagnostic requests must be unique")
        return self


def validate_monolithic_output(payload: object) -> MonolithicOutput:
    return MonolithicOutput.model_validate(payload)
