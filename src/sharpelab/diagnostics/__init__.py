"""Typed deterministic diagnostics for statistical inference."""

from sharpelab.diagnostics.provenance import ProvenanceCompleteness, ResearchProvenance
from sharpelab.diagnostics.registry import run_diagnostics
from sharpelab.diagnostics.summary import ReturnSummary, summarize_returns

__all__ = [
    "ProvenanceCompleteness",
    "ResearchProvenance",
    "ReturnSummary",
    "run_diagnostics",
    "summarize_returns",
]
