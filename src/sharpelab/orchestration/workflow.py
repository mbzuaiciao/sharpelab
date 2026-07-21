"""Plain-Python Phase 4A workflow with deterministic final authority."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from datetime import datetime
from hashlib import sha256

from pydantic import BaseModel

from sharpelab.agents.mock import MockRawProvider
from sharpelab.agents.planner import DiagnosticPlannerAgent
from sharpelab.agents.provenance import ProvenanceAgent, validate_provenance_support
from sharpelab.agents.provider import (
    EnvironmentLiveProvider,
    ProviderError,
    TypedProvider,
    ValidatingProvider,
    provider_audit_records,
)
from sharpelab.agents.reporter import ReportAgent, validate_report_traceability
from sharpelab.agents.reviewer import SkepticalReviewerAgent
from sharpelab.agents.schemas import (
    PlannerOutput,
    ProvenanceOutput,
    ReportOutput,
    ReviewerOutput,
)
from sharpelab.agents.semantic_validation import (
    validate_agent_output_text,
    validate_planner_output,
)
from sharpelab.config import Phase2Config
from sharpelab.data.returns import ReturnInput
from sharpelab.diagnostics.provenance import ResearchProvenance
from sharpelab.diagnostics.registry import run_diagnostics
from sharpelab.orchestration.adjudicator import (
    TOOL_REGISTRY,
    DeterministicAdjudicator,
    build_planner_semantic_context,
)
from sharpelab.orchestration.audit import AuditTrail
from sharpelab.orchestration.budgets import AgentConfig, BudgetExceeded, BudgetLedger
from sharpelab.orchestration.state import AgenticWorkflowState, RejectedProposal
from sharpelab.routing.router import route_methods
from sharpelab.schemas.evidence import EvidenceItem
from sharpelab.schemas.inference import InferenceResult
from sharpelab.schemas.methods import MethodDecision
from sharpelab.workflows.deterministic import run_inference_method


def _json_payload(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _require_clean_agent_text(
    output: PlannerOutput | ReviewerOutput | ReportOutput,
    audit: AuditTrail,
    *,
    actor: str,
) -> None:
    result = validate_agent_output_text(output)
    audit.append(
        "agent-text-semantic-validation",
        "deterministic-semantic-validator",
        {
            "actor": actor,
            "status": "passed" if result.valid else "failed",
            "registry_version": result.registry_version,
            "detections": [item.model_dump(mode="json") for item in result.detections],
        },
    )
    if not result.valid:
        raise ProviderError(
            f"{actor} returned schema-valid malformed reserved-token text"
        )


def _default_provider(config: AgentConfig) -> TypedProvider:
    raw = (
        MockRawProvider()
        if config.mode == "mock"
        else EnvironmentLiveProvider(timeout_seconds=config.timeout_seconds)
    )
    return ValidatingProvider(raw, allow_repair=config.retries == 1)


def _mock_provider(config: AgentConfig) -> TypedProvider:
    return ValidatingProvider(MockRawProvider(), allow_repair=config.retries == 1)


def _consume_model_call(
    budget: BudgetLedger, audit: AuditTrail, *, actor: str, provider_source: str
) -> None:
    before = budget.snapshot()
    try:
        budget.consume_model_call()
    except BudgetExceeded:
        audit.append(
            "budget-rejected",
            actor,
            {
                "budget_type": "model-call",
                "provider_source": provider_source,
                "budget_before": before,
                "budget_after": budget.snapshot(),
            },
        )
        raise
    audit.append(
        "budget-consumed",
        actor,
        {
            "budget_type": "model-call",
            "provider_source": provider_source,
            "budget_before": before,
            "budget_after": budget.snapshot(),
        },
    )


def _consume_review_iteration(
    budget: BudgetLedger, audit: AuditTrail, *, actor: str
) -> None:
    before = budget.snapshot()
    try:
        budget.consume_review_iteration()
    except BudgetExceeded:
        audit.append(
            "budget-rejected",
            actor,
            {
                "budget_type": "review-iteration",
                "budget_before": before,
                "budget_after": budget.snapshot(),
            },
        )
        raise
    audit.append(
        "budget-consumed",
        actor,
        {
            "budget_type": "review-iteration",
            "budget_before": before,
            "budget_after": budget.snapshot(),
        },
    )


def _flush_provider_records(
    provider: TypedProvider,
    audit: AuditTrail,
    *,
    provider_source: str,
    provider_mode: str,
    cursors: dict[str, int],
) -> None:
    records = provider_audit_records(provider)
    start = cursors.get(provider_source, 0)
    for record in records[start:]:
        audit.append(
            "provider-response",
            "provider-adapter",
            {
                "provider_mode": provider_mode,
                "provider_source": provider_source,
                "fallback": provider_source == "fallback",
                **record,
            },
        )
    cursors[provider_source] = len(records)


def _run_agent_call[AgentOutputT: BaseModel](
    *,
    actor: str,
    primary: TypedProvider,
    fallback: TypedProvider,
    provider_mode: str,
    fallback_to_mock: bool,
    budget: BudgetLedger,
    audit: AuditTrail,
    cursors: dict[str, int],
    run: Callable[[TypedProvider], AgentOutputT],
    validate: Callable[[AgentOutputT], None] | None = None,
) -> tuple[AgentOutputT, bool]:
    try:
        _consume_model_call(budget, audit, actor=actor, provider_source="primary")
        try:
            output = run(primary)
            if validate is not None:
                validate(output)
        finally:
            _flush_provider_records(
                primary,
                audit,
                provider_source="primary",
                provider_mode=provider_mode,
                cursors=cursors,
            )
    except BudgetExceeded as error:
        raise ProviderError(f"{actor} stopped safely: {error}") from error
    except (ProviderError, ValueError) as error:
        audit.append(
            "agent-output-rejected",
            actor,
            {
                "status": "rejected",
                "provider_source": "primary",
                "reason": str(error),
            },
        )
        if not fallback_to_mock:
            raise ProviderError(
                f"{actor} provider failed and mock fallback is disabled"
            ) from error
        try:
            _consume_model_call(budget, audit, actor=actor, provider_source="fallback")
            try:
                output = run(fallback)
                if validate is not None:
                    validate(output)
            finally:
                _flush_provider_records(
                    fallback,
                    audit,
                    provider_source="fallback",
                    provider_mode="mock",
                    cursors=cursors,
                )
        except (BudgetExceeded, ProviderError, ValueError) as fallback_error:
            audit.append(
                "fallback-failed",
                actor,
                {"status": "rejected", "reason": str(fallback_error)},
            )
            raise ProviderError(
                f"{actor} mock fallback failed safely"
            ) from fallback_error
        audit.append(
            "fallback-accepted",
            actor,
            {
                "status": "accepted",
                "provider_source": "fallback",
                "output": output.model_dump(mode="json"),
            },
        )
        return output, True
    audit.append(
        "agent-output-accepted",
        actor,
        {
            "status": "accepted",
            "provider_source": "primary",
            "output": output.model_dump(mode="json"),
        },
    )
    return output, False


def _execute_decision(
    decision: MethodDecision,
    *,
    returns: ReturnInput,
    config: Phase2Config,
    evidence: tuple[EvidenceItem, ...],
    extra_methods: tuple[str, ...] = (),
    include_decision_sensitivities: bool = True,
) -> tuple[InferenceResult, ...]:
    if decision.selected_method is None:
        return ()
    eligible = {item.method_id for item in decision.eligibility if item.eligible}
    method_ids = tuple(
        dict.fromkeys(
            (
                decision.selected_method,
                *(
                    decision.sensitivity_methods
                    if include_decision_sensitivities
                    else ()
                ),
                *(item for item in extra_methods if item in eligible),
            )
        )
    )
    fingerprint = next(
        (item.data_fingerprint for item in evidence if item.data_fingerprint), None
    )
    provenance_reference = next(
        (item.provenance_reference for item in evidence if item.provenance_reference),
        None,
    )
    return tuple(
        run_inference_method(
            method_id,
            returns,
            config,
            data_fingerprint=fingerprint,
            provenance_reference=provenance_reference,
        )
        for method_id in method_ids
    )


def run_agentic_workflow(
    returns: ReturnInput,
    phase2_config: Phase2Config,
    agent_config: AgentConfig,
    *,
    provenance_text: str = "",
    timestamps: Sequence[datetime | None] | None = None,
    example_id: str | None = None,
    input_frequency: str = "per-period",
    provider: TypedProvider | None = None,
) -> AgenticWorkflowState:
    """Run agents above deterministic diagnostics, eligibility, and inference."""
    audit = AuditTrail()
    budget = BudgetLedger(agent_config.budgets)
    primary = provider or _default_provider(agent_config)
    fallback = _mock_provider(agent_config)
    rejected: list[RejectedProposal] = []
    accepted: list[str] = []
    provider_cursors: dict[str, int] = {}
    fallback_used = False

    audit.append(
        "workflow-started",
        "orchestrator",
        {
            "provider_mode": agent_config.mode,
            "example_id": example_id or "user-input",
            "input_frequency": input_frequency,
            "fallback_to_mock": agent_config.fallback_to_mock,
            "configured_budgets": agent_config.budgets.model_dump(mode="json"),
        },
    )

    provenance_output: ProvenanceOutput | None = None
    proposed_provenance: ResearchProvenance | None = None
    audit.append(
        "agent-input",
        "provenance",
        {
            "input_character_count": len(provenance_text),
            "input_sha256": sha256(provenance_text.encode()).hexdigest(),
            "schema": "ProvenanceOutput",
        },
    )
    try:
        provenance_output, used_fallback = _run_agent_call(
            actor="provenance",
            primary=primary,
            fallback=fallback,
            provider_mode=agent_config.mode,
            fallback_to_mock=agent_config.fallback_to_mock,
            budget=budget,
            audit=audit,
            cursors=provider_cursors,
            run=lambda selected_provider: ProvenanceAgent(selected_provider).run(
                provenance_text
            ),
            validate=lambda output: validate_provenance_support(
                provenance_text, output
            ),
        )
        fallback_used = fallback_used or used_fallback
        proposed_provenance = provenance_output.proposed_provenance
    except ProviderError as error:
        rejected.append(
            RejectedProposal(
                proposal_type="provenance",
                proposal_id="provenance-output",
                reason=str(error),
            )
        )
        audit.append(
            "provenance-safe-failure",
            "provenance",
            {"status": "rejected", "reason": str(error)},
        )

    evidence = run_diagnostics(
        returns,
        phase2_config.diagnostics,
        timestamps=timestamps,
        provenance=proposed_provenance,
    )
    audit.append(
        "deterministic-diagnostics-completed",
        "deterministic-core",
        {
            "status": "completed",
            "evidence_ids": [item.evidence_id for item in evidence],
        },
    )
    unresolved_claims = sorted(
        {
            item.claim
            for item in evidence
            if item.finding.value not in {"support", "supports"}
        }
    )

    planner_tool_ids = tuple(
        item.tool_id for item in TOOL_REGISTRY.values() if item.kind == "diagnostic"
    )
    planner_payload = _json_payload(
        {
            "evidence": [item.model_dump(mode="json") for item in evidence],
            "available_diagnostics": [
                {"tool_id": item.tool_id, "description": item.description}
                for item in TOOL_REGISTRY.values()
                if item.kind == "diagnostic"
            ],
            "unresolved_claims": unresolved_claims,
            "budget_state": budget.snapshot(),
            "remaining_diagnostic_budget": max(
                0,
                agent_config.budgets.maximum_diagnostic_requests
                - budget.diagnostic_requests,
            ),
        }
    )
    audit.append(
        "agent-input",
        "diagnostic-planner",
        {
            "evidence_ids": [item.evidence_id for item in evidence],
            "unresolved_claims": unresolved_claims,
            "tool_ids": sorted(planner_tool_ids),
            "budget_state": budget.snapshot(),
            "schema": "PlannerOutput",
        },
    )
    planner_output, used_fallback = _run_agent_call(
        actor="diagnostic-planner",
        primary=primary,
        fallback=fallback,
        provider_mode=agent_config.mode,
        fallback_to_mock=agent_config.fallback_to_mock,
        budget=budget,
        audit=audit,
        cursors=provider_cursors,
        run=lambda selected_provider: DiagnosticPlannerAgent(selected_provider).run(
            planner_payload
        ),
    )
    fallback_used = fallback_used or used_fallback
    planner_semantic = validate_planner_output(
        planner_output,
        build_planner_semantic_context(
            planner_tool_ids,
            allowed_evidence_references=unresolved_claims,
        ),
    )

    adjudicator = DeterministicAdjudicator(budget, audit)
    evidence, planner_accepted, planner_rejected = adjudicator.execute_planner_requests(
        planner_output,
        semantic_validation=planner_semantic,
        returns=returns,
        config=phase2_config,
        provenance=proposed_provenance,
        evidence=evidence,
        timestamps=timestamps,
    )
    accepted.extend(planner_accepted)
    rejected.extend(planner_rejected)

    initial_decision = route_methods(
        evidence, phase2_config.routing, phase2_config.experiment
    )
    initial_results = _execute_decision(
        initial_decision,
        returns=returns,
        config=phase2_config,
        evidence=evidence,
        include_decision_sensitivities=False,
    )
    audit.append(
        "initial-route",
        "deterministic-core",
        {
            "status": "completed",
            "route_stage": "initial",
            "evidence_ids": [item.evidence_id for item in evidence],
            "decision": initial_decision.model_dump(mode="json"),
            "result_ids": [item.inference_id for item in initial_results],
        },
    )

    review_payload = _json_payload(
        {
            "evidence": [item.model_dump(mode="json") for item in evidence],
            "decision": initial_decision.model_dump(mode="json"),
            "results": [item.model_dump(mode="json") for item in initial_results],
            "available_sensitivity_methods": sorted(
                item.method_id for item in initial_decision.eligibility if item.eligible
            ),
        }
    )
    audit.append(
        "agent-input",
        "skeptical-reviewer",
        {
            "evidence_ids": [item.evidence_id for item in evidence],
            "selected_method": initial_decision.selected_method,
            "result_ids": [item.inference_id for item in initial_results],
            "eligible_method_ids": sorted(
                item.method_id for item in initial_decision.eligibility if item.eligible
            ),
            "budget_state": budget.snapshot(),
            "schema": "ReviewerOutput",
        },
    )
    try:
        _consume_review_iteration(budget, audit, actor="skeptical-reviewer")
    except BudgetExceeded as error:
        raise ProviderError(f"skeptical-reviewer stopped safely: {error}") from error
    reviewer_output, used_fallback = _run_agent_call(
        actor="skeptical-reviewer",
        primary=primary,
        fallback=fallback,
        provider_mode=agent_config.mode,
        fallback_to_mock=agent_config.fallback_to_mock,
        budget=budget,
        audit=audit,
        cursors=provider_cursors,
        run=lambda selected_provider: SkepticalReviewerAgent(selected_provider).run(
            review_payload
        ),
    )
    fallback_used = fallback_used or used_fallback
    _require_clean_agent_text(reviewer_output, audit, actor="skeptical-reviewer")
    audit.append(
        "review-recommendation-recorded",
        "deterministic-adjudicator",
        {
            "recommendation": reviewer_output.recommendation.value,
            "status": "advisory",
        },
    )
    review_accepted, review_rejected = adjudicator.validate_review(
        reviewer_output, evidence=evidence, decision=initial_decision
    )
    accepted.extend(review_accepted)
    rejected.extend(review_rejected)

    final_decision = route_methods(
        evidence, phase2_config.routing, phase2_config.experiment
    )
    final_results = _execute_decision(
        final_decision,
        returns=returns,
        config=phase2_config,
        evidence=evidence,
        extra_methods=review_accepted,
    )
    audit.append(
        "final-deterministic-decision",
        "deterministic-core",
        {
            "status": "completed",
            "route_stage": "final",
            "evidence_ids": [item.evidence_id for item in evidence],
            "decision": final_decision.model_dump(mode="json"),
            "result_ids": [item.inference_id for item in final_results],
        },
    )

    report_payload = _json_payload(
        {
            "evidence": [item.model_dump(mode="json") for item in evidence],
            "decision": final_decision.model_dump(mode="json"),
            "results": [item.model_dump(mode="json") for item in final_results],
            "review": reviewer_output.model_dump(mode="json"),
        }
    )
    audit.append(
        "agent-input",
        "report",
        {
            "evidence_ids": [item.evidence_id for item in evidence],
            "selected_method": final_decision.selected_method,
            "result_ids": [item.inference_id for item in final_results],
            "rejected_proposal_ids": [item.proposal_id for item in rejected],
            "schema": "ReportOutput",
        },
    )
    report, used_fallback = _run_agent_call(
        actor="report",
        primary=primary,
        fallback=fallback,
        provider_mode=agent_config.mode,
        fallback_to_mock=agent_config.fallback_to_mock,
        budget=budget,
        audit=audit,
        cursors=provider_cursors,
        run=lambda selected_provider: ReportAgent(selected_provider).run(
            report_payload
        ),
        validate=lambda output: validate_report_traceability(
            output,
            evidence=evidence,
            results=final_results,
            decision=final_decision,
        ),
    )
    fallback_used = fallback_used or used_fallback
    _require_clean_agent_text(report, audit, actor="report")

    data_fingerprint = next(
        (item.data_fingerprint for item in evidence if item.data_fingerprint), None
    )
    sample_size = next(
        (item.sample_size for item in evidence if item.sample_size is not None), None
    )
    audit.append(
        "workflow-completed",
        "orchestrator",
        {
            "status": "completed",
            "provider_mode": agent_config.mode,
            "fallback_used": fallback_used,
            "evidence_ids": [item.evidence_id for item in evidence],
            "result_ids": [item.inference_id for item in final_results],
            "selected_method": final_decision.selected_method,
            "abstained": final_decision.selected_method is None,
            "accepted_proposal_ids": accepted,
            "rejected_proposal_ids": [item.proposal_id for item in rejected],
            "budget_usage": budget.snapshot(),
        },
    )

    return AgenticWorkflowState(
        mode=agent_config.mode,
        example_id=example_id,
        input_frequency=input_frequency,
        input_sample_size=sample_size,
        input_data_fingerprint=data_fingerprint,
        fallback_used=fallback_used,
        evidence=evidence,
        provenance_output=provenance_output,
        planner_output=planner_output,
        planner_semantic_validation=planner_semantic,
        initial_decision=initial_decision,
        reviewer_output=reviewer_output,
        final_decision=final_decision,
        inference_results=final_results,
        report=report,
        rejected_proposals=tuple(rejected),
        accepted_agent_requests=tuple(accepted),
        budget_usage=budget.snapshot(),
        audit_events=tuple(audit.events),
    )
