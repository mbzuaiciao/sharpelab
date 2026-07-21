"""Mertens non-Gaussian Sharpe variance and Probabilistic Sharpe Ratio.

Kurtosis is raw Pearson kurtosis, so a Gaussian population has kurtosis three.
PSR is a frequentist normal-approximation probability, not a Bayesian posterior.
"""

from math import isfinite, sqrt

from sharpelab.data.returns import ReturnInput, validate_returns
from sharpelab.diagnostics.summary import summarize_returns
from sharpelab.inference.common import PSRResult, normal_cdf
from sharpelab.inference.sharpe import sample_sharpe


def mertens_sharpe_variance(
    sharpe: float,
    sample_size: int,
    *,
    skewness: float,
    raw_kurtosis: float,
) -> float:
    """Return IID non-Gaussian asymptotic variance of sample Sharpe.

    ``Var(S_hat) = [1 - skewness*S + (raw_kurtosis - 1)*S^2/4] / n``.
    """
    values = (float(sharpe), float(skewness), float(raw_kurtosis))
    if not all(isfinite(value) for value in values):
        raise ValueError("Sharpe, skewness, and raw kurtosis must be finite")
    if sample_size < 2:
        raise ValueError("sample_size must be at least two")
    if raw_kurtosis < 1.0:
        raise ValueError("raw_kurtosis must be at least one")
    numerator = (
        1.0
        - skewness * sharpe
        + 0.25 * (raw_kurtosis - 1.0) * sharpe**2
    )
    variance = numerator / sample_size
    if not isfinite(variance) or variance <= 0.0:
        raise ValueError("Mertens variance must be positive and finite")
    return variance


def probabilistic_sharpe_ratio(
    returns: ReturnInput,
    *,
    benchmark: float,
) -> PSRResult:
    """Estimate the frequentist probability Sharpe exceeds ``benchmark``."""
    benchmark_value = float(benchmark)
    if not isfinite(benchmark_value):
        raise ValueError("benchmark must be finite")
    values = validate_returns(returns, minimum_size=2)
    summary = summarize_returns(values)
    estimate = sample_sharpe(values)
    variance = mertens_sharpe_variance(
        estimate,
        summary.sample_size,
        skewness=summary.skewness,
        raw_kurtosis=summary.raw_kurtosis,
    )
    standard_error = sqrt(variance)
    probability = normal_cdf((estimate - benchmark_value) / standard_error)
    if not isfinite(probability) or not 0.0 <= probability <= 1.0:
        raise ArithmeticError("probabilistic Sharpe ratio is outside [0, 1]")
    return PSRResult(
        sample_sharpe=estimate,
        benchmark=benchmark_value,
        probabilistic_sharpe_ratio=probability,
        estimated_variance=variance,
        standard_error=standard_error,
        skewness=summary.skewness,
        raw_kurtosis=summary.raw_kurtosis,
        sample_size=summary.sample_size,
        warnings=(
            "Moment estimates are uncorrected plug-ins and may be unstable in "
            "small samples.",
        ),
    )
