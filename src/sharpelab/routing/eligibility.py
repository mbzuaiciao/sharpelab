"""Evidence-to-method eligibility rules."""

from sharpelab.config import ExperimentConfig, RoutingConfig
from sharpelab.schemas.evidence import EvidenceFinding, EvidenceItem
from sharpelab.schemas.methods import MethodEligibility


def evaluate_eligibility(
    evidence: tuple[EvidenceItem, ...],
    routing: RoutingConfig,
    experiment: ExperimentConfig,
) -> tuple[MethodEligibility, ...]:
    """Evaluate every implemented method using explicit typed evidence."""
    by_claim: dict[str, tuple[EvidenceItem, ...]] = {}
    for item in evidence:
        by_claim[item.claim] = (*by_claim.get(item.claim, ()), item)
    sample_size = max((item.sample_size or 0 for item in evidence), default=0)
    invalid = _contradicts(by_claim.get("data_validity", ()))
    degenerate = _contradicts(by_claim.get("variance_adequate", ()))
    linear = _contradicts(by_claim.get("linear_independence", ()))
    squared = _contradicts(
        by_claim.get("absence_of_squared_return_dependence", ())
    )
    non_gaussian = _contradicts(by_claim.get("gaussian_shape", ()))
    unstable = _contradicts(by_claim.get("structural_stability", ()))
    independence_supported = _supported_only(
        by_claim.get("linear_independence", ())
    ) and _supported_only(
        by_claim.get("absence_of_squared_return_dependence", ())
    )

    def references(*claims: str) -> tuple[str, ...]:
        return tuple(
            item.evidence_id
            for claim in claims
            for item in by_claim.get(claim, ())
        )

    common_failure = invalid or degenerate

    iid_reasons: list[str] = []
    if common_failure:
        iid_reasons.append("Data are invalid or variance is degenerate.")
    if sample_size < routing.iid_gaussian_minimum_sample:
        iid_reasons.append("Sample is below the configured IID Gaussian minimum.")
    if linear or squared:
        iid_reasons.append("Temporal dependence contradicts IID inference.")
    iid_eligible = not iid_reasons
    iid = MethodEligibility(
        method_id="iid-gaussian-sharpe",
        eligible=iid_eligible,
        reasons=tuple(iid_reasons)
        or (
            "Conditionally eligible for sensitivity; configured diagnostics "
            "did not establish IID assumptions.",
        ),
        evidence_references=references(
            "data_validity",
            "variance_adequate",
            "linear_independence",
            "absence_of_squared_return_dependence",
            "gaussian_shape",
        ),
        weakened=iid_eligible and (non_gaussian or not independence_supported),
        sensitivity_only=iid_eligible and (
            non_gaussian or not independence_supported
        ),
    )

    mertens_reasons: list[str] = []
    if common_failure:
        mertens_reasons.append("Data are invalid or variance is degenerate.")
    if sample_size < routing.mertens_minimum_sample:
        mertens_reasons.append("Sample is below the configured Mertens minimum.")
    if linear or squared:
        mertens_reasons.append(
            "Temporal dependence contradicts the IID basis of Mertens/PSR."
        )
    mertens_eligible = not mertens_reasons
    mertens = MethodEligibility(
        method_id="mertens-psr",
        eligible=mertens_eligible,
        reasons=tuple(mertens_reasons)
        or (
            "Conditionally eligible for sensitivity; Mertens/PSR is not "
            "dependence robust and IID assumptions were not established.",
        ),
        evidence_references=references(
            "data_validity",
            "variance_adequate",
            "linear_independence",
            "absence_of_squared_return_dependence",
            "gaussian_shape",
        ),
        weakened=mertens_eligible and not independence_supported,
        sensitivity_only=mertens_eligible and not independence_supported,
    )

    hac_reasons: list[str] = []
    if common_failure:
        hac_reasons.append("Data are invalid or variance is degenerate.")
    if sample_size < routing.hac_minimum_sample:
        hac_reasons.append("Sample is below the configured HAC minimum.")
    if unstable and routing.abstain_on_structural_instability:
        hac_reasons.append("Material structural instability violates routing policy.")
    if experiment.hac_bandwidth >= sample_size and sample_size > 0:
        hac_reasons.append("HAC bandwidth must be below sample size.")
    hac_eligible = not hac_reasons
    hac = MethodEligibility(
        method_id="hac-sharpe",
        eligible=hac_eligible,
        reasons=tuple(hac_reasons)
        or ("Explicit-bandwidth weak-dependence inference is eligible.",),
        evidence_references=references(
            "data_validity", "variance_adequate", "structural_stability"
        ),
        weakened=hac_eligible and unstable,
        missing_requirements=()
        if experiment.hac_bandwidth >= 0
        else ("hac_bandwidth",),
    )

    bootstrap_reasons: list[str] = []
    if common_failure:
        bootstrap_reasons.append("Data are invalid or variance is degenerate.")
    if sample_size < routing.bootstrap_minimum_sample:
        bootstrap_reasons.append("Sample is below the configured bootstrap minimum.")
    if unstable and routing.abstain_on_structural_instability:
        bootstrap_reasons.append(
            "Material structural instability violates routing policy."
        )
    if experiment.bootstrap_block_length > sample_size and sample_size > 0:
        bootstrap_reasons.append("Bootstrap block length exceeds sample size.")
    bootstrap_eligible = not bootstrap_reasons
    bootstrap = MethodEligibility(
        method_id="circular-block-bootstrap",
        eligible=bootstrap_eligible,
        reasons=tuple(bootstrap_reasons)
        or ("Explicit block length, replications, and seed are supplied.",),
        evidence_references=references(
            "data_validity", "variance_adequate", "structural_stability"
        ),
        weakened=bootstrap_eligible and unstable,
    )
    return iid, mertens, hac, bootstrap


def _contradicts(items: tuple[EvidenceItem, ...]) -> bool:
    return any(
        item.finding
        in (EvidenceFinding.CONTRADICTS, EvidenceFinding.CONTRADICTION)
        for item in items
    )


def _supported_only(items: tuple[EvidenceItem, ...]) -> bool:
    return bool(items) and all(
        item.finding in (EvidenceFinding.SUPPORTS, EvidenceFinding.SUPPORT)
        for item in items
    )
