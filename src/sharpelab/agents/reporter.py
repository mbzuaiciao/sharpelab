"""Traceable Report Agent."""

import json
import re

from sharpelab.agents.prompts import role_messages
from sharpelab.agents.provider import TypedProvider
from sharpelab.agents.schemas import AgentRole, ReportOutput
from sharpelab.schemas.evidence import EvidenceItem
from sharpelab.schemas.inference import InferenceResult
from sharpelab.schemas.methods import MethodDecision


class ReportAgent:
    def __init__(self, provider: TypedProvider) -> None:
        self.provider = provider

    def run(self, payload: str) -> ReportOutput:
        return self.provider.generate_typed(
            role=AgentRole.REPORT,
            messages=role_messages(AgentRole.REPORT, payload),
            output_schema=ReportOutput,
        )


def validate_report_traceability(
    report: ReportOutput,
    *,
    evidence: tuple[EvidenceItem, ...],
    results: tuple[InferenceResult, ...],
    decision: MethodDecision,
) -> None:
    """Require references and factual numeric/method claims to match final state."""
    evidence_ids = {item.evidence_id for item in evidence}
    result_ids = {item.inference_id for item in results}
    unknown_evidence = set(report.evidence_references) - evidence_ids
    unknown_results = set(report.result_references) - result_ids
    if unknown_evidence or unknown_results:
        raise ValueError(
            "report contains unknown trace references: "
            f"evidence={sorted(unknown_evidence)}, results={sorted(unknown_results)}"
        )
    if set(report.evidence_references) != evidence_ids:
        raise ValueError(
            "report must reference all final evidence, including conflicts"
        )
    if set(report.result_references) != result_ids:
        raise ValueError("report must reference all deterministic inference results")

    expected_method = decision.selected_method or "deterministic-abstention"
    if report.selected_method != expected_method:
        raise ValueError("report selected method does not match deterministic decision")
    if report.eligibility_explanation != decision.rationale:
        raise ValueError(
            "report eligibility explanation must match deterministic rationale"
        )

    weakened = {
        item.method_id
        for item in decision.eligibility
        if not item.eligible or item.weakened
    }
    missing_method_names = {
        method_id
        for method_id in weakened
        if method_id not in report.rejected_or_weakened_methods
    }
    if missing_method_names:
        raise ValueError(
            "report suppresses rejected or weakened methods: "
            f"{sorted(missing_method_names)}"
        )

    if decision.selected_method is None:
        if results or "abstention" not in report.abstention_or_qualifications.lower():
            raise ValueError("report must preserve deterministic abstention")
        assert decision.abstention is not None
        if any(
            reason not in report.abstention_or_qualifications
            for reason in decision.abstention.reasons
        ):
            raise ValueError("report omits a deterministic abstention reason")
    else:
        selected = next(
            item for item in results if item.method_id == decision.selected_method
        )
        if (
            selected.inference_id not in report.estimate
            or str(selected.estimate) not in report.estimate
        ):
            raise ValueError("report estimate does not match the selected typed result")
        if selected.confidence_interval is not None and any(
            str(value) not in report.uncertainty
            for value in selected.confidence_interval
        ):
            raise ValueError("report interval does not match the selected typed result")

    provenance_warnings = {
        warning
        for item in evidence
        if item.claim == "selection_provenance_complete"
        for warning in item.warnings
    }
    if any(
        warning not in report.provenance_limitations for warning in provenance_warnings
    ):
        raise ValueError("report suppresses a provenance limitation")

    report_text = "\n".join(
        str(value)
        for field, value in report.model_dump().items()
        if field not in {"evidence_references", "result_references"}
    )
    if re.search(
        r"\b(?:bayesian|posterior|causal|causality|outperform|superior|guarantee|skill)\b",
        report_text,
        re.IGNORECASE,
    ):
        raise ValueError(
            "report contains prohibited causal, skill, or posterior language"
        )
    if "deterministic" not in report.audit_trace_summary.lower():
        raise ValueError("report audit summary must identify deterministic authority")

    state_json = json.dumps(
        {
            "evidence": [item.model_dump(mode="json") for item in evidence],
            "results": [item.model_dump(mode="json") for item in results],
            "decision": decision.model_dump(mode="json"),
        },
        sort_keys=True,
    )
    number_pattern = re.compile(
        r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?(?![A-Za-z])"
    )
    allowed_numbers = set(number_pattern.findall(state_json))
    for item in results:
        allowed_numbers.add(f"{item.confidence_level:.0%}".rstrip("%"))
    unsupported_numbers = set(number_pattern.findall(report_text)) - allowed_numbers
    if unsupported_numbers:
        raise ValueError(
            f"report introduces numbers absent from typed state: {unsupported_numbers}"
        )
