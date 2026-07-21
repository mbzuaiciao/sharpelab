"""Strict Phase 2 diagnostic, routing, and experiment configuration."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

IMPLEMENTED_METHOD_IDS = frozenset(
    {
        "iid-gaussian-sharpe",
        "mertens-psr",
        "hac-sharpe",
        "circular-block-bootstrap",
    }
)


class ConfigModel(BaseModel):
    """Immutable configuration with unknown-key rejection."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class DataQualityConfig(ConfigModel):
    minimum_sample_size: int = Field(ge=2)
    near_zero_variance: FiniteFloat = Field(gt=0.0)
    repeated_value_warning_fraction: FiniteFloat = Field(gt=0.0, lt=1.0)
    extreme_concentration_fraction: FiniteFloat = Field(gt=0.0, lt=1.0)
    irregular_spacing_cv: FiniteFloat = Field(gt=0.0)


class DependenceConfig(ConfigModel):
    lags: tuple[int, ...] = Field(min_length=1)
    significance_level: FiniteFloat = Field(gt=0.0, lt=1.0)
    practical_autocorrelation: FiniteFloat = Field(gt=0.0, lt=1.0)
    minimum_sample_size: int = Field(ge=3)

    @model_validator(mode="after")
    def validate_lags(self) -> "DependenceConfig":
        if any(lag < 1 for lag in self.lags):
            raise ValueError("dependence lags must be positive")
        if len(self.lags) != len(set(self.lags)):
            raise ValueError("dependence lags must be unique")
        if self.lags != tuple(sorted(self.lags)):
            raise ValueError("dependence lags must be strictly increasing")
        if max(self.lags) >= self.minimum_sample_size:
            raise ValueError(
                "maximum dependence lag must be below the minimum sample size"
            )
        return self


class DistributionConfig(ConfigModel):
    significance_level: FiniteFloat = Field(gt=0.0, lt=1.0)
    material_absolute_skewness: FiniteFloat = Field(gt=0.0)
    heavy_tail_raw_kurtosis: FiniteFloat = Field(gt=3.0)
    minimum_sample_size: int = Field(ge=4)


class StabilityConfig(ConfigModel):
    split_fraction: FiniteFloat = Field(gt=0.1, lt=0.9)
    material_mean_z: FiniteFloat = Field(gt=0.0)
    material_variance_ratio: FiniteFloat = Field(gt=1.0)
    minimum_sample_size: int = Field(ge=4)
    minimum_segment_size: int = Field(ge=2)

    @model_validator(mode="after")
    def validate_segment_sizes(self) -> "StabilityConfig":
        if self.minimum_sample_size < 2 * self.minimum_segment_size:
            raise ValueError(
                "stability minimum sample size must cover two minimum segments"
            )
        split = int(self.minimum_sample_size * self.split_fraction)
        if (
            split < self.minimum_segment_size
            or self.minimum_sample_size - split < self.minimum_segment_size
        ):
            raise ValueError(
                "stability split fraction must satisfy both minimum segment sizes "
                "at the minimum sample size"
            )
        return self


class DiagnosticsConfig(ConfigModel):
    data_quality: DataQualityConfig
    linear_dependence: DependenceConfig
    squared_dependence: DependenceConfig
    distribution: DistributionConfig
    stability: StabilityConfig


class RoutingConfig(ConfigModel):
    method_priority: tuple[str, ...] = Field(min_length=1)
    iid_gaussian_minimum_sample: int = Field(ge=2)
    mertens_minimum_sample: int = Field(ge=4)
    hac_minimum_sample: int = Field(ge=3)
    bootstrap_minimum_sample: int = Field(ge=3)
    abstain_on_structural_instability: bool

    @model_validator(mode="after")
    def validate_priority(self) -> "RoutingConfig":
        if len(self.method_priority) != len(set(self.method_priority)):
            raise ValueError("method priority entries must be unique")
        if frozenset(self.method_priority) != IMPLEMENTED_METHOD_IDS:
            raise ValueError(
                "method priority must contain every implemented method exactly once"
            )
        return self


class ExperimentConfig(ConfigModel):
    benchmark_sharpe: FiniteFloat
    confidence_level: FiniteFloat = Field(gt=0.0, lt=1.0)
    hac_bandwidth: int = Field(ge=0)
    bootstrap_block_length: int = Field(ge=1)
    bootstrap_replications: int = Field(ge=2)
    bootstrap_seed: int
    claim_requires_selection_provenance: bool


class Phase2Config(ConfigModel):
    diagnostics: DiagnosticsConfig
    routing: RoutingConfig
    experiment: ExperimentConfig


def load_yaml_model[ModelT: ConfigModel](
    path: Path, model_type: type[ModelT]
) -> ModelT:
    """Load one YAML file into an unknown-key-rejecting typed model."""
    if not path.is_file():
        raise FileNotFoundError(f"configuration file is missing: {path}")
    raw: object = yaml.safe_load(path.read_text("utf-8"))
    return model_type.model_validate(raw)


def load_phase2_config(config_root: Path) -> Phase2Config:
    """Load the three explicit Phase 2 configuration files."""
    root = config_root.resolve()
    diagnostics = load_yaml_model(root / "diagnostics/default.yaml", DiagnosticsConfig)
    routing = load_yaml_model(root / "routing/conservative.yaml", RoutingConfig)
    experiment = load_yaml_model(
        root / "experiments/phase2-smoke.yaml", ExperimentConfig
    )
    return Phase2Config(
        diagnostics=diagnostics,
        routing=routing,
        experiment=experiment,
    )
