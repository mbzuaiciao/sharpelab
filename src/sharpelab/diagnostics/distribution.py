"""Distribution-shape diagnostics with explicit moment conventions."""

from math import exp

from sharpelab.config import DistributionConfig
from sharpelab.data.returns import ReturnInput, validate_returns
from sharpelab.diagnostics.evidence_factory import fingerprint_returns, make_evidence
from sharpelab.diagnostics.summary import summarize_returns
from sharpelab.schemas.evidence import EvidenceFinding, EvidenceItem


def diagnose_distribution(
    returns: ReturnInput, config: DistributionConfig
) -> tuple[EvidenceItem, EvidenceItem]:
    values = validate_returns(returns, minimum_size=2)
    fingerprint = fingerprint_returns(values)
    if values.size < config.minimum_sample_size:
        shape = make_evidence(
            claim="gaussian_shape",
            finding=EvidenceFinding.INCONCLUSIVE,
            diagnostic_name="distribution-shape",
            sample_size=int(values.size),
            configuration={"minimum_sample_size": config.minimum_sample_size},
            warnings=("Sample is insufficient for configured shape thresholds.",),
            data_fingerprint=fingerprint,
        )
        return shape, _fourth_moment(int(values.size), None, fingerprint)
    summary = summarize_returns(values)
    jb = (
        summary.sample_size
        / 6.0
        * (summary.skewness**2 + 0.25 * (summary.raw_kurtosis - 3.0) ** 2)
    )
    p_value = exp(-0.5 * jb)
    material = (
        abs(summary.skewness) >= config.material_absolute_skewness
        or summary.raw_kurtosis >= config.heavy_tail_raw_kurtosis
        or p_value < config.significance_level
    )
    heavy_tail_warning = summary.raw_kurtosis >= config.heavy_tail_raw_kurtosis
    shape = make_evidence(
        claim="gaussian_shape",
        finding=EvidenceFinding.CONTRADICTS
        if material
        else EvidenceFinding.INCONCLUSIVE,
        diagnostic_name="distribution-shape",
        sample_size=summary.sample_size,
        statistic=jb,
        p_value=p_value,
        structured_output={
            "skewness": summary.skewness,
            "raw_kurtosis": summary.raw_kurtosis,
            "heavy_tail_warning": heavy_tail_warning,
        },
        configuration={
            "significance_level": config.significance_level,
            "material_absolute_skewness": config.material_absolute_skewness,
            "heavy_tail_raw_kurtosis": config.heavy_tail_raw_kurtosis,
        },
        methods_weakened=("iid-gaussian-sharpe",) if material else (),
        methods_enabled=("mertens-psr",) if material else (),
        assumptions=(
            "Skewness and raw kurtosis are uncorrected plug-in central moments.",
            "Kurtosis is raw Pearson kurtosis; Gaussian equals three.",
            "The Jarque-Bera statistic uses an asymptotic chi-square reference "
            "with two degrees of freedom.",
        ),
        warnings=(
            "The Jarque-Bera reference can be inaccurate in small samples.",
            *(
                ("Raw kurtosis crosses the configured heavy-tail warning threshold.",)
                if heavy_tail_warning
                else ()
            ),
        ),
        does_not_establish=(
            "Failure to reject Gaussian shape does not prove Gaussianity.",
            "A heavy-tail warning is a heuristic threshold, not a formal "
            "tail-index test.",
        ),
        data_fingerprint=fingerprint,
    )
    return shape, _fourth_moment(summary.sample_size, summary.raw_kurtosis, fingerprint)


def _fourth_moment(
    sample_size: int, raw_kurtosis: float | None, fingerprint: str
) -> EvidenceItem:
    return make_evidence(
        claim="finite_fourth_moment_plausible",
        finding=EvidenceFinding.INCONCLUSIVE,
        diagnostic_name="distribution-shape",
        sample_size=sample_size,
        statistic=raw_kurtosis,
        structured_output={"raw_kurtosis": raw_kurtosis},
        warnings=("Finite-fourth-moment assessment is heuristic only.",),
        does_not_establish=(
            "A finite sample cannot prove that the population fourth moment is finite.",
        ),
        data_fingerprint=fingerprint,
    )
