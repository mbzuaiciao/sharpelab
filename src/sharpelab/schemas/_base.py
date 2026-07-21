"""Shared schema configuration and scalar constraints."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat

NonNegativeFloat = Annotated[FiniteFloat, Field(ge=0.0)]
PValue = Annotated[
    FiniteFloat,
    Field(ge=0.0, le=1.0, description="Frequentist tail probability"),
]
ConfidenceLevel = Annotated[
    FiniteFloat,
    Field(gt=0.0, lt=1.0, description="Confidence interval coverage level"),
]
PosteriorProbability = Annotated[
    FiniteFloat,
    Field(ge=0.0, le=1.0, description="Bayesian posterior probability"),
]
CalibrationScore = Annotated[
    FiniteFloat,
    Field(ge=0.0, le=1.0, description="Model calibration score"),
]


class SchemaModel(BaseModel):
    """Strict base model used by all public ERI schemas."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )
