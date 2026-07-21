"""Render complete Phase 4A audit artifacts without changing typed state."""

from __future__ import annotations

import json
from pathlib import Path

from sharpelab.orchestration.state import AgenticWorkflowState


def render_report_markdown(state: AgenticWorkflowState) -> str:
    report = state.report
    accepted = ", ".join(state.accepted_agent_requests) or "None."
    rejected = (
        "; ".join(
            f"{item.proposal_id}: {item.reason}" for item in state.rejected_proposals
        )
        or "None."
    )
    result_summary = (
        "; ".join(
            f"{item.method_id} ({item.inference_id}) estimate={item.estimate}"
            for item in state.inference_results
        )
        or "No deterministic method result was issued."
    )
    return "\n".join(
        (
            "# Evidence-Routed Agentic Analysis",
            "",
            (
                "> Statistical calculations and final eligibility decisions are "
                "deterministic."
            ),
            "",
            f"> Agent mode: **{state.mode}**; mock fallback used: "
            f"**{str(state.fallback_used).lower()}**.",
            "",
            "## Input summary",
            "",
            f"- Example: `{state.example_id or 'user-input'}`",
            f"- Observations: `{state.input_sample_size}`",
            f"- Declared frequency: `{state.input_frequency}`",
            f"- Data fingerprint: `{state.input_data_fingerprint}`",
            "",
            "## Agent requests and adjudication",
            "",
            "- Planner stop recommendation: "
            f"`{state.planner_output.stop_recommendation}`",
            f"- Accepted requests: {accepted}",
            f"- Rejected proposals: {rejected}",
            "- Reviewer recommendation: "
            f"`{state.reviewer_output.recommendation.value}`",
            "",
            "## Deterministic route",
            "",
            f"- Initial: `{state.initial_decision.selected_method or 'abstain'}`",
            f"- Final: `{state.final_decision.selected_method or 'abstain'}`",
            f"- Results: {result_summary}",
            "",
            "## Estimate",
            "",
            report.estimate,
            "",
            "## Selected method",
            "",
            report.selected_method,
            "",
            "## Why it is eligible",
            "",
            report.eligibility_explanation,
            "",
            "## Rejected or weakened methods",
            "",
            report.rejected_or_weakened_methods,
            "",
            "## Uncertainty",
            "",
            report.uncertainty,
            "",
            "## Sensitivity findings",
            "",
            report.sensitivity_findings,
            "",
            "## Provenance limitations",
            "",
            report.provenance_limitations,
            "",
            "## Abstention or qualifications",
            "",
            report.abstention_or_qualifications,
            "",
            "## Audit trace summary",
            "",
            report.audit_trace_summary,
            "",
            "## Budget usage",
            "",
            f"`{json.dumps(state.budget_usage, sort_keys=True)}`",
            "",
        )
    )


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", "utf-8")


def write_demo_artifacts(
    state: AgenticWorkflowState, output_directory: Path
) -> tuple[Path, ...]:
    output_directory.mkdir(parents=True, exist_ok=False)
    artifacts = {
        "final_report.md": render_report_markdown(state),
        "final_state.json": state.model_dump(mode="json"),
        "evidence.json": [item.model_dump(mode="json") for item in state.evidence],
        "agent_requests.json": {
            "planner": state.planner_output.model_dump(mode="json"),
            "reviewer": state.reviewer_output.model_dump(mode="json"),
            "accepted": list(state.accepted_agent_requests),
            "rejected": [
                item.model_dump(mode="json") for item in state.rejected_proposals
            ],
        },
        "deterministic_decision.json": state.final_decision.model_dump(mode="json"),
        "method_results.json": [
            item.model_dump(mode="json") for item in state.inference_results
        ],
    }
    written: list[Path] = []
    for name, value in artifacts.items():
        path = output_directory / name
        if isinstance(value, str):
            path.write_text(value, "utf-8")
        else:
            _write_json(path, value)
        written.append(path)
    audit_path = output_directory / "audit_log.jsonl"
    audit_path.write_text(
        "".join(item.model_dump_json() + "\n" for item in state.audit_events),
        "utf-8",
    )
    written.append(audit_path)
    return tuple(written)
