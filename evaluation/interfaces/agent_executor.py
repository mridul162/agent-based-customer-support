from app.agents.support_agent import SupportAgent
from app.schemas.agent import AgentResponse

from evaluation.interfaces.conversation_executor import (
    ConversationExecutor,
)


class SupportAgentExecutor(ConversationExecutor):
    """Adapter exposing SupportAgent to the evaluation framework."""

    def __init__(self, agent: SupportAgent):
        self.agent = agent

    def execute(
        self,
        *,
        customer_id: str,
        message: str,
    ) -> AgentResponse:

        return self.agent.handle_message(
            customer_id=customer_id,
            message=message,
        )