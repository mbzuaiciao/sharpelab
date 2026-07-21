"""IID Gaussian excess-return generator."""

from __future__ import annotations

from typing import Any

import numpy as np

from sharpelab.benchmark.schemas import ProcessFamily, SimulationResult
from sharpelab.simulation.common import build_result, finite_float, positive_float


def simulate_iid_gaussian(
    *, sample_size: int, seed: int, parameters: dict[str, Any]
) -> SimulationResult:
    """Generate ``r_t = mean + volatility * epsilon_t``."""
    mean = finite_float(parameters.get("mean", 0.0), "mean")
    volatility = positive_float(parameters.get("volatility", 0.1), "volatility")
    generator = np.random.default_rng(seed)
    values = generator.normal(mean, volatility, sample_size)
    return build_result(
        values=values,
        family=ProcessFamily.IID_GAUSSIAN,
        version="1.0",
        sample_size=sample_size,
        seed=seed,
        parameters={"mean": mean, "volatility": volatility},
        truth={
            "target_scale": "unannualized-per-period",
            "analytical_variance": volatility**2,
            "linear_dependence": False,
            "squared_return_dependence": False,
            "gaussian_innovations": True,
            "structural_instability": False,
        },
        target_defined=True,
        true_mean=mean,
        true_standard_deviation=volatility,
        true_sharpe=mean / volatility,
    )
