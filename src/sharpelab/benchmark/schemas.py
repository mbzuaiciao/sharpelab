"""Immutable typed contracts for Phase 3A simulation and evaluation."""

from __future__ import annotations

from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Self

from pydantic import (
    Field,
    FiniteFloat,
    JsonValue,
    model_validator,
)

from sharpelab.config import ConfigModel


class BenchmarkModel(ConfigModel):
    """Strict immutable benchmark schema."""


class ProcessFamily(StrEnum):
    IID_GAUSSIAN = "iid-gaussian"
    AR1 = "ar1"
    GARCH = "garch"
    STRUCTURAL_BREAK = "structural-break"


class BaselineName(StrEnum):
    ALWAYS_GAUSSIAN = "always-iid-gaussian"
    ALWAYS_HAC = "always-hac"
    DETERMINISTIC_ROUTER = "deterministic-router"
    ORACLE = "oracle"


class EligibilityStatus(StrEnum):
    ELIGIBLE = "eligible"
    SENSITIVITY_ONLY = "sensitivity-only"
    INELIGIBLE = "ineligible"
    TARGET_NOT_WELL_DEFINED = "target-not-well-defined"


class LabelBasis(StrEnum):
    ANALYTICAL = "analytical"
    POLICY = "policy-based"


class EligibilityLabel(BenchmarkModel):
    method_id: str = Field(min_length=1)
    status: EligibilityStatus
    reason: str = Field(min_length=1)
    assumptions: tuple[str, ...] = ()
    version: str = Field(min_length=1)
    basis: LabelBasis


class SimulationResult(BenchmarkModel):
    returns: tuple[FiniteFloat, ...] = Field(min_length=2)
    true_mean: FiniteFloat | None
    true_standard_deviation: FiniteFloat | None
    true_sharpe: FiniteFloat | None
    descriptive_full_sample_sharpe: FiniteFloat | None = None
    target_defined: bool
    sample_size: int = Field(ge=2)
    seed: int
    process_family: ProcessFamily
    process_version: str = Field(min_length=1)
    parameters: dict[str, JsonValue]
    inference_truth: dict[str, JsonValue]
    caveats: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_target_and_values(self) -> Self:
        if len(self.returns) != self.sample_size:
            raise ValueError("returns length must equal sample_size")
        if self.target_defined:
            if (
                self.true_mean is None
                or self.true_standard_deviation is None
                or self.true_sharpe is None
            ):
                raise ValueError("a defined target requires finite population moments")
            if self.true_standard_deviation <= 0.0:
                raise ValueError("true standard deviation must be positive")
        elif self.true_sharpe is not None:
            raise ValueError("an undefined inferential target cannot have true_sharpe")
        return self


class ScenarioConfig(BenchmarkModel):
    scenario_id: str = Field(min_length=1)
    family: ProcessFamily
    sample_size: int = Field(ge=30)
    parameters: dict[str, JsonValue]


class BenchmarkConfig(BenchmarkModel):
    benchmark_version: str = Field(min_length=1)
    run_label: str = Field(min_length=1)
    output_root: Path = Path("runs/phase3a")
    confidence_level: FiniteFloat = Field(gt=0.0, lt=1.0)
    hac_bandwidth: int = Field(ge=0)
    bootstrap_block_length: int = Field(ge=1)
    bootstrap_replications: int = Field(ge=2)
    bootstrap_seed: int
    loss_profile: str = Field(min_length=1)
    oracle_training_seeds: tuple[int, ...] = Field(min_length=1)
    evaluation_seeds: tuple[int, ...] = Field(min_length=1)
    scenarios: tuple[ScenarioConfig, ...] = Field(min_length=4)
    generate_figures: bool = True

    @model_validator(mode="after")
    def validate_benchmark_design(self) -> Self:
        ids = [scenario.scenario_id for scenario in self.scenarios]
        if len(ids) != len(set(ids)):
            raise ValueError("scenario IDs must be unique")
        if set(self.oracle_training_seeds) & set(self.evaluation_seeds):
            raise ValueError("oracle training and evaluation seeds must be disjoint")
        if len(self.oracle_training_seeds) != len(set(self.oracle_training_seeds)):
            raise ValueError("oracle training seeds must be unique")
        if len(self.evaluation_seeds) != len(set(self.evaluation_seeds)):
            raise ValueError("evaluation seeds must be unique")
        families = {scenario.family for scenario in self.scenarios}
        if families != set(ProcessFamily):
            raise ValueError("Phase 3A configuration must include all four families")
        for scenario in self.scenarios:
            if self.hac_bandwidth >= scenario.sample_size:
                raise ValueError("HAC bandwidth must be below every sample size")
            if self.bootstrap_block_length > scenario.sample_size:
                raise ValueError("bootstrap block length exceeds a sample size")
        return self


