"""Descriptive summary statistics for validated returns."""

from dataclasses import dataclass

import numpy as np

from sharpelab.data.returns import ReturnInput, validate_returns


@dataclass(frozen=True, slots=True)
class ReturnSummary:
    """Finite sample summary using raw (not excess) kurtosis."""

    sample_size: int
    mean: float
    standard_deviation: float
    minimum: float
    maximum: float
    skewness: float
    raw_kurtosis: float
    standard_deviation_ddof: int = 1


def summarize_returns(returns: ReturnInput) -> ReturnSummary:
    """Summarize finite nondegenerate returns.

    Skewness and raw kurtosis are uncorrected plug-in central moments with
    denominator ``n``, normalized by the population-form second moment. A
    Gaussian population therefore has raw kurtosis three.
    """
    values = validate_returns(returns, minimum_size=2)
    mean = float(np.mean(values))
    centered = values - mean
    second_moment = float(np.mean(centered**2))
    if not np.isfinite(second_moment) or second_moment <= np.finfo(float).eps:
        raise ValueError("returns have zero or numerically degenerate variance")
    skewness = float(np.mean(centered**3) / second_moment**1.5)
    raw_kurtosis = float(np.mean(centered**4) / second_moment**2)
    outputs = (mean, skewness, raw_kurtosis)
    if not all(np.isfinite(value) for value in outputs):
        raise ArithmeticError("return summary contains a non-finite value")
    return ReturnSummary(
        sample_size=int(values.size),
        mean=mean,
        standard_deviation=float(np.std(values, ddof=1)),
        minimum=float(np.min(values)),
        maximum=float(np.max(values)),
        skewness=skewness,
        raw_kurtosis=raw_kurtosis,
    )
