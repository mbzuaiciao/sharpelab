"""Deterministic primary-method selection policy."""

from sharpelab.config import RoutingConfig
from sharpelab.schemas.methods import MethodEligibility


def select_primary(
    eligibility: tuple[MethodEligibility, ...], config: RoutingConfig
) -> str | None:
    """Choose the first non-sensitivity eligible method in configured priority."""
    entries = {item.method_id: item for item in eligibility}
    for method_id in config.method_priority:
        candidate = entries.get(method_id)
        if (
            candidate is not None
            and candidate.eligible
            and not candidate.sensitivity_only
        ):
            return method_id
    return None
