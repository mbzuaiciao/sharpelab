"""Stationary Gaussian AR(1) excess-return generator."""

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


def simulate_ar1(
    *, sample_size: int, seed: int, parameters: dict[str, Any]
) -> SimulationResult:
    """Generate a stationary AR(1) with documented innovation variance."""
    mean = finite_float(parameters.get("mean", 0.0), "mean")
    phi = finite_float(parameters.get("phi", 0.3), "phi")
    if abs(phi) >= 1.0:
        raise ValueError("AR(1) phi must satisfy abs(phi) < 1")
    innovation_std = positive_float(
        parameters.get("innovation_std", 0.1), "innovation_std"
    )
    burn_in = positive_int(parameters.get("burn_in", 200), "burn_in", minimum=0)
    unconditional_variance = innovation_std**2 / (1.0 - phi**2)
    generator = np.random.default_rng(seed)
    centered = generator.normal(0.0, sqrt(unconditional_variance))
    values = np.empty(sample_size, dtype=np.float64)
    for index in range(burn_in + sample_size):
        centered = phi * centered + generator.normal(0.0, innovation_std)
        if index >= burn_in:
            values[index - burn_in] = mean + centered
    unconditional_std = sqrt(unconditional_variance)
    return build_result(
        values=values,
        family=ProcessFamily.AR1,
        version="1.0",
        sample_size=sample_size,
        seed=seed,
        parameters={
            "mean": mean,
            "phi": phi,
            "innovation_std": innovation_std,
            "innovation_variance": innovation_std**2,
            "burn_in": burn_in,
            "unconditional_variance": unconditional_variance,
        },
        truth={
            "target_scale": "unannualized-per-period",
            "linear_dependence": abs(phi) > 0.05,
            "squared_return_dependence": abs(phi) > 0.05,
            "gaussian_innovations": True,
            "structural_instability": False,
        },
        target_defined=True,
        true_mean=mean,
        true_standard_deviation=unconditional_std,
        true_sharpe=mean / unconditional_std,
        caveats=("IID-only inference is not primary-valid under material phi.",),
    )
