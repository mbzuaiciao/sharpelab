"""Typed contracts and shared validation for benchmark simulations."""

from __future__ import annotations

from math import isfinite
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pydantic import JsonValue

from sharpelab.benchmark.schemas import ProcessFamily, SimulationResult


def finite_float(value: Any, name: str) -> float:
    """Return a finite float or reject the parameter."""
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def positive_float(value: Any, name: str) -> float:
    result = finite_float(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive")
    return result


def positive_int(value: Any, name: str, *, minimum: int = 1) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    result = int(value)
    if result != value or result < minimum:
        raise ValueError(f"{name} must be an integer at least {minimum}")
    return result


def build_result(
    *,
    values: NDArray[np.float64],
    family: ProcessFamily,
    version: str,
    sample_size: int,
    seed: int,
    parameters: dict[str, JsonValue],
    truth: dict[str, JsonValue],
    target_defined: bool,
    true_mean: float | None,
    true_standard_deviation: float | None,
    true_sharpe: float | None,
    descriptive_full_sample_sharpe: float | None = None,
    caveats: tuple[str, ...] = (),
) -> SimulationResult:
    """Validate finite generated values and build an immutable result."""
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (sample_size,) or not bool(np.all(np.isfinite(array))):
        raise ArithmeticError("simulation must produce finite values of sample_size")
    return SimulationResult(
        returns=tuple(float(value) for value in array),
        true_mean=true_mean,
        true_standard_deviation=true_standard_deviation,
        true_sharpe=true_sharpe,
        descriptive_full_sample_sharpe=descriptive_full_sample_sharpe,
        target_defined=target_defined,
        sample_size=sample_size,
        seed=seed,
        process_family=family,
        process_version=version,
        parameters=parameters,
        inference_truth=truth,
        caveats=caveats,
    )
