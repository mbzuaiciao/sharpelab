"""Versioned metadata for deterministic inference methods."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MethodSpec:
    method_id: str
    version: str
    assumptions: tuple[str, ...]
    required_evidence: tuple[str, ...]
    contraindications: tuple[str, ...]
    minimum_sample_requirement: str
    required_configuration: tuple[str, ...]
    supported_outputs: tuple[str, ...]
    limitations: tuple[str, ...]


METHOD_CATALOG: tuple[MethodSpec, ...] = (
    MethodSpec(
        "iid-gaussian-sharpe",
        "1.0",
        ("IID Gaussian returns",),
        ("valid data", "adequate variance"),
        ("temporal dependence", "material non-Gaussianity"),
        "routing.iid_gaussian_minimum_sample",
        (),
        ("estimate", "CI", "test"),
        ("Failure to detect dependence does not prove IID.",),
    ),
    MethodSpec(
        "mertens-psr",
        "1.0",
        ("IID returns", "stable low-order moments"),
        ("valid data", "adequate variance"),
        ("temporal dependence",),
        "routing.mertens_minimum_sample",
        (),
        ("frequentist PSR",),
        ("PSR is not a Bayesian posterior.", "Moment estimates may be unstable."),
    ),
    MethodSpec(
        "hac-sharpe",
        "1.0",
        ("weak dependence", "structural stability"),
        ("valid data", "adequate sample"),
        ("major instability",),
        "routing.hac_minimum_sample",
        ("hac_bandwidth",),
        ("estimate", "standard error"),
        ("Bandwidth is not inferred.", "Not valid under arbitrary nonstationarity."),
    ),
    MethodSpec(
        "circular-block-bootstrap",
        "1.0",
        ("local dependence preserved by blocks",),
        ("valid data", "adequate sample"),
        ("major instability",),
        "routing.bootstrap_minimum_sample",
        ("block_length", "replications", "seed"),
        ("estimate", "percentile interval"),
        (
            "Block length is not inferred.",
            "No universal block-bootstrap validity claim.",
        ),
    ),
    MethodSpec(
        "sensitivity-comparison",
        "1.0",
        ("At least two valid methods",),
        ("multiple eligible methods",),
        (),
        "not applicable",
        (),
        ("conclusion agreement",),
        ("Comparison does not adjudicate a misspecified common assumption.",),
    ),
    MethodSpec(
        "deflated-sharpe-ratio",
        "future",
        ("Fully specified selection process",),
        ("complete multiplicity provenance",),
        ("missing trial provenance",),
        "not implemented",
        ("trial count", "trial dependence"),
        (),
        ("Phase 2 does not implement DSR.",),
    ),
    MethodSpec(
        "abstention",
        "1.0",
        (),
        ("Recorded validity failure or evidence gap",),
        (),
        "not applicable",
        (),
        ("reasons", "information requests"),
        ("Abstention communicates scope; it is not evidence against a strategy.",),
    ),
)


def get_method(method_id: str) -> MethodSpec:
    """Return catalog metadata for one exact method identifier."""
    for method in METHOD_CATALOG:
        if method.method_id == method_id:
            return method
    raise KeyError(method_id)
