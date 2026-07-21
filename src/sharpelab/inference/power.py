"""IID Gaussian asymptotic power for a one-sided Sharpe test."""

from math import isfinite, sqrt

from sharpelab.data.frequency import validate_periods_per_year
from sharpelab.inference.common import PowerResult, normal_cdf, normal_quantile


def _open_probability(value: float, name: str) -> float:
    result = float(value)
    if not isfinite(result) or not 0.0 < result < 1.0:
        raise ValueError(f"{name} must be finite and in (0, 1)")
    return result


def gaussian_sharpe_power(
    *,
    sample_size: int,
    true_sharpe: float,
    benchmark: float,
    significance_level: float = 0.05,
    periods_per_year: float | None = None,
) -> PowerResult:
    """Approximate power for ``H0: S <= benchmark`` versus ``H1: S > benchmark``.

    The null rejection threshold uses the standard error at ``benchmark``;
    power is evaluated under the distribution at ``true_sharpe``.
    """
    if sample_size < 2:
        raise ValueError("sample_size must be at least two")
    true_value = float(true_sharpe)
    benchmark_value = float(benchmark)
    if not all(isfinite(value) for value in (true_value, benchmark_value)):
        raise ValueError("true_sharpe and benchmark must be finite")
    alpha = _open_probability(significance_level, "significance_level")
    null_standard_error = sqrt(
        (1.0 + 0.5 * benchmark_value**2) / sample_size
    )
    alternative_standard_error = sqrt(
        (1.0 + 0.5 * true_value**2) / sample_size
    )
    critical_value = normal_quantile(1.0 - alpha)
    rejection_threshold = benchmark_value + critical_value * null_standard_error
    power = normal_cdf(
        (true_value - rejection_threshold) / alternative_standard_error
    )
    if not isfinite(power) or not 0.0 <= power <= 1.0:
        raise ArithmeticError("power is outside [0, 1]")
    frequency = (
        validate_periods_per_year(periods_per_year)
        if periods_per_year is not None
        else None
    )
    return PowerResult(
        sample_size=sample_size,
        power=power,
        true_sharpe=true_value,
        benchmark=benchmark_value,
        significance_level=alpha,
        null_standard_error=null_standard_error,
        alternative_standard_error=alternative_standard_error,
        rejection_threshold=rejection_threshold,
        periods_per_year=frequency,
        sample_length_years=(sample_size / frequency if frequency else None),
    )


def minimum_sample_length(
    *,
    true_sharpe: float,
    benchmark: float,
    significance_level: float = 0.05,
    target_power: float = 0.8,
    periods_per_year: float | None = None,
    maximum_sample_size: int = 10_000_000,
) -> PowerResult:
    """Numerically find the smallest integer sample size reaching target power."""
    target = _open_probability(target_power, "target_power")
    true_value = float(true_sharpe)
    benchmark_value = float(benchmark)
    if not all(isfinite(value) for value in (true_value, benchmark_value)):
        raise ValueError("true_sharpe and benchmark must be finite")
    if true_value <= benchmark_value:
        raise ValueError("true_sharpe must exceed benchmark for one-sided power")
    if maximum_sample_size < 2:
        raise ValueError("maximum_sample_size must be at least two")

    def power_at(sample_size: int) -> float:
        return gaussian_sharpe_power(
            sample_size=sample_size,
            true_sharpe=true_value,
            benchmark=benchmark_value,
            significance_level=significance_level,
        ).power

    low = 2
    high = 2
    while high < maximum_sample_size and power_at(high) < target:
        low = high + 1
        high = min(maximum_sample_size, high * 2)
    if power_at(high) < target:
        raise ValueError("target power is not reached within maximum_sample_size")
    while low < high:
        midpoint = (low + high) // 2
        if power_at(midpoint) >= target:
            high = midpoint
        else:
            low = midpoint + 1
    result = gaussian_sharpe_power(
        sample_size=low,
        true_sharpe=true_value,
        benchmark=benchmark_value,
        significance_level=significance_level,
        periods_per_year=periods_per_year,
    )
    return PowerResult(
        sample_size=result.sample_size,
        power=result.power,
        true_sharpe=result.true_sharpe,
        benchmark=result.benchmark,
        significance_level=result.significance_level,
        null_standard_error=result.null_standard_error,
        alternative_standard_error=result.alternative_standard_error,
        rejection_threshold=result.rejection_threshold,
        target_power=target,
        periods_per_year=result.periods_per_year,
        sample_length_years=result.sample_length_years,
    )
