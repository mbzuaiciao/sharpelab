"""Diagnostic Planner Agent."""

from sharpelab.agents.prompts import role_messages
from sharpelab.agents.provider import TypedProvider
from sharpelab.agents.schemas import AgentRole, PlannerOutput


class DiagnosticPlannerAgent:
    def __init__(self, provider: TypedProvider) -> None:
        self.provider = provider

    def run(self, payload: str) -> PlannerOutput:
        return self.provider.generate_typed(
            role=AgentRole.DIAGNOSTIC_PLANNER,
            messages=role_messages(AgentRole.DIAGNOSTIC_PLANNER, payload),
            output_schema=PlannerOutput,
        )
