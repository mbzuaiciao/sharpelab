"""Deterministic scripted provider used by tests and demo fallback."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import cast

from sharpelab.agents.provenance import extract_unambiguous_count
from sharpelab.agents.schemas import AgentRole, ProviderMessage


def _object_dict(value: object) -> dict[str, object]:
    return cast(dict[str, object], value) if isinstance(value, dict) else {}


def _object_list(state: dict[str, object], key: str) -> list[dict[str, object]]:
    value = state.get(key, [])
    if not isinstance(value, list):
        return []
    items = cast(list[object], value)
    return [cast(dict[str, object], item) for item in items if isinstance(item, dict)]


def _string_items(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in cast(list[object], value))


class MockRawProvider:
    """Produce typed-role dictionaries from typed state, without a network."""

    def generate_raw(
        self,
        *,
        role: AgentRole,
        messages: Sequence[ProviderMessage],
        schema_name: str,
        repair_error: str | None,
    ) -> object:
        del schema_name, repair_error
        payload = messages[-1].content
        if role is AgentRole.PROVENANCE:
            return self._provenance(payload)
        state = cast(dict[str, object], json.loads(payload))
        if role is AgentRole.DIAGNOSTIC_PLANNER:
            return self._planner(state)
        if role is AgentRole.SKEPTICAL_REVIEWER:
            return self._reviewer(state)
        if role is AgentRole.REPORT:
            return self._report(state)
        raise AssertionError(f"unsupported mock role: {role}")

    @staticmethod
    def _provenance(prose: str) -> dict[str, object]:
        if prose == "No provenance supplied.":
            return {
                "proposed_provenance": {"completeness": "missing"},
                "source_support": [],
                "confidence": "low",
                "unresolved_fields": [
                    "trials",
                    "parameter_searches",
                    "markets_or_universes",
                    "start_dates_or_windows",
                    "failed_trials_retained",
                    "trial_dependence_known",
                ],
                "questions_for_user": [
                    "How many strategies or trials were evaluated?",
                    "Were unsuccessful trials retained?",
                ],
            }
        trial_support = extract_unambiguous_count(prose, "trials")
        trials = trial_support[0] if trial_support else None
        supports: list[dict[str, str]] = []
        if trial_support:
            supports.append({"field_name": "trials", "exact_excerpt": trial_support[1]})
        unresolved = [
            "parameter_searches",
            "markets_or_universes",
            "start_dates_or_windows",
            "failed_trials_retained",
            "trial_dependence_known",
        ]
        if trials is None:
            unresolved.insert(0, "trials")
        proposed: dict[str, object] = {
            "trials": trials,
            "completeness": "partial" if trials is not None else "missing",
        }
        if trials is not None:
            proposed["reference"] = "agent-proposal:provenance"
        return {
            "proposed_provenance": proposed,
            "source_support": supports,
            "confidence": "medium" if trials is not None else "low",
            "unresolved_fields": unresolved,
            "questions_for_user": [
                "Which universes and windows were searched?",
                "Were failed trials retained and are trials dependent?",
            ],
        }

    @staticmethod
    def _planner(state: dict[str, object]) -> dict[str, object]:
        evidence = _object_list(state, "evidence")
        requests: list[dict[str, object]] = []
        claims = {str(item.get("claim")): item for item in evidence}
        squared = claims.get("absence_of_squared_return_dependence", {})
        stability = claims.get("structural_stability", {})
        if squared.get("finding") in {"contradicts", "contradiction"}:
            requests.append(
                {
                    "diagnostic_id": "squared-return-dependence",
                    "rationale": (
                        "Squared-return dependence is material to IID eligibility."
                    ),
                    "unresolved_claims": ["absence_of_squared_return_dependence"],
                    "priority": 1,
                    "expected_information_gain": "high",
                }
            )
        if stability.get("finding") in {"contradicts", "contradiction"}:
            requests.append(
                {
                    "diagnostic_id": "stability-diagnostic",
                    "rationale": (
                        "Instability controls whether a stable full-sample claim "
                        "is allowed."
                    ),
                    "unresolved_claims": ["structural_stability"],
                    "priority": 1,
                    "expected_information_gain": "high",
                }
            )
        return {
            "requested_diagnostics": requests,
            "rationale": (
                "Request only diagnostics tied to material unresolved evidence."
                if requests
                else "Existing typed evidence is sufficient for deterministic routing."
            ),
            "stop_recommendation": not requests,
        }

    @staticmethod
    def _reviewer(state: dict[str, object]) -> dict[str, object]:
        evidence = _object_list(state, "evidence")
        decision = _object_dict(state.get("decision", {}))
        selected = decision.get("selected_method")
        squared_refs = [
            str(item["evidence_id"])
            for item in evidence
            if item.get("claim") == "absence_of_squared_return_dependence"
            and item.get("finding") in {"contradicts", "contradiction"}
        ]
        stability_refs = [
            str(item["evidence_id"])
            for item in evidence
            if item.get("claim") == "structural_stability"
            and item.get("finding") in {"contradicts", "contradiction"}
        ]
        if selected is None:
            return {
                "supported_challenges": [
                    {
                        "challenge_id": "challenge:instability",
                        "statement": (
                            "A stable full-sample inferential target is not defensible."
                        ),
                        "evidence_references": stability_refs
                        or [str(evidence[0]["evidence_id"])],
                    }
                ],
                "recommendation": "abstain-or-qualify",
                "rationale": (
                    "Preserve deterministic abstention under material instability."
                ),
            }
        if squared_refs:
            return {
                "supported_challenges": [
                    {
                        "challenge_id": "challenge:squared-dependence",
                        "statement": (
                            "IID-only inference must not be primary under volatility "
                            "clustering."
                        ),
                        "evidence_references": squared_refs,
                        "method_ids": ["iid-gaussian-sharpe", "mertens-psr"],
                    }
                ],
                "requested_sensitivity_methods": ["circular-block-bootstrap"],
                "recommendation": "run-sensitivity-methods",
                "rationale": (
                    "Request an eligible dependence-aware sensitivity analysis."
                ),
            }
        return {
            "recommendation": "accept",
            "rationale": (
                "No evidence-referenced challenge changes deterministic eligibility."
            ),
        }

    @staticmethod
    def _report(state: dict[str, object]) -> dict[str, object]:
        decision = _object_dict(state.get("decision", {}))
        results = _object_list(state, "results")
        evidence = _object_list(state, "evidence")
        selected = decision.get("selected_method")
        selected_result = next(
            (item for item in results if item.get("method_id") == selected), None
        )
        if selected_result is None:
            estimate = "No inferential estimate was issued."
            uncertainty = "No ordinary interval applies because the workflow abstained."
        else:
            estimate = (
                "Per-period estimate from typed result "
                f"{selected_result['inference_id']}: {selected_result['estimate']}."
            )
            interval = selected_result.get("confidence_interval")
            level_value = selected_result.get("confidence_level", 0.95)
            level = (
                float(level_value) if isinstance(level_value, (int, float)) else 0.95
            )
            uncertainty = (
                f"Typed {level:.0%} interval: {interval}."
                if interval is not None
                else (
                    "The typed result reports uncertainty without a confidence "
                    "interval."
                )
            )
        eligibility_value = decision.get("eligibility", [])
        eligibility_items = (
            cast(list[object], eligibility_value)
            if isinstance(eligibility_value, list)
            else []
        )
        eligibility = (
            [
                cast(dict[str, object], item)
                for item in eligibility_items
                if isinstance(item, dict)
            ]
            if eligibility_items
            else []
        )
        rejected = [
            str(item.get("method_id"))
            for item in eligibility
            if not item.get("eligible") or item.get("weakened")
        ]
        provenance_items = [
            item
            for item in evidence
            if item.get("claim") == "selection_provenance_complete"
        ]
        sensitivity_summaries = [
            (
                f"{item['method_id']} ({item['inference_id']}) estimate "
                f"{item['estimate']}"
            )
            for item in results
            if item.get("method_id") != selected
        ]
        abstention_value = decision.get("abstention")
        abstention = (
            cast(dict[str, object], abstention_value)
            if isinstance(abstention_value, dict)
            else {}
        )
        abstention_reasons = _string_items(abstention.get("reasons", []))
        return {
            "estimate": estimate,
            "selected_method": str(selected or "deterministic-abstention"),
            "eligibility_explanation": str(decision.get("rationale")),
            "rejected_or_weakened_methods": (
                ", ".join(rejected) if rejected else "None recorded."
            ),
            "uncertainty": uncertainty,
            "sensitivity_findings": (
                "Typed deterministic sensitivity results: "
                + "; ".join(sensitivity_summaries)
                if sensitivity_summaries
                else "No additional deterministic sensitivity result was requested."
            ),
            "provenance_limitations": (
                "; ".join(
                    warning
                    for item in provenance_items
                    for warning in _string_items(item.get("warnings", []))
                )
                or "No additional provenance limitation was recorded."
            ),
            "abstention_or_qualifications": (
                "Deterministic abstention is final: " + "; ".join(abstention_reasons)
                if selected is None
                else (
                    "This analysis is distinct from preliminary Phase 3B "
                    "benchmark evidence."
                )
            ),
            "audit_trace_summary": (
                "Agent proposals were validated and deterministic routing remained "
                "final authority."
            ),
            "evidence_references": [str(item["evidence_id"]) for item in evidence],
            "result_references": [str(item["inference_id"]) for item in results],
        }


class SequenceRawProvider:
    """Small deterministic fixture provider for repair and failure tests."""

    def __init__(self, responses: Sequence[object]) -> None:
        self.responses = list(responses)
        self.calls = 0

    def generate_raw(
        self,
        *,
        role: AgentRole,
        messages: Sequence[ProviderMessage],
        schema_name: str,
        repair_error: str | None,
    ) -> object:
        del role, messages, schema_name, repair_error
        index = min(self.calls, len(self.responses) - 1)
        self.calls += 1
        return self.responses[index]
