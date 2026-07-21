"""Explicit sampling-frequency helpers."""

from math import isfinite


def validate_periods_per_year(periods_per_year: float) -> float:
    """Validate an explicit positive, finite annualization frequency.

    Frequency is never inferred from the number of return observations.
    Fractional values are accepted for nonstandard sampling conventions.
    """
    value = float(periods_per_year)
    if not isfinite(value) or value <= 0.0:
        raise ValueError("periods_per_year must be positive and finite")
    return value
