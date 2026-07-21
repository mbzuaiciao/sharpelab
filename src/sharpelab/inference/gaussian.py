"""IID Gaussian asymptotic inference for the unannualized sample Sharpe.

The approximation uses ``Var(S_hat) = (1 + S_hat**2 / 2) / n`` and can be
unreliable in small samples or under non-Gaussianity or serial dependence.
"""

from math import isfinite, sqrt

from sharpelab.data.returns import ReturnInput, validate_returns
from sharpelab.inference.common import (
    Alternative,
    ConfidenceIntervalResult,
    HypothesisTestResult,
    StandardErrorResult,
    normal_cdf,
    normal_quantile,
    normal_survival,
)
from sharpelab.inference.sharpe import sample_sharpe

_ASSUMPTIONS = (
    "Returns are IID Gaussian excess returns.",
    "Inference uses a first-order asymptotic normal approximation.",
)
_WARNINGS = ("The approximation may be inaccurate in small samples.",)


def _validate_probability(value: float, name: str, *, open_interval: bool) -> float:
    result = float(value)
    valid = 0.0 < result < 1.0 if open_interval else 0.0 <= result <= 1.0
    if not isfinite(result) or not valid:
        interval = "(0, 1)" if open_interval else "[0, 1]"
        raise ValueError(f"{name} must be finite and in {interval}")
    return result


def _validate_finite(value: float, name: str) -> float:
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def iid_gaussian_sharpe_variance(sharpe: float, sample_size: int) -> float:
    """Return IID Gaussian asymptotic variance of a sample Sharpe estimate."""
    estimate = _validate_finite(sharpe, "sharpe")
    if sample_size < 2:
        raise ValueError("sample_size must be at least two")
    variance = (1.0 + 0.5 * estimate**2) / sample_size
    if not isfinite(variance) or variance <= 0.0:
        raise ArithmeticError("Gaussian Sharpe variance is not positive and finite")
    return variance


def iid_gaussian_sharpe_standard_error(returns: ReturnInput) -> StandardErrorResult:
    """Estimate IID Gaussian asymptotic standard error for sample Sharpe."""
    values = validate_returns(returns, minimum_size=2)
    estimate = sample_sharpe(values)
    standard_error = sqrt(iid_gaussian_sharpe_variance(estimate, int(values.size)))
    return StandardErrorResult(
        estimate=estimate,
        standard_error=standard_error,
        sample_size=int(values.size),
        method="iid-gaussian-sharpe",
        warnings=_WARNINGS,
        assumptions=_ASSUMPTIONS,
    )


def gaussian_sharpe_confidence_interval(
    returns: ReturnInput,
    *,
    confidence_level: float = 0.95,
) -> ConfidenceIntervalResult:
    """Construct a two-sided normal-approximation Sharpe interval."""
    level = _validate_probability(
        confidence_level, "confidence_level", open_interval=True
    )
    standard_error = iid_gaussian_sharpe_standard_error(returns)
    critical_value = normal_quantile(0.5 + level / 2.0)
    lower = standard_error.estimate - critical_value * standard_error.standard_error
    upper = standard_error.estimate + critical_value * standard_error.standard_error
    if not all(isfinite(value) for value in (critical_value, lower, upper)):
        raise ArithmeticError("Gaussian confidence interval is not finite")
    return ConfidenceIntervalResult(
        estimate=standard_error.estimate,
        lower=lower,
        upper=upper,
        confidence_level=level,
        sample_size=standard_error.sample_size,
        standard_error=standard_error.standard_error,
        method="iid-gaussian-sharpe-normal-ci",
        warnings=_WARNINGS,
        assumptions=_ASSUMPTIONS,
    )


def gaussian_sharpe_test(
    returns: ReturnInput,
    *,
    benchmark: float,
    alternative: Alternative = "greater",
) -> HypothesisTestResult:
    """Test an unannualized Sharpe using variance under the null benchmark."""
    benchmark_value = _validate_finite(benchmark, "benchmark")
    if alternative not in ("greater", "less", "two-sided"):
        raise ValueError("alternative must be greater, less, or two-sided")
    values = validate_returns(returns, minimum_size=2)
    sample_size = int(values.size)
    estimate = sample_sharpe(values)
    null_standard_error = sqrt(
        iid_gaussian_sharpe_variance(benchmark_value, sample_size)
    )
    statistic = (estimate - benchmark_value) / null_standard_error
    if alternative == "greater":
        p_value = normal_survival(statistic)
    elif alternative == "less":
        p_value = normal_cdf(statistic)
    else:
        p_value = 2.0 * normal_survival(abs(statistic))
    if (
        not all(isfinite(value) for value in (statistic, p_value))
        or not 0.0 <= p_value <= 1.0
    ):
        raise ArithmeticError("Gaussian hypothesis test produced an invalid value")
    return HypothesisTestResult(
        estimate=estimate,
        benchmark=benchmark_value,
        standard_error=null_standard_error,
        statistic=statistic,
        p_value=p_value,
        alternative=alternative,
        sample_size=sample_size,
        method="iid-gaussian-sharpe-z-test",
        warnings=_WARNINGS,
        assumptions=(
            *_ASSUMPTIONS,
            "Test variance is evaluated at the null benchmark.",
        ),
    )
