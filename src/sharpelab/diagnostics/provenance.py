"""Typed research-process provenance and completeness evidence."""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sharpelab.diagnostics.evidence_factory import make_evidence
from sharpelab.schemas.evidence import EvidenceFinding, EvidenceItem


class ProvenanceCompleteness(StrEnum):
    MISSING = "missing"
    PARTIAL = "partial"
    COMPLETE = "complete"


class ResearchProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    trials: int | None = Field(default=None, ge=1)
    parameter_searches: int | None = Field(default=None, ge=0)
    markets_or_universes: tuple[str, ...] = ()
    start_dates_or_windows: tuple[str, ...] = ()
    failed_trials_retained: bool | None = None
    trial_dependence_known: bool | None = None
    completeness: ProvenanceCompleteness = ProvenanceCompleteness.MISSING
    reference: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_completeness(self) -> Self:
        text_entries = (*self.markets_or_universes, *self.start_dates_or_windows)
        if any(not entry.strip() for entry in text_entries):
            raise ValueError("provenance market and window entries must not be blank")
        if self.completeness is ProvenanceCompleteness.COMPLETE:
            required_scalars = (
                self.trials,
                self.parameter_searches,
                self.failed_trials_retained,
                self.trial_dependence_known,
            )
            if any(value is None for value in required_scalars):
                raise ValueError(
                    "complete provenance requires trial counts, search counts, "
                    "failed-trial retention, and trial-dependence status"
                )
            if not self.markets_or_universes or not self.start_dates_or_windows:
                raise ValueError(
                    "complete provenance requires searched universes and windows"
                )
        return self


def diagnose_provenance(provenance: ResearchProvenance | None) -> EvidenceItem:
    supplied = provenance or ResearchProvenance()
    complete = supplied.completeness is ProvenanceCompleteness.COMPLETE
    return make_evidence(
        claim="selection_provenance_complete",
        finding=EvidenceFinding.SUPPORTS if complete else EvidenceFinding.INCONCLUSIVE,
        diagnostic_name="research-provenance",
        sample_size=None,
        structured_output={
            "completeness": supplied.completeness.value,
            "trials": supplied.trials,
            "parameter_searches": supplied.parameter_searches,
            "markets_or_universes": list(supplied.markets_or_universes),
            "start_dates_or_windows": list(supplied.start_dates_or_windows),
            "failed_trials_retained": supplied.failed_trials_retained,
            "trial_dependence_known": supplied.trial_dependence_known,
        },
        uncertainty={"completeness": supplied.completeness.value},
        warnings=()
        if complete
        else ("Selection bias cannot be assessed from the return series alone.",),
        methods_ruled_out=() if complete else ("deflated-sharpe-ratio",),
        does_not_establish=(
            "Return diagnostics cannot reconstruct unreported research trials.",
        ),
        provenance_reference=supplied.reference,
    )
