"""Return-series and optional timestamp quality diagnostics."""

from collections import Counter
from collections.abc import Sequence
from datetime import datetime

import numpy as np

from sharpelab.config import DataQualityConfig
from sharpelab.diagnostics.evidence_factory import fingerprint_returns, make_evidence
from sharpelab.schemas.evidence import EvidenceFinding, EvidenceItem


def diagnose_data_quality(
    returns: object,
    config: DataQualityConfig,
    *,
    timestamps: Sequence[datetime | None] | None = None,
) -> tuple[EvidenceItem, ...]:
    """Diagnose validity without imputing or silently dropping observations."""
    try:
        values = np.asarray(returns, dtype=np.float64)
    except (TypeError, ValueError):
        values = np.asarray([], dtype=np.float64)
    valid_shape = values.ndim == 1
    nonempty = values.size > 0
    all_finite = nonempty and bool(np.all(np.isfinite(values)))
    valid = valid_shape and nonempty and all_finite
    sample_size = int(values.size) if valid_shape and values.size > 0 else None
    fingerprint = fingerprint_returns(values) if nonempty else None
    validity = make_evidence(
        claim="data_validity",
        finding=EvidenceFinding.SUPPORTS if valid else EvidenceFinding.CONTRADICTS,
        diagnostic_name="data-quality",
        sample_size=sample_size,
        structured_output={
            "one_dimensional": valid_shape,
            "nonempty": nonempty,
            "all_finite": all_finite,
        },
        warnings=() if valid else ("No values were imputed or removed.",),
        methods_ruled_out=() if valid else ("all-inference-methods",),
        data_fingerprint=fingerprint,
    )
    if not valid:
        return (validity,)
    assert fingerprint is not None
    enough = values.size >= config.minimum_sample_size
    sample = make_evidence(
        claim="sample_size_adequate",
        finding=EvidenceFinding.SUPPORTS if enough else EvidenceFinding.CONTRADICTS,
        diagnostic_name="data-quality",
        sample_size=int(values.size),
        statistic=float(values.size),
        configuration={"minimum_sample_size": config.minimum_sample_size},
        data_fingerprint=fingerprint,
    )
    variance = float(np.var(values)) if values.size else 0.0
    variance_ok = variance > config.near_zero_variance
    variance_item = make_evidence(
        claim="variance_adequate",
        finding=EvidenceFinding.SUPPORTS
        if variance_ok
        else EvidenceFinding.CONTRADICTS,
        diagnostic_name="data-quality",
        sample_size=int(values.size),
        statistic=variance,
        configuration={"near_zero_variance": config.near_zero_variance},
        methods_ruled_out=() if variance_ok else ("all-sharpe-methods",),
        data_fingerprint=fingerprint,
    )
    counts = Counter(float(value) for value in values)
    modal_fraction = max(counts.values(), default=0) / max(1, values.size)
    repeated_fraction = 1.0 - len(counts) / max(1, values.size)
    concentrated = (
        modal_fraction >= config.extreme_concentration_fraction
        or repeated_fraction >= config.repeated_value_warning_fraction
    )
    concentration = make_evidence(
        claim="return_concentration_risk",
        finding=EvidenceFinding.SUPPORTS
        if concentrated
        else EvidenceFinding.INCONCLUSIVE,
        diagnostic_name="data-quality",
        sample_size=int(values.size),
        statistic=float(modal_fraction),
        structured_output={
            "modal_fraction": float(modal_fraction),
            "repeated_fraction": float(repeated_fraction),
            "possible_stale_or_smoothed_prices": concentrated,
        },
        configuration={
            "extreme_concentration_fraction": config.extreme_concentration_fraction,
            "repeated_value_warning_fraction": config.repeated_value_warning_fraction,
        },
        warnings=("Repeated values may indicate stale prices or smoothing.",)
        if concentrated
        else (),
        does_not_establish=(
            "The configured repetition cutoff is a heuristic warning, not a "
            "formal stale-price test.",
            "No detected concentration does not prove unsmoothed prices.",
        ),
        data_fingerprint=fingerprint,
    )
    return (
        validity,
        sample,
        variance_item,
        concentration,
        _diagnose_timestamps(timestamps, int(values.size), config, fingerprint),
    )


def _diagnose_timestamps(
    timestamps: Sequence[datetime | None] | None,
    sample_size: int,
    config: DataQualityConfig,
    fingerprint: str,
) -> EvidenceItem:
    supplied = timestamps is not None
    sequence = tuple(timestamps or ())
    present = tuple(value for value in sequence if value is not None)
    missing = sum(value is None for value in sequence)
    duplicates = len(present) - len(set(present))
    length_mismatch = supplied and len(sequence) != sample_size
    spacings = np.asarray(
        [
            (right - left).total_seconds()
            for left, right in zip(present, present[1:], strict=False)
        ],
        dtype=np.float64,
    )
    positive = spacings.size == 0 or bool(np.all(spacings > 0.0))
    spacing_cv = (
        float(np.std(spacings) / np.mean(spacings))
        if spacings.size > 1 and float(np.mean(spacings)) > 0.0
        else 0.0
    )
    irregular = spacing_cv > config.irregular_spacing_cv
    problem = (
        length_mismatch or missing > 0 or duplicates > 0 or not positive or irregular
    )
    finding = (
        EvidenceFinding.INCONCLUSIVE
        if not supplied
        else EvidenceFinding.CONTRADICTS
        if problem
        else EvidenceFinding.SUPPORTS
    )
    return make_evidence(
        claim="timestamp_quality",
        finding=finding,
        diagnostic_name="data-quality",
        sample_size=sample_size,
        structured_output={
            "timestamps_supplied": supplied,
            "length_mismatch": length_mismatch,
            "missing_count": missing,
            "duplicate_count": duplicates,
            "strictly_increasing": positive,
            "spacing_coefficient_of_variation": spacing_cv,
            "irregular_spacing": irregular,
        },
        configuration={"irregular_spacing_cv": config.irregular_spacing_cv},
        warnings=("Timestamp quality limits frequency-sensitive interpretation.",)
        if problem
        else (),
        data_fingerprint=fingerprint,
    )
