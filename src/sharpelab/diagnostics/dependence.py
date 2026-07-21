"""Distinct linear-return and squared-return dependence diagnostics."""

from collections.abc import Callable

import numpy as np
from numpy.typing import NDArray

from sharpelab.config import DependenceConfig
from sharpelab.data.returns import ReturnInput, validate_returns
from sharpelab.diagnostics._math import chi_square_survival
from sharpelab.diagnostics.evidence_factory import fingerprint_returns, make_evidence
from sharpelab.schemas.evidence import EvidenceFinding, EvidenceItem


def sample_autocorrelation(values: NDArray[np.float64], lag: int) -> float:
    if lag < 1 or lag >= values.size:
        raise ValueError("lag must be between one and sample_size - 1")
    centered = values - np.mean(values)
    denominator = float(np.dot(centered, centered))
    if denominator <= np.finfo(float).eps:
        raise ValueError("autocorrelation input has degenerate variance")
    return float(np.dot(centered[lag:], centered[:-lag]) / denominator)


def diagnose_linear_dependence(
    returns: ReturnInput, config: DependenceConfig
) -> EvidenceItem:
    return _diagnose(
        returns,
        config,
        claim="linear_independence",
        name="linear-dependence",
        transform=lambda values: values,
        caveat="Failure to detect linear dependence does not prove independence.",
    )


def diagnose_squared_dependence(
    returns: ReturnInput, config: DependenceConfig
) -> EvidenceItem:
    return _diagnose(
        returns,
        config,
        claim="absence_of_squared_return_dependence",
        name="squared-return-dependence",
        transform=lambda values: (values - np.mean(values)) ** 2,
        caveat=(
            "This identifies volatility-clustering evidence, not a specific "
            "volatility model."
        ),
    )


def _diagnose(
    returns: ReturnInput,
    config: DependenceConfig,
    *,
    claim: str,
    name: str,
    transform: Callable[[NDArray[np.float64]], NDArray[np.float64]],
    caveat: str,
) -> EvidenceItem:
    values = validate_returns(returns, minimum_size=2)
    fingerprint = fingerprint_returns(values)
    maximum_lag = max(config.lags)
    sample_insufficient = values.size < config.minimum_sample_size
    lag_too_large = maximum_lag >= values.size
    if sample_insufficient or lag_too_large:
        warnings = (
            *(
                ("Sample is insufficient for the configured dependence diagnostic.",)
                if sample_insufficient
                else ()
            ),
            *(
                (
                    "The maximum configured Ljung-Box lag must be below sample size.",
                )
                if lag_too_large
                else ()
            ),
        )
        return make_evidence(
            claim=claim,
            finding=EvidenceFinding.INCONCLUSIVE,
            diagnostic_name=name,
            sample_size=int(values.size),
            configuration={
                "configured_lags": list(config.lags),
                "minimum_sample_size": config.minimum_sample_size,
            },
            warnings=warnings,
            does_not_establish=(caveat,),
            data_fingerprint=fingerprint,
        )
    transformed = np.asarray(transform(values), dtype=np.float64)
    ljung_box_lags = tuple(range(1, maximum_lag + 1))
    try:
        correlations = tuple(
            sample_autocorrelation(transformed, lag) for lag in ljung_box_lags
        )
    except ValueError:
        return make_evidence(
            claim=claim,
            finding=EvidenceFinding.INCONCLUSIVE,
            diagnostic_name=name,
            sample_size=int(values.size),
            configuration={"configured_lags": list(config.lags)},
            warnings=("Transformed series has degenerate variance.",),
            does_not_establish=(caveat,),
            data_fingerprint=fingerprint,
        )
    n = int(values.size)
    statistic = float(
        n
        * (n + 2)
        * sum(
            rho**2 / (n - lag)
            for rho, lag in zip(correlations, ljung_box_lags, strict=True)
        )
    )
    p_value = chi_square_survival(statistic, maximum_lag)
    practical = (
        max(abs(value) for value in correlations) >= config.practical_autocorrelation
    )
    detected = p_value < config.significance_level or practical
    return make_evidence(
        claim=claim,
        finding=EvidenceFinding.CONTRADICTS
        if detected
        else EvidenceFinding.INCONCLUSIVE,
        diagnostic_name=name,
        sample_size=n,
        statistic=statistic,
        p_value=p_value,
        structured_output={
            "configured_lags": list(config.lags),
            "ljung_box_lags": list(ljung_box_lags),
            "autocorrelations": list(correlations),
            "max_absolute_autocorrelation": max(abs(value) for value in correlations),
            "degrees_of_freedom": maximum_lag,
            "dependence_detected": detected,
        },
        configuration={
            "maximum_ljung_box_lag": maximum_lag,
            "significance_level": config.significance_level,
            "practical_autocorrelation": config.practical_autocorrelation,
        },
        assumptions=(
            "The Ljung-Box reference uses chi-square degrees of freedom equal "
            "to the maximum lag; no model parameters are estimated.",
        ),
        warnings=("The Ljung-Box chi-square reference is asymptotic.",),
        methods_ruled_out=("iid-gaussian-sharpe", "mertens-psr") if detected else (),
        methods_enabled=("hac-sharpe", "circular-block-bootstrap") if detected else (),
        does_not_establish=(caveat,),
        data_fingerprint=fingerprint,
    )
