"""Deterministic registry for the Phase 2 diagnostic suite."""

from collections.abc import Sequence
from datetime import datetime

from sharpelab.config import DiagnosticsConfig
from sharpelab.data.returns import ReturnInput
from sharpelab.diagnostics.data_quality import diagnose_data_quality
from sharpelab.diagnostics.dependence import (
    diagnose_linear_dependence,
    diagnose_squared_dependence,
)
from sharpelab.diagnostics.distribution import diagnose_distribution
from sharpelab.diagnostics.provenance import ResearchProvenance, diagnose_provenance
from sharpelab.diagnostics.stability import diagnose_stability
from sharpelab.schemas.evidence import EvidenceFinding, EvidenceItem


def run_diagnostics(
    returns: ReturnInput,
    config: DiagnosticsConfig,
    *,
    timestamps: Sequence[datetime | None] | None = None,
    provenance: ResearchProvenance | None = None,
) -> tuple[EvidenceItem, ...]:
    quality = diagnose_data_quality(returns, config.data_quality, timestamps=timestamps)
    validity = next(item for item in quality if item.claim == "data_validity")
    variance = next(
        (item for item in quality if item.claim == "variance_adequate"), None
    )
    provenance_item = diagnose_provenance(provenance)
    if validity.finding is EvidenceFinding.CONTRADICTS or (
        variance is not None and variance.finding is EvidenceFinding.CONTRADICTS
    ):
        return (*quality, provenance_item)
    distribution = diagnose_distribution(returns, config.distribution)
    return (
        *quality,
        diagnose_linear_dependence(returns, config.linear_dependence),
        diagnose_squared_dependence(returns, config.squared_dependence),
        *distribution,
        diagnose_stability(returns, config.stability),
        provenance_item,
    )


def run_named_diagnostic(
    diagnostic_name: str,
    returns: ReturnInput,
    config: DiagnosticsConfig,
    *,
    timestamps: Sequence[datetime | None] | None = None,
    provenance: ResearchProvenance | None = None,
) -> tuple[EvidenceItem, ...]:
    """Execute exactly one registered diagnostic family by canonical name."""
    if diagnostic_name == "data-quality":
        return diagnose_data_quality(
            returns, config.data_quality, timestamps=timestamps
        )
    if diagnostic_name == "linear-dependence":
        return (diagnose_linear_dependence(returns, config.linear_dependence),)
    if diagnostic_name == "squared-return-dependence":
        return (diagnose_squared_dependence(returns, config.squared_dependence),)
    if diagnostic_name == "distribution-shape":
        return diagnose_distribution(returns, config.distribution)
    if diagnostic_name == "split-sample-stability":
        return (diagnose_stability(returns, config.stability),)
    if diagnostic_name == "provenance":
        return (diagnose_provenance(provenance),)
    raise KeyError(f"unknown diagnostic name: {diagnostic_name}")
