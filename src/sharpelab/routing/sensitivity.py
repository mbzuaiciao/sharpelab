"""Conclusion comparison across defensible inference methods."""

from math import isfinite

from pydantic import BaseModel, ConfigDict

from sharpelab.schemas.inference import InferenceResult


class ConclusionComparison(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    benchmark: float
    significance_level: float
    probability_threshold: float
    conclusions: dict[str, bool | None]
    disagreement: bool
    interpretation: str


def compare_conclusions(
    results: tuple[InferenceResult, ...], *, benchmark: float, significance_level: float
) -> ConclusionComparison:
    """Compare whether available results support exceeding a benchmark."""
    if not isfinite(benchmark):
        raise ValueError("benchmark must be finite")
    if not isfinite(significance_level) or not 0.0 < significance_level < 1.0:
        raise ValueError("significance_level must be in (0, 1)")
    probability_threshold = 1.0 - significance_level
    conclusions: dict[str, bool | None] = {}
    for result in results:
        if result.confidence_interval is not None:
            conclusions[result.method_id] = result.confidence_interval[0] > benchmark
        elif result.p_value is not None:
            conclusions[result.method_id] = (
                result.estimate > benchmark and result.p_value < significance_level
            )
        elif "frequentist_probability" in result.metadata:
            value = result.metadata["frequentist_probability"]
            conclusions[result.method_id] = (
                bool(value >= probability_threshold)
                if isinstance(value, (int, float))
                else None
            )
        else:
            conclusions[result.method_id] = None
    determinate = {value for value in conclusions.values() if value is not None}
    disagreement = len(determinate) > 1
    return ConclusionComparison(
        benchmark=benchmark,
        significance_level=significance_level,
        probability_threshold=probability_threshold,
        conclusions=conclusions,
        disagreement=disagreement,
        interpretation="Substantive conclusions disagree across valid methods."
        if disagreement
        else "No substantive disagreement was detected among comparable outputs.",
    )
