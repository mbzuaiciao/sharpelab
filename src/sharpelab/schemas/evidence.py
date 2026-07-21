"""Evidence input contracts."""

from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import Field, FiniteFloat, JsonValue, PositiveInt, model_validator

from sharpelab.schemas._base import PValue, SchemaModel


class EvidenceFinding(StrEnum):
    """Direction of an evidence item relative to the evaluated claim."""

    SUPPORT = "support"
    CONTRADICTION = "contradiction"
    INCONCLUSIVE = "inconclusive"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"


class EvidenceItem(SchemaModel):
    """A single auditable claim and its provenance."""

    evidence_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    finding: EvidenceFinding
    diagnostic_name: str | None = Field(default=None, min_length=1)
    diagnostic_version: str | None = Field(default=None, min_length=1)
    statistic: FiniteFloat | None = None
    structured_output: dict[str, JsonValue] = Field(default_factory=dict)
    p_value: PValue | None = None
    uncertainty: dict[str, JsonValue] = Field(default_factory=dict)
    sample_size: PositiveInt | None = None
    configuration: dict[str, JsonValue] = Field(default_factory=dict)
    assumptions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    methods_enabled: tuple[str, ...] = ()
    methods_weakened: tuple[str, ...] = ()
    methods_ruled_out: tuple[str, ...] = ()
    does_not_establish: tuple[str, ...] = ()
    data_fingerprint: str | None = Field(default=None, min_length=1)
    provenance_reference: str | None = Field(default=None, min_length=1)
    observed_at: datetime | None = None
    attributes: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def reject_blank_audit_entries(self) -> Self:
        """Keep list-like audit metadata stable and non-ambiguous."""
        audit_sequences = (
            self.assumptions,
            self.warnings,
            self.methods_enabled,
            self.methods_weakened,
            self.methods_ruled_out,
            self.does_not_establish,
        )
        if any(not value.strip() for values in audit_sequences for value in values):
            raise ValueError("evidence audit metadata entries must not be blank")
        return self
