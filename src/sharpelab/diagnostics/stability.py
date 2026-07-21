"""Lightweight split-sample structural stability diagnostics."""

import numpy as np

from sharpelab.config import StabilityConfig
from sharpelab.data.returns import ReturnInput, validate_returns
from sharpelab.diagnostics.evidence_factory import fingerprint_returns, make_evidence
from sharpelab.schemas.evidence import EvidenceFinding, EvidenceItem


def diagnose_stability(returns: ReturnInput, config: StabilityConfig) -> EvidenceItem:
    values = validate_returns(returns, minimum_size=2)
    fingerprint = fingerprint_returns(values)
    if values.size < config.minimum_sample_size:
        return make_evidence(
            claim="structural_stability",
            finding=EvidenceFinding.INCONCLUSIVE,
            diagnostic_name="split-sample-stability",
            sample_size=int(values.size),
            configuration={"minimum_sample_size": config.minimum_sample_size},
            warnings=("Stability tests have finite-sample limitations.",),
            data_fingerprint=fingerprint,
        )
    split = int(values.size * config.split_fraction)
    if (
        split < config.minimum_segment_size
        or values.size - split < config.minimum_segment_size
    ):
        return make_evidence(
            claim="structural_stability",
            finding=EvidenceFinding.INCONCLUSIVE,
            diagnostic_name="split-sample-stability",
            sample_size=int(values.size),
            structured_output={"proposed_split_index": split},
            configuration={
                "split_fraction": config.split_fraction,
                "minimum_segment_size": config.minimum_segment_size,
            },
            warnings=(
                "The configured split leaves a segment below its minimum size.",
            ),
            does_not_establish=(
                "An unevaluable split provides no evidence of structural stability.",
            ),
            data_fingerprint=fingerprint,
        )
    left, right = values[:split], values[split:]
    left_variance, right_variance = (
        float(np.var(left, ddof=1)),
        float(np.var(right, ddof=1)),
    )
    standard_error = float(
        np.sqrt(left_variance / left.size + right_variance / right.size)
    )
    mean_z = float(
        abs(float(np.mean(left) - np.mean(right)))
        / max(standard_error, float(np.finfo(float).eps))
    )
    variance_ratio = float(
        max(left_variance, right_variance)
        / max(min(left_variance, right_variance), float(np.finfo(float).eps))
    )
    mean_instability = bool(mean_z >= config.material_mean_z)
    variance_instability = bool(
        variance_ratio >= config.material_variance_ratio
    )
    unstable = mean_instability or variance_instability
    triggered_components = tuple(
        component
        for component, triggered in (
            ("mean", mean_instability),
            ("variance", variance_instability),
        )
        if triggered
    )
    return make_evidence(
        claim="structural_stability",
        finding=EvidenceFinding.CONTRADICTS
        if unstable
        else EvidenceFinding.INCONCLUSIVE,
        diagnostic_name="split-sample-stability",
        sample_size=int(values.size),
        structured_output={
            "split_index": split,
            "segment_sizes": [int(left.size), int(right.size)],
            "mean_standardized_difference": mean_z,
            "variance_ratio": variance_ratio,
            "mean_instability_detected": mean_instability,
            "variance_instability_detected": variance_instability,
            "instability_risk_detected": unstable,
            "triggered_components": list(triggered_components),
        },
        configuration={
            "split_fraction": config.split_fraction,
            "material_mean_z": config.material_mean_z,
            "material_variance_ratio": config.material_variance_ratio,
            "minimum_segment_size": config.minimum_segment_size,
        },
        methods_weakened=("hac-sharpe", "circular-block-bootstrap") if unstable else (),
        warnings=(
            "Mean and variance cutoffs are policy thresholds, not calibrated "
            "change-point tests; finite-sample power is limited.",
        ),
        does_not_establish=(
            "No detected split change does not prove stationarity.",
            "Detected instability risk does not identify an exact change point "
            "or structural-change model.",
        ),
        data_fingerprint=fingerprint,
    )
