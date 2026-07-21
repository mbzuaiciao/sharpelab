"""Deterministic construction of auditable evidence items."""

import hashlib
import json
from typing import Any

import numpy as np
from pydantic import JsonValue

from sharpelab.schemas.evidence import EvidenceFinding, EvidenceItem


def fingerprint_returns(values: np.ndarray[Any, np.dtype[np.float64]]) -> str:
    """Return a stable content fingerprint for float64 returns."""
    contiguous = np.ascontiguousarray(values, dtype=np.dtype("<f8"))
    payload = (
        contiguous.dtype.str.encode()
        + str(contiguous.shape).encode()
        + contiguous.tobytes()
    )
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def make_evidence(
    *,
    claim: str,
    finding: EvidenceFinding,
    diagnostic_name: str,
    sample_size: int | None,
    structured_output: dict[str, JsonValue] | None = None,
    statistic: float | None = None,
    p_value: float | None = None,
    uncertainty: dict[str, JsonValue] | None = None,
    attributes: dict[str, JsonValue] | None = None,
    configuration: dict[str, JsonValue] | None = None,
    assumptions: tuple[str, ...] = (),
    warnings: tuple[str, ...] = (),
    methods_enabled: tuple[str, ...] = (),
    methods_weakened: tuple[str, ...] = (),
    methods_ruled_out: tuple[str, ...] = (),
    does_not_establish: tuple[str, ...] = (),
    data_fingerprint: str | None = None,
    provenance_reference: str | None = None,
) -> EvidenceItem:
    """Build an item whose identifier is stable for identical evidence."""
    item = EvidenceItem(
        evidence_id="pending",
        source=diagnostic_name,
        claim=claim,
        finding=finding,
        diagnostic_name=diagnostic_name,
        diagnostic_version="1.0",
        statistic=statistic,
        structured_output=structured_output or {},
        p_value=p_value,
        uncertainty=uncertainty or {},
        attributes=attributes or {},
        sample_size=sample_size,
        configuration=configuration or {},
        assumptions=assumptions,
        warnings=warnings,
        methods_enabled=methods_enabled,
        methods_weakened=methods_weakened,
        methods_ruled_out=methods_ruled_out,
        does_not_establish=does_not_establish,
        data_fingerprint=data_fingerprint,
        provenance_reference=provenance_reference,
    )
    identity = item.model_dump(
        mode="json", exclude={"evidence_id", "observed_at"}
    )
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:20]
    return item.model_copy(update={"evidence_id": f"evidence:{digest}"})
