"""Inference output contracts."""

from typing import Self

from pydantic import Field, FiniteFloat, JsonValue, model_validator

from sharpelab.schemas._base import (
    CalibrationScore,
    ConfidenceLevel,
    NonNegativeFloat,
    PosteriorProbability,
    PValue,
    SchemaModel,
)
from sharpelab.schemas.diagnostics import DiagnosticResult


class InferenceResult(SchemaModel):
    """A finite point estimate with optional uncertainty information."""

    inference_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    method_version: str | None = Field(default=None, min_length=1)
    method_configuration: dict[str, JsonValue] = Field(default_factory=dict)
    estimate: FiniteFloat
    standard_error: NonNegativeFloat | None = None
    confidence_level: ConfidenceLevel = 0.95
    confidence_interval: tuple[FiniteFloat, FiniteFloat] | None = None
    p_value: PValue | None = None
    posterior_probability: PosteriorProbability | None = None
    calibration_score: CalibrationScore | None = None
    sample_frequency: str | None = Field(default=None, min_length=1)
    periods_per_year: NonNegativeFloat | None = None
    annualization_convention: str | None = Field(default=None, min_length=1)
    benchmark_sharpe: FiniteFloat | None = None
    data_provenance: str | None = Field(default=None, min_length=1)
    data_fingerprint: str | None = Field(default=None, min_length=1)
    warnings: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    diagnostics: tuple[DiagnosticResult, ...] = ()
    metadata: dict[str, JsonValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def confidence_interval_is_ordered(self) -> Self:
        """Reject intervals whose lower bound exceeds their upper bound."""
        if (
            self.confidence_interval is not None
            and self.confidence_interval[0] > self.confidence_interval[1]
        ):
            raise ValueError("confidence interval lower bound exceeds upper bound")
        if self.periods_per_year == 0.0:
            raise ValueError("periods per year must be positive when supplied")
        if any(not warning.strip() for warning in self.warnings):
            raise ValueError("warnings must not be blank")
        if any(not assumption.strip() for assumption in self.assumptions):
            raise ValueError("assumptions must not be blank")
        return self
