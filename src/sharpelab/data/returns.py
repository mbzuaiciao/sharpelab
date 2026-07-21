"""Validation for one-dimensional return series."""

import numpy as np
from numpy.typing import ArrayLike, NDArray

FloatArray = NDArray[np.float64]
ReturnInput = ArrayLike


def validate_returns(
    returns: ReturnInput,
    *,
    minimum_size: int = 2,
) -> FloatArray:
    """Return a finite one-dimensional copy with enough observations.

    Values are interpreted as excess returns unless a caller explicitly
    documents another convention. Variance validation is performed by the
    statistic that requires it, rather than by this shape/finite-value helper.
    """
    if minimum_size < 1:
        raise ValueError("minimum_size must be at least one")
    values = np.asarray(returns, dtype=np.float64)
    if values.ndim != 1:
        raise ValueError("returns must be one-dimensional")
    if values.size < minimum_size:
        raise ValueError(f"at least {minimum_size} return observations are required")
    if not bool(np.all(np.isfinite(values))):
        raise ValueError("returns must contain only finite values")
    return values.copy()
