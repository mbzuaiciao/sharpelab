"""Provider-neutral typed generation with bounded repair and redacted audit."""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Sequence
from typing import Protocol, TypeVar, cast

from pydantic import BaseModel, ValidationError

from sharpelab.agents.schemas import AgentRole, ProviderMessage

ModelT = TypeVar("ModelT", bound=BaseModel)
SECRET_KEY = re.compile(r"(api[_-]?key|token|secret|password)", re.IGNORECASE)


class ProviderError(RuntimeError):
    """A provider could not return a valid typed output safely."""


class RawProvider(Protocol):
    def generate_raw(
        self,
        *,
        role: AgentRole,
        messages: Sequence[ProviderMessage],
        schema_name: str,
        repair_error: str | None,
    ) -> object: ...


class TypedProvider(Protocol):
    def generate_typed(
        self,
        *,
        role: AgentRole,
        messages: Sequence[ProviderMessage],
        output_schema: type[ModelT],
    ) -> ModelT: ...


def redact_secrets(value: object) -> object:
    """Recursively redact common credential fields and bearer-like strings."""
    if isinstance(value, dict):
        mapping = cast(dict[object, object], value)
        return {
            str(key): "[REDACTED]"
            if SECRET_KEY.search(str(key))
            else redact_secrets(item)
            for key, item in mapping.items()
        }
    if isinstance(value, (list, tuple)):
        items = cast(Sequence[object], value)
        return [redact_secrets(item) for item in items]
    if isinstance(value, str):
        redacted = re.sub(
            r"(?i)(bearer\s+|sk-[a-z0-9_-]{8,})[a-z0-9._-]*",
            "[REDACTED]",
            value,
        )
        for key, secret in os.environ.items():
            if SECRET_KEY.search(key) and len(secret) >= 4:
                redacted = redacted.replace(secret, "[REDACTED]")
        return redacted
    return value


class ValidatingProvider:
    """Validate raw provider output, allowing at most one repair attempt."""

    def __init__(self, raw_provider: RawProvider, *, allow_repair: bool = True) -> None:
        self._raw_provider = raw_provider
        self._allow_repair = allow_repair
        self.audit_records: list[dict[str, object]] = []

    def generate_typed(
        self,
        *,
        role: AgentRole,
        messages: Sequence[ProviderMessage],
        output_schema: type[ModelT],
    ) -> ModelT:
        repair_error: str | None = None
        attempts = 2 if self._allow_repair else 1
        for attempt in range(attempts):
            raw = self._raw_provider.generate_raw(
                role=role,
                messages=messages,
                schema_name=output_schema.__name__,
                repair_error=repair_error,
            )
            self.audit_records.append(
                {
                    "role": role.value,
                    "attempt": attempt + 1,
                    "raw_response": redact_secrets(raw),
                }
            )
            try:
                if isinstance(raw, str):
                    return output_schema.model_validate_json(raw)
                return output_schema.model_validate(raw)
            except ValidationError as error:
                repair_error = str(error)
        raise ProviderError(
            f"provider returned malformed {output_schema.__name__} after "
            f"{attempts} attempt(s)"
        )


class EnvironmentLiveProvider:
    """Optional live adapter shell with environment-only configuration.

    A transport is injected by an application that deliberately installs a
    provider SDK. The default project has no network dependency and therefore
    fails safely without one.
    """

    def __init__(
        self,
        transport: Callable[[str, str, Sequence[ProviderMessage], float], object]
        | None = None,
        *,
        timeout_seconds: float = 20.0,
    ) -> None:
        self.model = os.getenv("ERI_AGENT_MODEL", "")
        self.api_key = os.getenv("ERI_AGENT_API_KEY", "")
        self.timeout_seconds = timeout_seconds
        self._transport = transport

    def generate_raw(
        self,
        *,
        role: AgentRole,
        messages: Sequence[ProviderMessage],
        schema_name: str,
        repair_error: str | None,
    ) -> object:
        if not self.model or not self.api_key or self._transport is None:
            raise ProviderError(
                "live provider unavailable; set ERI_AGENT_MODEL and ERI_AGENT_API_KEY "
                "and inject an explicit provider transport"
            )
        prompt = f"role={role.value}; schema={schema_name}"
        if repair_error is not None:
            prompt += "; repair the prior schema-invalid response"
        return self._transport(self.model, prompt, messages, self.timeout_seconds)


def provider_audit_records(provider: TypedProvider) -> tuple[dict[str, object], ...]:
    records: object = getattr(provider, "audit_records", ())
    if not isinstance(records, (list, tuple)):
        return ()
    items = cast(Sequence[object], records)
    return tuple(
        cast(dict[str, object], item) for item in items if isinstance(item, dict)
    )
