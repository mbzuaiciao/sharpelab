"""Skeptical Reviewer Agent."""

from sharpelab.agents.prompts import role_messages
from sharpelab.agents.provider import TypedProvider
from sharpelab.agents.schemas import AgentRole, ReviewerOutput


class SkepticalReviewerAgent:
    def __init__(self, provider: TypedProvider) -> None:
        self.provider = provider

    def run(self, payload: str) -> ReviewerOutput:
        return self.provider.generate_typed(
            role=AgentRole.SKEPTICAL_REVIEWER,
            messages=role_messages(AgentRole.SKEPTICAL_REVIEWER, payload),
            output_schema=ReviewerOutput,
        )
