"""Explicit agent and tool-call budgets."""

from pathlib import Path

import yaml
from pydantic import Field, model_validator

from sharpelab.config import ConfigModel


class AgentBudgets(ConfigModel):
    maximum_diagnostic_requests: int = Field(ge=0)
    maximum_sensitivity_requests: int = Field(ge=0)
    maximum_review_iterations: int = Field(ge=1)
    maximum_model_calls: int = Field(ge=1)
    maximum_repeated_identical_request_count: int = Field(ge=1)


class AgentConfig(ConfigModel):
    mode: str
    timeout_seconds: float = Field(gt=0.0)
    retries: int = Field(ge=0, le=1)
    fallback_to_mock: bool = True
    budgets: AgentBudgets

    @model_validator(mode="after")
    def known_mode(self) -> "AgentConfig":
        if self.mode not in {"mock", "live"}:
            raise ValueError("agent mode must be mock or live")
        return self


class BudgetExceeded(RuntimeError):
    """A monotone workflow budget cannot fund another operation."""


class BudgetLedger:
    def __init__(self, budgets: AgentBudgets) -> None:
        self.budgets = budgets
        self.diagnostic_requests = 0
        self.sensitivity_requests = 0
        self.review_iterations = 0
        self.model_calls = 0
        self.request_counts: dict[str, int] = {}

    def consume_model_call(self) -> None:
        if self.model_calls >= self.budgets.maximum_model_calls:
            raise BudgetExceeded("model-call budget exhausted")
        self.model_calls += 1

    def consume_review_iteration(self) -> None:
        if self.review_iterations >= self.budgets.maximum_review_iterations:
            raise BudgetExceeded("review-iteration budget exhausted")
        self.review_iterations += 1

    def consume_request(self, key: str, *, sensitivity: bool) -> None:
        count = self.request_counts.get(key, 0)
        if count >= self.budgets.maximum_repeated_identical_request_count:
            raise BudgetExceeded(f"repeated request limit reached: {key}")
        if sensitivity:
            if self.sensitivity_requests >= self.budgets.maximum_sensitivity_requests:
                raise BudgetExceeded("sensitivity-request budget exhausted")
            self.sensitivity_requests += 1
        else:
            if self.diagnostic_requests >= self.budgets.maximum_diagnostic_requests:
                raise BudgetExceeded("diagnostic-request budget exhausted")
            self.diagnostic_requests += 1
        self.request_counts[key] = count + 1

    def snapshot(self) -> dict[str, object]:
        return {
            "diagnostic_requests": self.diagnostic_requests,
            "sensitivity_requests": self.sensitivity_requests,
            "review_iterations": self.review_iterations,
            "model_calls": self.model_calls,
            "request_counts": dict(sorted(self.request_counts.items())),
        }


def load_agent_config(path: Path) -> AgentConfig:
    raw: object = yaml.safe_load(path.read_text("utf-8"))
    return AgentConfig.model_validate(raw)
