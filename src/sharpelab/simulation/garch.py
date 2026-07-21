"""Stationary Gaussian-innovation GARCH(1,1)-style generator."""

from __future__ import annotations

from math import sqrt
from typing import Any

import numpy as np

from sharpelab.benchmark.schemas import ProcessFamily, SimulationResult
from sharpelab.simulation.common import (
    build_result,
    finite_float,
    positive_float,
    positive_int,
)


def simulate_garch(
    *, sample_size: int, seed: int, parameters: dict[str, Any]
) -> SimulationResult:
    """Generate a positive stationary GARCH(1,1) process."""
    mean = finite_float(parameters.get("mean", 0.0), "mean")
    omega = positive_float(parameters.get("omega", 0.0002), "omega")
    alpha = finite_float(parameters.get("alpha", 0.1), "alpha")
    beta = finite_float(parameters.get("beta", 0.8), "beta")
    if alpha < 0.0 or beta < 0.0:
        raise ValueError("GARCH alpha and beta must be nonnegative")
    if alpha + beta >= 1.0:
        raise ValueError("GARCH stationarity requires alpha + beta < 1")
    burn_in = positive_int(parameters.get("burn_in", 300), "burn_in", minimum=0)
    unconditional_variance = omega / (1.0 - alpha - beta)
    fourth_moment_coefficient = 3.0 * alpha**2 + 2.0 * alpha * beta + beta**2
    finite_fourth_moment = fourth_moment_coefficient < 1.0
    generator = np.random.default_rng(seed)
    conditional_variance = unconditional_variance
    residual = 0.0
    values = np.empty(sample_size, dtype=np.float64)
    for index in range(burn_in + sample_size):
        conditional_variance = omega + alpha * residual**2 + beta * conditional_variance
        if conditional_variance <= 0.0:
            raise ArithmeticError("GARCH conditional variance became nonpositive")
        residual = sqrt(conditional_variance) * generator.normal()
        if index >= burn_in:
            values[index - burn_in] = mean + residual
    unconditional_std = sqrt(unconditional_variance)
    return build_result(
        values=values,
        family=ProcessFamily.GARCH,
        version="1.0",
        sample_size=sample_size,
        seed=seed,
        parameters={
            "mean": mean,
            "omega": omega,
            "alpha": alpha,
            "beta": beta,
            "burn_in": burn_in,
            "innovation_distribution": "standard-normal",
            "initial_conditional_variance": unconditional_variance,
            "unconditional_variance": unconditional_variance,
            "fourth_moment_coefficient": fourth_moment_coefficient,
        },
        truth={
            "target_scale": "unannualized-per-period",
            "linear_dependence": False,
            "squared_return_dependence": alpha > 0.0,
            "finite_fourth_moment": finite_fourth_moment,
            "gaussian_innovations": True,
            "structural_instability": False,
        },
        target_defined=True,
        true_mean=mean,
        true_standard_deviation=unconditional_std,
        true_sharpe=mean / unconditional_std,
        caveats=(
            "Gaussian innovations do not make conditionally heteroskedastic "
            "returns IID.",
            "HAC and block-bootstrap eligibility requires the registered "
            "finite-fourth-moment condition.",
        ),
    )
