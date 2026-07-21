"""Diagnostic result contracts."""

from pydantic import Field, FiniteFloat

from sharpelab.schemas._base import CalibrationScore, PValue, SchemaModel


class DiagnosticResult(SchemaModel):
    """The outcome of one named eligibility or model diagnostic."""

    diagnostic_id: str = Field(min_length=1)
    passed: bool
    statistic: FiniteFloat | None = None
    p_value: PValue | None = None
    calibration_score: CalibrationScore | None = None
    threshold: FiniteFloat | None = None
    message: str | None = Field(default=None, min_length=1)
