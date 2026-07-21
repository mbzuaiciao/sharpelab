"""Abstention decision contracts."""

from typing import Self

from pydantic import model_validator

from sharpelab.schemas._base import SchemaModel


class AbstentionDecision(SchemaModel):
    """A decision to proceed or abstain, including evidence gaps."""

    abstain: bool
    reasons: tuple[str, ...] = ()
    missing_evidence: tuple[str, ...] = ()

    @model_validator(mode="after")
    def explain_abstention(self) -> Self:
        """Require non-blank reasons whenever inference is declined."""
        if self.abstain and not self.reasons:
            raise ValueError("abstention requires at least one reason")
        if any(not reason.strip() for reason in self.reasons):
            raise ValueError("abstention reasons must not be blank")
        if any(not item.strip() for item in self.missing_evidence):
            raise ValueError("missing evidence descriptions must not be blank")
        return self

