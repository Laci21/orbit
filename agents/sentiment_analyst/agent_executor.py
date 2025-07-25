"""Agent executor for the Sentiment Analyst agent."""

import logging
from typing import Optional
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.errors import ServerError
from a2a.types import (
    UnsupportedOperationError,
    JSONRPCResponse,
    ContentTypeNotSupportedError,
    InternalError,
    Message,
    Role,
    TextPart,
    Part,
    Task
)
from a2a.utils import (
    new_task,
)

from agents.sentiment_analyst.agent import SentimentAnalystAgent
from agents.sentiment_analyst.card import AGENT_CARD

logger = logging.getLogger("orbit.sentiment_analyst_agent.agent_executor")


class SentimentAnalystAgentExecutor(AgentExecutor):
    """Agent executor for sentiment analysis of crisis content."""
    
    def __init__(self):
        self.agent = SentimentAnalystAgent()
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)
        
    def _validate_request(self, context: RequestContext) -> Optional[JSONRPCResponse]:
        """Validate incoming request."""
        if not context or not context.message or not context.message.parts:
            logger.error("Invalid request parameters: %s", context)
            return JSONRPCResponse(error=ContentTypeNotSupportedError())
        return None
    
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the agent's logic for sentiment analysis."""
        logger.debug("Received message request: %s", context.message)
        
        # Validate request first
        validation_error = self._validate_request(context)
        if validation_error:
            event_queue.enqueue_event(validation_error)
            return
            
        # Extract user input following lungo pattern
        prompt = context.get_user_input()
        
        # Create task if needed
        task = context.current_task
        if not task:
            task = new_task(context.message)
            event_queue.enqueue_event(task)
            
        try:
            # Simple agent invocation following lungo pattern
            output = await self.agent.ainvoke(prompt)
            
            # Create standard response message
            message = Message(
                messageId=str(uuid4()),
                role=Role.agent,
                metadata={"name": self.agent_card["name"]},
                parts=[Part(TextPart(text=output))]
            )
            
            logger.info("agent output message: %s", message)
            event_queue.enqueue_event(message)
                    
        except Exception as e:
            logger.error(f"An error occurred while processing sentiment analysis: {e}")
            raise ServerError(error=InternalError()) from e
            
    async def cancel(
        self, 
        request: RequestContext, 
        event_queue: EventQueue
    ) -> Optional[Task]:
        """Cancel agent execution."""
        raise ServerError(error=UnsupportedOperationError())