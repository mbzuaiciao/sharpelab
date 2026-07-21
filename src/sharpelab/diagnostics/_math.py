"""Small deterministic probability helpers used by diagnostics."""

from math import exp, isfinite, lgamma, log


def chi_square_survival(statistic: float, degrees_of_freedom: int) -> float:
    """Return the chi-square survival probability without SciPy."""
    if not isfinite(statistic) or statistic < 0.0:
        raise ValueError("chi-square statistic must be finite and nonnegative")
    if degrees_of_freedom < 1:
        raise ValueError("degrees_of_freedom must be positive")
    return _regularized_gamma_q(0.5 * degrees_of_freedom, 0.5 * statistic)


def _regularized_gamma_q(shape: float, value: float) -> float:
    if value == 0.0:
        return 1.0
    # Numerical convergence safeguards only; these do not classify evidence.
    limit, tolerance, tiny = 200, 1.0e-14, 1.0e-300
    log_scale = -value + shape * log(value) - lgamma(shape)
    if value < shape + 1.0:
        term = total = 1.0 / shape
        shifted = shape
        for _ in range(limit):
            shifted += 1.0
            term *= value / shifted
            total += term
            if abs(term) <= abs(total) * tolerance:
                return min(1.0, max(0.0, 1.0 - total * exp(log_scale)))
        raise ArithmeticError("incomplete-gamma series did not converge")
    shifted = value + 1.0 - shape
    denominator = 1.0 / max(shifted, tiny)
    numerator = 1.0 / tiny
    result = denominator
    for iteration in range(1, limit + 1):
        coefficient = -iteration * (iteration - shape)
        shifted += 2.0
        denominator = coefficient * denominator + shifted
        denominator = tiny if abs(denominator) < tiny else denominator
        numerator = shifted + coefficient / numerator
        numerator = tiny if abs(numerator) < tiny else numerator
        denominator = 1.0 / denominator
        delta = denominator * numerator
        result *= delta
        if abs(delta - 1.0) <= tolerance:
            return min(1.0, max(0.0, exp(log_scale) * result))
    raise ArithmeticError("incomplete-gamma continued fraction did not converge")
