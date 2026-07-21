"""Deterministic semantic validation for schema-valid agent outputs."""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from sharpelab.agents.schemas import (
    DiagnosticRequest,
    PlannerOutput,
    ReportOutput,
    ReviewerOutput,
)

SEMANTIC_VALIDATOR_VERSION = "phase4d-planner-semantic-validator-v1"
ALIAS_REGISTRY_VERSION = "phase4d-planner-alias-registry-v1"
RESERVED_TOKEN_REGISTRY_VERSION = "phase4d-reserved-token-registry-v1"


class SemanticModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class OutputValidationStatus(StrEnum):
    SCHEMA_VALID_SEMANTIC_VALID = "schema-valid-semantically-valid"
    SCHEMA_VALID_SEMANTIC_INVALID = "schema-valid-semantically-invalid"
    SCHEMA_INVALID = "schema-invalid"
    PROVIDER_FAILURE = "provider-failure"


class SemanticFailureCategory(StrEnum):
    UNKNOWN_DIAGNOSTIC_ID = "unknown-diagnostic-id"
    INVALID_DIAGNOSTIC_CONFIGURATION = "invalid-diagnostic-configuration"
    DUPLICATE_DIAGNOSTIC_REQUEST = "duplicate-diagnostic-request"
    INVALID_EVIDENCE_REFERENCE = "invalid-evidence-reference"
    MALFORMED_RESERVED_TOKEN_TEXT = "malformed-reserved-token-text"
    UNSUPPORTED_RATIONALE_CONTENT = "unsupported-rationale-content"
    SEMANTIC_VALIDATION_FAILED = "semantic-validation-failed"


class DiagnosticPermission(SemanticModel):
    request_visible_id: str = Field(min_length=1)
    canonical_id: str = Field(min_length=1)
    configuration_ids: tuple[str, ...] = Field(min_length=1)


class PlannerSemanticContext(SemanticModel):
    permissions: tuple[DiagnosticPermission, ...]
    allowed_evidence_references: tuple[str, ...]
    alias_registry_version: Literal["phase4d-planner-alias-registry-v1"] = (
        ALIAS_REGISTRY_VERSION
    )


class IdentifierMapping(SemanticModel):
    original_id: str
    normalized_id: str
    canonical_id: str | None
    alias_applied: bool


class OffendingConfiguration(SemanticModel):
    diagnostic_id: str
    configuration_id: str
    allowed_configuration_ids: tuple[str, ...]


class ReservedTokenDetection(SemanticModel):
    field_path: str
    pattern_name: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    redacted_preview: str = Field(max_length=160)


class TextValidationResult(SemanticModel):
    valid: bool
    registry_version: Literal["phase4d-reserved-token-registry-v1"] = (
        RESERVED_TOKEN_REGISTRY_VERSION
    )
    detections: tuple[ReservedTokenDetection, ...]


class PlannerSemanticValidationResult(SemanticModel):
    validator_version: Literal["phase4d-planner-semantic-validator-v1"] = (
        SEMANTIC_VALIDATOR_VERSION
    )
    alias_registry_version: Literal["phase4d-planner-alias-registry-v1"] = (
        ALIAS_REGISTRY_VERSION
    )
    reserved_token_registry_version: Literal["phase4d-reserved-token-registry-v1"] = (
        RESERVED_TOKEN_REGISTRY_VERSION
    )
    source_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    schema_validation: Literal["passed"] = "passed"
    allowlist_validation: Literal["passed", "failed"]
    malformed_text_validation: Literal["passed", "failed"]
    overall_status: OutputValidationStatus
    valid: bool
    failure_categories: tuple[SemanticFailureCategory, ...]
    offending_ids: tuple[str, ...]
    offending_configurations: tuple[OffendingConfiguration, ...]
    request_visible_allowed_ids: tuple[str, ...]
    allowed_ids: tuple[str, ...]
    normalized_mappings: tuple[IdentifierMapping, ...]
    evidence_references: tuple[str, ...]
    invalid_evidence_references: tuple[str, ...]
    text_detections: tuple[ReservedTokenDetection, ...]
    normalized_output: PlannerOutput | None
    redacted_proposal: dict[str, JsonValue]
    safe_summary: str = Field(min_length=1, max_length=1_000)


