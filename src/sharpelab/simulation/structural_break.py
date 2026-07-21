"""Explicit two-segment mean or variance break generator."""

from __future__ import annotations

from math import sqrt
from typing import Any

import numpy as np

from sharpelab.benchmark.schemas import ProcessFamily, SimulationResult
from sharpelab.simulation.common import build_result, finite_float, positive_float


def simulate_structural_break(
    *, sample_size: int, seed: int, parameters: dict[str, Any]
) -> SimulationResult:
    """Generate a two-segment Gaussian break with no stable full-sample target."""
    variant = str(parameters.get("variant", "mean"))
    if variant not in {"mean", "variance"}:
        raise ValueError("structural break variant must be mean or variance")
    break_fraction = finite_float(
        parameters.get("break_fraction", 0.5), "break_fraction"
    )
    if not 0.1 < break_fraction < 0.9:
        raise ValueError("break_fraction must be in (0.1, 0.9)")
    mean_1 = finite_float(parameters.get("mean_1", 0.0), "mean_1")
    mean_2 = finite_float(parameters.get("mean_2", 0.0), "mean_2")
    volatility_1 = positive_float(parameters.get("volatility_1", 0.1), "volatility_1")
    volatility_2 = positive_float(parameters.get("volatility_2", 0.1), "volatility_2")
    if variant == "mean" and mean_1 == mean_2:
        raise ValueError("mean-break segments must have distinct means")
    if variant == "mean" and volatility_1 != volatility_2:
        raise ValueError("mean-break segments must have equal volatility")
    if variant == "variance" and volatility_1 == volatility_2:
        raise ValueError("variance-break segments must have distinct volatility")
    if variant == "variance" and mean_1 != mean_2:
        raise ValueError("variance-break segments must have equal means")
    break_index = int(sample_size * break_fraction)
    if break_index < 2 or sample_size - break_index < 2:
        raise ValueError("break must leave at least two observations per segment")
    generator = np.random.default_rng(seed)
    first = generator.normal(mean_1, volatility_1, break_index)
    second = generator.normal(mean_2, volatility_2, sample_size - break_index)
    values = np.concatenate((first, second))
    weight = break_index / sample_size
    mixture_mean = weight * mean_1 + (1.0 - weight) * mean_2
    mixture_variance = weight * (volatility_1**2 + (mean_1 - mixture_mean) ** 2) + (
        1.0 - weight
    ) * (volatility_2**2 + (mean_2 - mixture_mean) ** 2)
    descriptive_sharpe = mixture_mean / sqrt(mixture_variance)
    return build_result(
        values=np.asarray(values, dtype=np.float64),
        family=ProcessFamily.STRUCTURAL_BREAK,
        version="1.0",
        sample_size=sample_size,
        seed=seed,
        parameters={
            "variant": variant,
            "break_fraction": break_fraction,
            "break_index": break_index,
            "mean_1": mean_1,
            "mean_2": mean_2,
            "volatility_1": volatility_1,
            "volatility_2": volatility_2,
            "segment_sharpe_1": mean_1 / volatility_1,
            "segment_sharpe_2": mean_2 / volatility_2,
            "mixture_functional_definition": "weighted marginal mean / marginal sd",
        },
        truth={
            "target_scale": "unannualized-per-period",
            "linear_dependence": False,
            "squared_return_dependence": variant == "variance",
            "gaussian_innovations": True,
            "structural_instability": True,
        },
        target_defined=False,
        true_mean=None,
        true_standard_deviation=None,
        true_sharpe=None,
        descriptive_full_sample_sharpe=descriptive_sharpe,
        caveats=(
            "No single stable population Sharpe is defined for full-sample inference.",
            "The descriptive mixture functional is not treated as an "
            "inferential target.",
        ),
    )
