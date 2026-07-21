"""Bartlett/Newey-West HAC inference for the sample Sharpe ratio."""

from math import isfinite, sqrt

import numpy as np
from numpy.typing import NDArray

from sharpelab.data.returns import ReturnInput, validate_returns
from sharpelab.inference.common import HACResult
from sharpelab.inference.sharpe import sample_sharpe


def influence_function_series(returns: ReturnInput) -> NDArray[np.float64]:
    """Estimate the Sharpe influence function for each observation.

    The series includes variation in both returns and squared returns:
    ``IF_t = e_t/sigma - S*(e_t^2 - sigma^2)/(2*sigma^2)``.
    Population-moment denominators are used inside this asymptotic influence
    calculation; the reported sample Sharpe still uses ``ddof=1``.
    """
    values = validate_returns(returns, minimum_size=2)
    mean = float(np.mean(values))
    centered = values - mean
    variance = float(np.mean(centered**2))
    if not isfinite(variance) or variance <= np.finfo(float).eps:
        raise ValueError("returns have zero or numerically degenerate variance")
    sigma = sqrt(variance)
    functional_sharpe = mean / sigma
    influence = centered / sigma - (
        functional_sharpe * (centered**2 - variance) / (2.0 * variance)
    )
    influence = np.asarray(influence - np.mean(influence), dtype=np.float64)
    if not bool(np.all(np.isfinite(influence))):
        raise ArithmeticError("Sharpe influence function contains non-finite values")
    return influence


def bartlett_long_run_variance(
    influence_values: ReturnInput,
    *,
    bandwidth: int,
) -> float:
    """Estimate long-run variance with lag covariances divided by ``n``."""
    values = validate_returns(influence_values, minimum_size=2)
    sample_size = int(values.size)
    if bandwidth < 0 or bandwidth >= sample_size:
        raise ValueError("bandwidth must be between zero and sample_size - 1")
    centered = values - np.mean(values)
    lag_zero_variance = float(np.dot(centered, centered) / sample_size)
    long_run_variance = lag_zero_variance
    for lag in range(1, bandwidth + 1):
        weight = 1.0 - lag / (bandwidth + 1.0)
        autocovariance = float(
            np.dot(centered[lag:], centered[:-lag]) / sample_size
        )
        long_run_variance += 2.0 * weight * autocovariance
    tolerance = np.finfo(float).eps * max(1.0, lag_zero_variance) * 100.0
    if long_run_variance < -tolerance:
        raise ValueError("HAC long-run variance is materially negative")
    if not isfinite(long_run_variance) or long_run_variance <= 0.0:
        raise ValueError("HAC long-run variance must be positive and finite")
    return long_run_variance


def hac_sharpe_standard_error(
    returns: ReturnInput,
    *,
    bandwidth: int,
) -> HACResult:
    """Estimate weak-dependence-robust asymptotic Sharpe uncertainty."""
    values = validate_returns(returns, minimum_size=2)
    influence = influence_function_series(values)
    long_run_variance = bartlett_long_run_variance(
        influence, bandwidth=bandwidth
    )
    standard_error = sqrt(long_run_variance / values.size)
    if not isfinite(standard_error) or standard_error <= 0.0:
        raise ArithmeticError("HAC standard error is not positive and finite")
    return HACResult(
        estimate=sample_sharpe(values),
        standard_error=standard_error,
        long_run_variance=long_run_variance,
        bandwidth=bandwidth,
        sample_size=int(values.size),
        influence_values=tuple(float(value) for value in influence),
    )
