"""Framework-independent routing evaluation hooks."""

from collections.abc import Iterable

from sharpelab.schemas.methods import MethodDecision


def routing_metrics(
    decisions: Iterable[MethodDecision], oracle_valid_methods: Iterable[set[str]]
) -> dict[str, float]:
    """Compute simple benchmark rates for paired decisions and oracle labels."""
    pairs = list(zip(decisions, oracle_valid_methods, strict=True))
    if not pairs:
        raise ValueError("at least one routing decision is required")
    selected = [decision.selected_method for decision, _ in pairs]
    valid = [
        method is not None and method in oracle
        for method, (_, oracle) in zip(selected, pairs, strict=True)
    ]
    invalid = [
        method is not None and method not in oracle
        for method, (_, oracle) in zip(selected, pairs, strict=True)
    ]
    abstained = [method is None for method in selected]
    unnecessary = [
        is_abstained and bool(oracle)
        for is_abstained, (_, oracle) in zip(abstained, pairs, strict=True)
    ]
    count = float(len(pairs))
    return {
        "valid_method_selection_rate": sum(valid) / count,
        "invalid_method_selection_rate": sum(invalid) / count,
        "abstention_rate": sum(abstained) / count,
        "unnecessary_abstention_rate": sum(unnecessary) / count,
        "oracle_agreement_rate": sum(valid) / count,
    }


def evidence_completeness(decision: MethodDecision) -> float:
    total = len(decision.eligibility)
    return (
        0.0
        if total == 0
        else sum(bool(item.evidence_references) for item in decision.eligibility)
        / total
    )


def routing_consistency(decisions: Iterable[MethodDecision]) -> float:
    selected = [decision.selected_method for decision in decisions]
    if not selected:
        raise ValueError("at least one routing decision is required")
    return max(selected.count(value) for value in set(selected)) / len(selected)
