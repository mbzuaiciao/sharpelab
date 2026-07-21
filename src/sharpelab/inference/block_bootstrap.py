"""Reproducible circular-block bootstrap for the sample Sharpe."""

from math import ceil, isfinite

import numpy as np
from numpy.typing import ArrayLike, NDArray

from sharpelab.data.returns import ReturnInput, validate_returns
from sharpelab.inference.common import BootstrapResult
from sharpelab.inference.sharpe import sample_sharpe


def circular_block_indices(
    *,
    sample_size: int,
    block_length: int,
    starts: ArrayLike,
) -> NDArray[np.int64]:
    """Build exactly ``sample_size`` circular indices from explicit starts."""
    if sample_size < 1:
        raise ValueError("sample_size must be positive")
    if block_length < 1 or block_length > sample_size:
        raise ValueError("block_length must be between one and sample size")
    start_values = np.asarray(starts, dtype=np.int64)
    if start_values.ndim != 1 or start_values.size < 1:
        raise ValueError("starts must be a nonempty one-dimensional sequence")
    if not bool(np.all((start_values >= 0) & (start_values < sample_size))):
        raise ValueError("block starts must be valid sample indices")
    blocks_required = ceil(sample_size / block_length)
    if start_values.size < blocks_required:
        raise ValueError("not enough block starts to construct a full sample")
    offsets = np.arange(block_length, dtype=np.int64)
    indices = (
        (start_values[:blocks_required, None] + offsets[None, :]) % sample_size
    ).ravel()[:sample_size]
    return np.asarray(indices, dtype=np.int64)


def circular_block_bootstrap(
    returns: ReturnInput,
    *,
    block_length: int,
    replications: int,
    seed: int,
    confidence_level: float = 0.95,
    retain_draws: bool = False,
) -> BootstrapResult:
    """Construct a circular-block percentile interval for sample Sharpe.

    Block length, replication count, and seed are mandatory; the function has
    no hidden expensive or random defaults.
    """
    values = validate_returns(returns, minimum_size=2)
    sample_size = int(values.size)
    if block_length < 1 or block_length > sample_size:
        raise ValueError("block_length must be between one and sample size")
    if replications < 2:
        raise ValueError("replications must be at least two")
    level = float(confidence_level)
    if not isfinite(level) or not 0.0 < level < 1.0:
        raise ValueError("confidence_level must be finite and in (0, 1)")
    generator = np.random.default_rng(seed)
    blocks_per_draw = ceil(sample_size / block_length)
    draws = np.empty(replications, dtype=np.float64)
    for replication in range(replications):
        starts = generator.integers(0, sample_size, size=blocks_per_draw)
        indices = circular_block_indices(
            sample_size=sample_size,
            block_length=block_length,
            starts=starts,
        )
        bootstrap_sample = values[indices]
        try:
            draws[replication] = sample_sharpe(bootstrap_sample)
        except ValueError as error:
            raise ValueError(
                f"bootstrap replication {replication} has degenerate variance"
            ) from error
    if not bool(np.all(np.isfinite(draws))):
        raise ArithmeticError("bootstrap produced a non-finite Sharpe draw")
    alpha = 1.0 - level
    lower, upper = np.quantile(
        draws,
        [alpha / 2.0, 1.0 - alpha / 2.0],
        method="linear",
    )
    interval = (float(lower), float(upper))
    if not all(isfinite(value) for value in interval) or interval[0] > interval[1]:
        raise ArithmeticError("bootstrap interval is invalid")
    return BootstrapResult(
        estimate=sample_sharpe(values),
        lower=interval[0],
        upper=interval[1],
        confidence_level=level,
        block_length=block_length,
        replications=replications,
        seed=seed,
        sample_size=sample_size,
        draws=tuple(float(value) for value in draws) if retain_draws else None,
    )
