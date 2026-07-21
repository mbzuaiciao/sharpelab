"""Core sample Sharpe statistics.

Input values are treated as excess returns. The sample standard deviation uses
``ddof=1``. No frequency is inferred from the row count.
"""

from math import sqrt

import numpy as np

from sharpelab.data.frequency import validate_periods_per_year
from sharpelab.data.returns import ReturnInput, validate_returns
from sharpelab.inference.common import SharpeEstimate

_VARIANCE_TOLERANCE = np.finfo(np.float64).eps


def sample_mean(returns: ReturnInput) -> float:
    """Calculate the arithmetic sample mean of finite returns."""
    values = validate_returns(returns, minimum_size=1)
    result = float(np.mean(values))
    if not np.isfinite(result):
        raise ArithmeticError("sample mean is not finite")
    return result


def sample_standard_deviation(returns: ReturnInput) -> float:
    """Calculate sample standard deviation using Bessel correction (ddof=1)."""
    values = validate_returns(returns, minimum_size=2)
    result = float(np.std(values, ddof=1))
    if not np.isfinite(result) or result <= _VARIANCE_TOLERANCE:
        raise ValueError("returns have zero or numerically degenerate variance")
    return result


def sample_sharpe(returns: ReturnInput) -> float:
    """Calculate the unannualized sample mean divided by sample std. dev."""
    values = validate_returns(returns, minimum_size=2)
    result = float(np.mean(values)) / sample_standard_deviation(values)
    if not np.isfinite(result):
        raise ArithmeticError("sample Sharpe is not finite")
    return result


def annualized_sample_sharpe(
    returns: ReturnInput,
    *,
    periods_per_year: float,
) -> float:
    """Apply explicit square-root-of-time annualization to sample Sharpe.

    This naive transformation can be invalid under serial dependence. Calling
    this explicitly and supplying ``periods_per_year`` records the convention;
    the frequency is never guessed from the data.
    """
    frequency = validate_periods_per_year(periods_per_year)
    result = sample_sharpe(returns) * sqrt(frequency)
    if not np.isfinite(result):
        raise ArithmeticError("annualized sample Sharpe is not finite")
    return result


def estimate_sharpe(
    returns: ReturnInput,
    *,
    annualize: bool = False,
    periods_per_year: float | None = None,
) -> SharpeEstimate:
    """Return a metadata-rich sample Sharpe estimate."""
    values = validate_returns(returns, minimum_size=2)
    if annualize:
        if periods_per_year is None:
            raise ValueError("periods_per_year is required for annualization")
        frequency = validate_periods_per_year(periods_per_year)
        return SharpeEstimate(
            value=annualized_sample_sharpe(values, periods_per_year=frequency),
            sample_size=int(values.size),
            annualized=True,
            periods_per_year=frequency,
            annualization_convention="square-root-of-time",
            warnings=(
                "Square-root-of-time annualization may be invalid under serial "
                "dependence.",
            ),
        )
    if periods_per_year is not None:
        raise ValueError("periods_per_year must be omitted when annualize is false")
    return SharpeEstimate(value=sample_sharpe(values), sample_size=int(values.size))