class LossProfile(BenchmarkModel):
    name: str = Field(min_length=1)
    coverage_error: FiniteFloat = Field(ge=0.0)
    interval_width: FiniteFloat = Field(ge=0.0)
    invalid_method: FiniteFloat = Field(ge=0.0)
    harmful_nonabstention: FiniteFloat = Field(ge=0.0)
    unnecessary_abstention: FiniteFloat = Field(ge=0.0)
    execution_failure: FiniteFloat = Field(ge=0.0)
    abstention: FiniteFloat = Field(ge=0.0)
    runtime: FiniteFloat = Field(ge=0.0)
    interval_width_scale: FiniteFloat = Field(gt=0.0)
    runtime_scale_seconds: FiniteFloat = Field(gt=0.0)
    notes: str = Field(min_length=1)


class LossProfiles(BenchmarkModel):
    profiles: tuple[LossProfile, ...] = Field(min_length=2)

    @model_validator(mode="after")
    def unique_names(self) -> Self:
        names = [profile.name for profile in self.profiles]
        if len(names) != len(set(names)):
            raise ValueError("loss profile names must be unique")
        return self


class MethodExecution(BenchmarkModel):
    selected_method: str | None = Field(default=None, min_length=1)
    sensitivity_methods: tuple[str, ...] = ()
    abstained: bool
    evidence_ids: tuple[str, ...] = ()
    unresolved_conflicts: tuple[str, ...] = ()
    confidence_interval: tuple[FiniteFloat, FiniteFloat] | None = None
    estimate: FiniteFloat | None = None
    execution_failure: str | None = Field(default=None, min_length=1)
    routing_runtime_seconds: FiniteFloat = Field(ge=0.0)
    inference_runtime_seconds: FiniteFloat = Field(ge=0.0)
    warnings: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_execution(self) -> Self:
        if self.abstained and self.selected_method is not None:
            raise ValueError("abstention cannot select a method")
        if self.confidence_interval is not None:
            lower, upper = self.confidence_interval
            if lower > upper:
                raise ValueError("confidence interval must be ordered")
        return self


class LedgerRecord(BenchmarkModel):
    run_id: str = Field(min_length=1)
    benchmark_version: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    process_family: ProcessFamily
    process_version: str | None = Field(default=None, min_length=1)
    process_parameters: dict[str, JsonValue]
    seed: int
    sample_size: int = Field(ge=2)
    draw_fingerprint: str = Field(min_length=1)
    inference_truth: dict[str, JsonValue]
    target_defined: bool | None = None
    true_mean: FiniteFloat | None = None
    true_standard_deviation: FiniteFloat | None = None
    true_sharpe: FiniteFloat | None = None
    descriptive_full_sample_sharpe: FiniteFloat | None = None
    eligibility_labels: tuple[EligibilityLabel, ...]
    baseline: BaselineName
    selected_method: str | None
    sensitivity_methods: tuple[str, ...]
    abstained: bool
    evidence_ids: tuple[str, ...]
    unresolved_conflicts: tuple[str, ...]
    estimate: FiniteFloat | None = None
    confidence_interval: tuple[FiniteFloat, FiniteFloat] | None
    coverage_applicable: bool | None = None
    covered: bool | None
    interval_width: FiniteFloat | None = Field(default=None, ge=0.0)
    execution_failure: str | None
    routing_runtime_seconds: FiniteFloat = Field(ge=0.0)
    inference_runtime_seconds: FiniteFloat = Field(ge=0.0)
    oracle_method: str = Field(min_length=1)
    oracle_total_loss: FiniteFloat | None = None
    loss_profile: str | None = Field(default=None, min_length=1)
    selected_label: EligibilityStatus | None
    valid_selection: bool
    invalid_selection: bool
    harmful_nonabstention: bool
    unnecessary_abstention: bool
    loss_components: dict[str, FiniteFloat]
    total_loss: FiniteFloat
    regret: FiniteFloat
    warnings: tuple[str, ...]

    @model_validator(mode="after")
    def finite_loss(self) -> Self:
        if not isfinite(self.total_loss) or not isfinite(self.regret):
            raise ValueError("loss and regret must be finite")
        if self.target_defined is False and self.covered is not None:
            raise ValueError("undefined targets cannot have ordinary coverage")
        if self.coverage_applicable is False and self.covered is not None:
            raise ValueError("inapplicable coverage must be null")
        if self.oracle_total_loss is not None:
            expected = (
                0.0
                if self.baseline is BaselineName.ORACLE
                else self.total_loss - self.oracle_total_loss
            )
            if abs(self.regret - expected) > 1e-12:
                raise ValueError("regret must equal selected loss minus oracle loss")
        return self


class OracleChoice(BenchmarkModel):
    scenario_id: str
    method_id: str
    expected_losses: dict[str, FiniteFloat]
    training_seeds: tuple[int, ...]
    tie_break_rule: str


class BenchmarkRunResult(BenchmarkModel):
    run_id: str
    run_directory: Path
    record_count: int = Field(ge=1)
    oracle_choices: tuple[OracleChoice, ...]
    summary: dict[str, JsonValue]
