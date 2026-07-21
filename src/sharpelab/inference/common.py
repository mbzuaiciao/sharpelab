"""Small immutable result objects shared by inference methods."""

from dataclasses import dataclass
from math import erfc, sqrt
from statistics import NormalDist
from typing import Literal

Alternative = Literal["greater", "less", "two-sided"]

_STANDARD_NORMAL = NormalDist()


def normal_cdf(value: float) -> float:
    """Numerically stable standard normal cumulative probability."""
    return 0.5 * erfc(-value / sqrt(2.0))


def normal_survival(value: float) -> float:
    """Numerically stable standard normal upper-tail probability."""
    return 0.5 * erfc(value / sqrt(2.0))


def normal_quantile(probability: float) -> float:
    """Standard normal quantile for an already validated probability."""
    return _STANDARD_NORMAL.inv_cdf(probability)


@dataclass(frozen=True, slots=True)
class SharpeEstimate:
    """A sample Sharpe estimate and its annualization convention."""

    value: float
    sample_size: int
    method: str = "sample-sharpe"
    method_version: str = "1.0"
    annualized: bool = False
    periods_per_year: float | None = None
    annualization_convention: str = "none"
    warnings: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ("Input values are excess returns.",)


@dataclass(frozen=True, slots=True)
class StandardErrorResult:
    """An asymptotic standard error with identifying metadata."""

    estimate: float
    standard_error: float
    sample_size: int
    method: str
    method_version: str = "1.0"
    annualization_convention: str = "none; unannualized per-period Sharpe"
    benchmark: float | None = None
    warnings: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConfidenceIntervalResult:
    """A normal-approximation or resampling confidence interval."""

    estimate: float
    lower: float
    upper: float
    confidence_level: float
    sample_size: int
    method: str
    method_version: str = "1.0"
    annualization_convention: str = "none; unannualized per-period Sharpe"
    standard_error: float | None = None
    warnings: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class HypothesisTestResult:
    """A frequentist Sharpe test against a supplied benchmark."""

    estimate: float
    benchmark: float
    standard_error: float
    statistic: float
    p_value: float
    alternative: Alternative
    sample_size: int
    method: str
    method_version: str = "1.0"
    annualization_convention: str = "none; unannualized per-period Sharpe"
    warnings: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PSRResult:
    """Frequentist Probabilistic Sharpe Ratio output."""

    sample_sharpe: float
    benchmark: float
    probabilistic_sharpe_ratio: float
    estimated_variance: float
    standard_error: float
    skewness: float
    raw_kurtosis: float
    sample_size: int
    method: str = "mertens-psr"
    method_version: str = "1.0"
    annualization_convention: str = "none; unannualized per-period Sharpe"
    warnings: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = (
        "PSR is a frequentist normal-approximation probability, not a posterior.",
        "Observations are IID with finite fourth moment.",
    )


@dataclass(frozen=True, slots=True)
class HACResult:
    """Dependence-robust Sharpe uncertainty from a Bartlett HAC estimator."""

    estimate: float
    standard_error: float
    long_run_variance: float
    bandwidth: int
    sample_size: int
    influence_values: tuple[float, ...]
    method: str = "hac-bartlett-sharpe"
    method_version: str = "1.0"
    annualization_convention: str = "none; unannualized per-period Sharpe"
    kernel: str = "Bartlett/Newey-West"
    warnings: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = (
        "The return process is weakly dependent and sufficiently stationary.",
        "The result is asymptotic, not an exact finite-sample solution.",
    )


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    """A reproducible circular-block percentile interval."""

    estimate: float
    lower: float
    upper: float
    confidence_level: float
    block_length: int
    replications: int
    seed: int
    sample_size: int
    draws: tuple[float, ...] | None
    method: str = "circular-block-bootstrap-sharpe"
    method_version: str = "1.0"
    annualization_convention: str = "none; unannualized per-period Sharpe"
    quantile_method: str = "linear"
    warnings: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = (
        "Blocks approximate dependence in a sufficiently stationary series.",
        "The percentile interval is not universally valid under nonstationarity.",
    )


@dataclass(frozen=True, slots=True)
class PowerResult:
    """Gaussian asymptotic one-sided Sharpe-test power."""

    sample_size: int
    power: float
    true_sharpe: float
    benchmark: float
    significance_level: float
    null_standard_error: float
    alternative_standard_error: float
    rejection_threshold: float
    target_power: float | None = None
    periods_per_year: float | None = None
    sample_length_years: float | None = None
    method: str = "iid-gaussian-sharpe-power"
    method_version: str = "1.0"
    annualization_convention: str = "none; unannualized per-period Sharpe"
    assumptions: tuple[str, ...] = (
        "The Sharpe estimator follows its IID Gaussian asymptotic law.",
        "The alternative is one-sided: Sharpe exceeds the benchmark.",
    )
