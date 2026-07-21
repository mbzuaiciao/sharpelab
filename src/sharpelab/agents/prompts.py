"""Concise role contracts; no hidden reasoning or chain-of-thought requests."""

from sharpelab.agents.schemas import AgentRole, ProviderMessage

ROLE_CONTRACTS: dict[AgentRole, str] = {
    AgentRole.DIAGNOSTIC_PLANNER: (
        "Request only allowlisted diagnostics for unresolved claims. Do not decide "
        "whether a statistical claim is true or calculate statistics."
    ),
    AgentRole.PROVENANCE: (
        "Extract only explicitly supported provenance. Quote exact support, preserve "
        "ambiguity, and never invent counts."
    ),
    AgentRole.SKEPTICAL_REVIEWER: (
        "Cite typed evidence or method metadata for every challenge. Never override "
        "eligibility or select a method."
    ),
    AgentRole.REPORT: (
        "Use only supplied typed state. Do not calculate new values. Distinguish "
        "frequentist PSR from posterior probability and benchmark evidence from "
        "this analysis."
    ),
}


def role_messages(role: AgentRole, payload: str) -> tuple[ProviderMessage, ...]:
    return (
        ProviderMessage(role="system", content=ROLE_CONTRACTS[role]),
        ProviderMessage(role="user", content=payload),
    )