class ProbeDSemanticRetrospective(SemanticModel):
    schema_version: Literal["phase4d-probe-d-semantic-retrospective-v1"] = (
        "phase4d-probe-d-semantic-retrospective-v1"
    )
    classification: Literal["derived-diagnostic-infrastructure-only"] = (
        "derived-diagnostic-infrastructure-only"
    )
    source_artifact: str
    source_artifact_sha256: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    source_artifact_preserved: Literal[True] = True
    validator_version: Literal["phase4d-planner-semantic-validator-v1"] = (
        SEMANTIC_VALIDATOR_VERSION
    )
    derived_at: datetime
    result: PlannerSemanticValidationResult


PLANNER_ALIASES: Mapping[str, str] = {
    "linear-dependence": "return-dependence",
    "squared-dependence": "squared-return-dependence",
    "distribution": "distribution-diagnostic",
    "stability": "stability-diagnostic",
}


_RESERVED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "openai-reserved-control-token",
        re.compile(r"<\|[^<>\r\n]{1,128}\|>"),
    ),
    (
        "gemma-turn-control-token",
        re.compile(r"<(?:start|end)_of_turn>"),
    ),
    (
        "llama-instruction-control-token",
        re.compile(r"\[/?INST\]|<<\/?SYS>>"),
    ),
    (
        "raw-chat-role-marker",
        re.compile(r"(?m)^\s*<(?:assistant|system|tool|user)>\s*$"),
    ),
    (
        "chat-template-delimiter",
        re.compile(
            r"(?:\{\{|\{%)[^}\r\n]{0,120}"
            r"(?:assistant|system|tool|message|bos_token|eos_token)"
            r"[^}\r\n]{0,120}(?:\}\}|%\})",
            re.IGNORECASE,
        ),
    ),
    ("tokenizer-replacement-character", re.compile("\ufffd")),
)


def normalize_identifier(value: str) -> str:
    """Apply conservative comparison normalization without inventing aliases."""
    return unicodedata.normalize("NFKC", value).strip().casefold()


def registered_alias_target(value: str) -> str | None:
    return PLANNER_ALIASES.get(normalize_identifier(value))


