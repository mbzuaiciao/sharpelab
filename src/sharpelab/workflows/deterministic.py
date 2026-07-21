"""Plain-Python evidence-to-inference workflow with no network or LLM."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from sharpelab.config import Phase2Config, load_phase2_config
from sharpelab.data.returns import ReturnInput
from sharpelab.diagnostics.provenance import ResearchProvenance
from sharpelab.diagnostics.registry import run_diagnostics
from sharpelab.inference.block_bootstrap import circular_block_bootstrap
from sharpelab.inference.gaussian import (
    gaussian_sharpe_confidence_interval,
    gaussian_sharpe_test,
)
from sharpelab.inference.hac import hac_sharpe_standard_error
from sharpelab.inference.mertens_psr import probabilistic_sharpe_ratio
from sharpelab.routing.router import route_methods
from sharpelab.routing.sensitivity import ConclusionComparison, compare_conclusions
from sharpelab.schemas.evidence import EvidenceItem
from sharpelab.schemas.inference import InferenceResult
from sharpelab.schemas.methods import MethodDecision


class DeterministicWorkflowResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    evidence: tuple[EvidenceItem, ...]
    decision: MethodDecision
    inference_results: tuple[InferenceResult, ...] = ()
    comparison: ConclusionComparison | None = None


def run_deterministic_workflow(
    returns: ReturnInput,
    config: Phase2Config,
    *,
    timestamps: Sequence[datetime | None] | None = None,
    provenance: ResearchProvenance | None = None,
) -> DeterministicWorkflowResult:
    """Validate, diagnose, route, and run selected/sensitivity methods."""
    evidence = run_diagnostics(
        returns, config.diagnostics, timestamps=timestamps, provenance=provenance
    )
    decision = route_methods(evidence, config.routing, config.experiment)
    if decision.selected_method is None:
        return DeterministicWorkflowResult(evidence=evidence, decision=decision)
    method_ids = (decision.selected_method, *decision.sensitivity_methods)
    data_fingerprint = next(
        (
            item.data_fingerprint
            for item in evidence
            if item.data_fingerprint is not None
        ),
        None,
    )
    provenance_reference = next(
        (
            item.provenance_reference
            for item in evidence
            if item.provenance_reference is not None
        ),
        None,
    )
    results = tuple(
        run_inference_method(
            method_id,
            returns,
            config,
            data_fingerprint=data_fingerprint,
            provenance_reference=provenance_reference,
        )
        for method_id in method_ids
    )
    comparison = compare_conclusions(
        results,
        benchmark=config.experiment.benchmark_sharpe,
        significance_level=1.0 - config.experiment.confidence_level,
    )
    return DeterministicWorkflowResult(
        evidence=evidence,
        decision=decision,
        inference_results=results,
        comparison=comparison,
    )


def run_inference_method(
    method_id: str,
    returns: ReturnInput,
    config: Phase2Config,
    *,
    data_fingerprint: str | None,
    provenance_reference: str | None,
) -> InferenceResult:
    """Execute one allowlisted audited inference method by identifier."""
    experiment = config.experiment
    if method_id == "iid-gaussian-sharpe":
        interval = gaussian_sharpe_confidence_interval(
            returns, confidence_level=experiment.confidence_level
        )
        test = gaussian_sharpe_test(returns, benchmark=experiment.benchmark_sharpe)
        return InferenceResult(
            inference_id="workflow:iid-gaussian",
            method_id=method_id,
            method_version="1.0",
            estimate=interval.estimate,
            standard_error=interval.standard_error,
            confidence_level=interval.confidence_level,
            confidence_interval=(interval.lower, interval.upper),
            p_value=test.p_value,
            benchmark_sharpe=experiment.benchmark_sharpe,
            sample_frequency="per-period",
            annualization_convention="not-annualized",
            data_fingerprint=data_fingerprint,
            data_provenance=provenance_reference,
            warnings=interval.warnings,
            assumptions=interval.assumptions,
            metadata={"benchmark_scale": "per-period"},
        )
    if method_id == "mertens-psr":
        psr = probabilistic_sharpe_ratio(returns, benchmark=experiment.benchmark_sharpe)
        return InferenceResult(
            inference_id="workflow:mertens-psr",
            method_id=method_id,
            method_version="1.0",
            estimate=psr.sample_sharpe,
            standard_error=psr.standard_error,
            confidence_level=experiment.confidence_level,
            benchmark_sharpe=experiment.benchmark_sharpe,
            sample_frequency="per-period",
            annualization_convention="not-annualized",
            data_fingerprint=data_fingerprint,
            data_provenance=provenance_reference,
            warnings=psr.warnings,
            assumptions=("PSR is a frequentist normal-approximation probability.",),
            metadata={
                "frequentist_probability": psr.probabilistic_sharpe_ratio,
                "skewness": psr.skewness,
                "raw_kurtosis": psr.raw_kurtosis,
                "benchmark_scale": "per-period",
            },
        )
    if method_id == "hac-sharpe":
        hac = hac_sharpe_standard_error(returns, bandwidth=experiment.hac_bandwidth)
        return InferenceResult(
            inference_id="workflow:hac",
            method_id=method_id,
            method_version="1.0",
            estimate=hac.estimate,
            standard_error=hac.standard_error,
            confidence_level=experiment.confidence_level,
            benchmark_sharpe=experiment.benchmark_sharpe,
            sample_frequency="per-period",
            annualization_convention="not-annualized",
            data_fingerprint=data_fingerprint,
            data_provenance=provenance_reference,
            method_configuration={"bandwidth": experiment.hac_bandwidth},
            assumptions=(
                "Bartlett/Newey-West long-run variance with Sharpe influence function.",
            ),
            metadata={
                "long_run_variance": hac.long_run_variance,
                "benchmark_scale": "per-period",
            },
        )
    if method_id == "circular-block-bootstrap":
        bootstrap = circular_block_bootstrap(
            returns,
            block_length=experiment.bootstrap_block_length,
            replications=experiment.bootstrap_replications,
            seed=experiment.bootstrap_seed,
            confidence_level=experiment.confidence_level,
        )
        return InferenceResult(
            inference_id="workflow:block-bootstrap",
            method_id=method_id,
            method_version="1.0",
            estimate=bootstrap.estimate,
            confidence_level=bootstrap.confidence_level,
            confidence_interval=(bootstrap.lower, bootstrap.upper),
            benchmark_sharpe=experiment.benchmark_sharpe,
            sample_frequency="per-period",
            annualization_convention="not-annualized",
            data_fingerprint=data_fingerprint,
            data_provenance=provenance_reference,
            method_configuration={
                "block_length": bootstrap.block_length,
                "replications": bootstrap.replications,
                "seed": bootstrap.seed,
            },
            metadata={"benchmark_scale": "per-period"},
        )
    raise KeyError(f"unsupported workflow method: {method_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-root", type=Path, default=Path("configs"))
    args = parser.parse_args()
    config = load_phase2_config(args.config_root)
    returns = [0.01, -0.005, 0.006, -0.002, 0.008, 0.001] * 20
    result = run_deterministic_workflow(returns, config)
    print(result.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
