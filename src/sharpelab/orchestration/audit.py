"""Deterministic audit events with recursive secret redaction."""

from typing import cast

from pydantic import BaseModel, ConfigDict, Field

from sharpelab.agents.provider import redact_secrets


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    event_id: str = Field(pattern=r"^audit:\d{4,}$")
    sequence: int = Field(ge=1)
    event_type: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    payload: dict[str, object]


class AuditTrail:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, event_type: str, actor: str, payload: dict[str, object]) -> None:
        redacted = redact_secrets(payload)
        if not isinstance(redacted, dict):
            raise TypeError("audit payload redaction must preserve dictionaries")
        typed_payload = cast(dict[str, object], redacted)
        self.events.append(
            AuditEvent(
                event_id=f"audit:{len(self.events) + 1:04d}",
                sequence=len(self.events) + 1,
                event_type=event_type,
                actor=actor,
                payload=typed_payload,
            )
        )