def planner_output_fingerprint(output: PlannerOutput) -> str:
    payload = json.dumps(
        output.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return f"sha256:{sha256(payload).hexdigest()}"


def classify_output_validation(
    *,
    provider_failed: bool,
    schema_valid: bool,
    semantic_result: PlannerSemanticValidationResult | None,
) -> OutputValidationStatus:
    if provider_failed:
        return OutputValidationStatus.PROVIDER_FAILURE
    if not schema_valid:
        return OutputValidationStatus.SCHEMA_INVALID
    if semantic_result is None or not semantic_result.valid:
        return OutputValidationStatus.SCHEMA_VALID_SEMANTIC_INVALID
    return OutputValidationStatus.SCHEMA_VALID_SEMANTIC_VALID


def validate_planner_output(
    output: PlannerOutput,
    context: PlannerSemanticContext,
) -> PlannerSemanticValidationResult:
    permissions = {item.canonical_id: item for item in context.permissions}
    visible_allowed = tuple(item.request_visible_id for item in context.permissions)
    allowed = tuple(item.canonical_id for item in context.permissions)
    allowed_evidence = set(context.allowed_evidence_references)
    mappings: list[IdentifierMapping] = []
    offending_ids: list[str] = []
    bad_configurations: list[OffendingConfiguration] = []
    evidence_references: list[str] = []
    invalid_evidence: list[str] = []
    normalized_requests: list[DiagnosticRequest] = []
    seen: set[tuple[str, str]] = set()
    duplicate = False

    for request in output.requested_diagnostics:
        normalized = normalize_identifier(request.diagnostic_id)
        alias = PLANNER_ALIASES.get(normalized)
        canonical = alias or normalized
        permission = permissions.get(canonical)
        mappings.append(
            IdentifierMapping(
                original_id=request.diagnostic_id,
                normalized_id=normalized,
                canonical_id=canonical if permission is not None else None,
                alias_applied=alias is not None,
            )
        )
        if permission is None:
            offending_ids.append(request.diagnostic_id)
        elif request.configuration_id not in permission.configuration_ids:
            bad_configurations.append(
                OffendingConfiguration(
                    diagnostic_id=canonical,
                    configuration_id=request.configuration_id,
                    allowed_configuration_ids=permission.configuration_ids,
                )
            )
        key = (canonical, request.configuration_id)
        if key in seen:
            duplicate = True
        seen.add(key)
        for reference in request.unresolved_claims:
            evidence_references.append(reference)
            if reference not in allowed_evidence:
                invalid_evidence.append(reference)
        normalized_requests.append(
            request.model_copy(update={"diagnostic_id": canonical})
        )

    text_result = validate_agent_output_text(output)
    categories: list[SemanticFailureCategory] = []
    if offending_ids:
        categories.append(SemanticFailureCategory.UNKNOWN_DIAGNOSTIC_ID)
    if bad_configurations:
        categories.append(SemanticFailureCategory.INVALID_DIAGNOSTIC_CONFIGURATION)
    if duplicate:
        categories.append(SemanticFailureCategory.DUPLICATE_DIAGNOSTIC_REQUEST)
    if invalid_evidence:
        categories.append(SemanticFailureCategory.INVALID_EVIDENCE_REFERENCE)
    if not text_result.valid:
        categories.append(SemanticFailureCategory.MALFORMED_RESERVED_TOKEN_TEXT)
    if not output.requested_diagnostics and not output.stop_recommendation:
        categories.append(SemanticFailureCategory.SEMANTIC_VALIDATION_FAILED)

    categories = list(dict.fromkeys(categories))
    valid = not categories
    normalized_output = (
        output.model_copy(update={"requested_diagnostics": tuple(normalized_requests)})
        if valid
        else None
    )
    return PlannerSemanticValidationResult(
        source_fingerprint=planner_output_fingerprint(output),
        allowlist_validation=(
            "passed"
            if not offending_ids
            and not bad_configurations
            and not duplicate
            and not invalid_evidence
            else "failed"
        ),
        malformed_text_validation="passed" if text_result.valid else "failed",
        overall_status=(
            OutputValidationStatus.SCHEMA_VALID_SEMANTIC_VALID
            if valid
            else OutputValidationStatus.SCHEMA_VALID_SEMANTIC_INVALID
        ),
        valid=valid,
        failure_categories=tuple(categories),
        offending_ids=tuple(dict.fromkeys(offending_ids)),
        offending_configurations=tuple(bad_configurations),
        request_visible_allowed_ids=visible_allowed,
        allowed_ids=allowed,
        normalized_mappings=tuple(mappings),
        evidence_references=tuple(dict.fromkeys(evidence_references)),
        invalid_evidence_references=tuple(dict.fromkeys(invalid_evidence)),
        text_detections=text_result.detections,
        normalized_output=normalized_output,
        redacted_proposal=_redacted_planner(output),
        safe_summary=(
            "Planner output passed request-scoped allowlist, reference, "
            "configuration, duplicate, and reserved-token validation."
            if valid
            else "Planner output was schema-valid but rejected before tool execution: "
            + ", ".join(item.value for item in categories)
        ),
    )


def validate_agent_output_text(
    output: PlannerOutput | ReviewerOutput | ReportOutput,
) -> TextValidationResult:
    fields: list[tuple[str, str]] = []
    if isinstance(output, PlannerOutput):
        fields.append(("rationale", output.rationale))
        fields.extend(
            (f"requested_diagnostics[{index}].rationale", item.rationale)
            for index, item in enumerate(output.requested_diagnostics)
        )
    elif isinstance(output, ReviewerOutput):
        fields.append(("rationale", output.rationale))
        fields.extend(
            (f"supported_challenges[{index}].statement", item.statement)
            for index, item in enumerate(output.supported_challenges)
        )
        fields.extend(
            (f"unresolved_contradictions[{index}]", item)
            for index, item in enumerate(output.unresolved_contradictions)
        )
    else:
        for name in (
            "estimate",
            "eligibility_explanation",
            "rejected_or_weakened_methods",
            "uncertainty",
            "sensitivity_findings",
            "provenance_limitations",
            "abstention_or_qualifications",
            "audit_trace_summary",
        ):
            fields.append((name, cast(str, getattr(output, name))))
    detections: list[ReservedTokenDetection] = []
    for field_path, text in fields:
        detections.extend(_detect_reserved_tokens(field_path, text))
    ordered = sorted(
        detections, key=lambda item: (item.field_path, item.start, item.pattern_name)
    )
    return TextValidationResult(valid=not ordered, detections=tuple(ordered))


def semantic_audit_record(
    result: PlannerSemanticValidationResult,
) -> dict[str, object]:
    """Produce an audit-safe semantic layer record with no model reasoning text."""
    return {
        "event_type": "planner-semantic-validation",
        "transport_status": "success",
        "schema_validation_status": "passed",
        "semantic_validation_status": result.overall_status.value,
        "semantic_failure_categories": [
            item.value for item in result.failure_categories
        ],
        "semantic_validation": result.model_dump(mode="json"),
    }


def attach_semantic_audit(
    provider: object, result: PlannerSemanticValidationResult
) -> None:
    records = getattr(provider, "audit_records", None)
    if not isinstance(records, list) or not records:
        return
    items = cast(list[object], records)
    last_value = items[-1]
    if not isinstance(last_value, dict):
        return
    last = cast(dict[str, object], last_value)
    last.update(semantic_audit_record(result))


def attach_text_semantic_audit(
    provider: object,
    result: TextValidationResult,
    *,
    role: str,
) -> None:
    records = getattr(provider, "audit_records", None)
    if not isinstance(records, list) or not records:
        return
    items = cast(list[object], records)
    last_value = items[-1]
    if not isinstance(last_value, dict):
        return
    last = cast(dict[str, object], last_value)
    last.update(
        {
            "event_type": "agent-text-semantic-validation",
            "transport_status": "success",
            "schema_validation_status": "passed",
            "semantic_validation_status": (
                OutputValidationStatus.SCHEMA_VALID_SEMANTIC_VALID.value
                if result.valid
                else OutputValidationStatus.SCHEMA_VALID_SEMANTIC_INVALID.value
            ),
            "semantic_role": role,
            "reserved_token_registry_version": result.registry_version,
            "text_detections": [
                item.model_dump(mode="json") for item in result.detections
            ],
        }
    )


def retrospective_record(
    *,
    source_artifact: str,
    source_artifact_sha256: str,
    result: PlannerSemanticValidationResult,
    derived_at: datetime | None = None,
) -> ProbeDSemanticRetrospective:
    return ProbeDSemanticRetrospective(
        source_artifact=source_artifact,
        source_artifact_sha256=source_artifact_sha256,
        derived_at=derived_at or datetime.now(UTC),
        result=result,
    )


def _detect_reserved_tokens(
    field_path: str, text: str
) -> tuple[ReservedTokenDetection, ...]:
    detections: list[ReservedTokenDetection] = []
    occupied: list[tuple[int, int]] = []
    for name, pattern in _RESERVED_PATTERNS:
        for match in pattern.finditer(text):
            occupied.append((match.start(), match.end()))
            detections.append(
                ReservedTokenDetection(
                    field_path=field_path,
                    pattern_name=name,
                    start=match.start(),
                    end=match.end(),
                    redacted_preview=_redacted_preview(
                        text, match.start(), match.end()
                    ),
                )
            )
    for delimiter, name in (
        ("<|", "unmatched-open-reserved-delimiter"),
        ("|>", "unmatched-close-reserved-delimiter"),
    ):
        start = 0
        while (index := text.find(delimiter, start)) >= 0:
            if not any(left <= index < right for left, right in occupied):
                end = index + len(delimiter)
                detections.append(
                    ReservedTokenDetection(
                        field_path=field_path,
                        pattern_name=name,
                        start=index,
                        end=end,
                        redacted_preview=_redacted_preview(text, index, end),
                    )
                )
            start = index + len(delimiter)
    for index, character in enumerate(text):
        codepoint = ord(character)
        if (codepoint < 32 and character not in "\t\n\r") or 127 <= codepoint <= 159:
            detections.append(
                ReservedTokenDetection(
                    field_path=field_path,
                    pattern_name="disallowed-control-character",
                    start=index,
                    end=index + 1,
                    redacted_preview=_redacted_preview(text, index, index + 1),
                )
            )
    return tuple(detections)


def _redacted_preview(text: str, start: int, end: int) -> str:
    left = max(0, start - 24)
    right = min(len(text), end + 24)
    prefix = text[left:start].encode("unicode_escape").decode("ascii")
    suffix = text[end:right].encode("unicode_escape").decode("ascii")
    return (
        ("..." if left else "")
        + prefix
        + "[CONTROL]"
        + suffix
        + ("..." if right < len(text) else "")
    )


def _redacted_planner(output: PlannerOutput) -> dict[str, JsonValue]:
    return {
        "requested_diagnostics": [
            {
                "diagnostic_id": item.diagnostic_id,
                "configuration_id": item.configuration_id,
                "rationale": "[REDACTED_MODEL_TEXT]",
                "unresolved_claims": list(item.unresolved_claims),
                "priority": item.priority,
                "expected_information_gain": item.expected_information_gain.value,
            }
            for item in output.requested_diagnostics
        ],
        "rationale": "[REDACTED_MODEL_TEXT]",
        "stop_recommendation": output.stop_recommendation,
    }
