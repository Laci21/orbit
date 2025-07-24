"""Agent executor for the Ear-to-Ground agent."""

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

from agents.ear_to_ground.agent import EarToGroundAgent
from agents.ear_to_ground.card import AGENT_CARD

logger = logging.getLogger("orbit.ear_to_ground_agent.agent_executor")


class EarToGroundAgentExecutor(AgentExecutor):
    """Agent executor for streaming crisis tweets."""
    
    def __init__(self):
        self.agent = EarToGroundAgent()
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
        """Execute agent request."""
        # Validate request first
        validation_error = self._validate_request(context)
        if validation_error:
            await event_queue.enqueue_event(validation_error)
            return
            
        try:
            # Extract user input using their pattern
            prompt = context.get_user_input()
            
            # Create task if needed
            task = context.current_task
            if not task:
                task = new_task(context.message)
                await event_queue.enqueue_event(task)
            
            # Use LangGraph workflow to process the request
            agent_response = await self.agent.ainvoke(prompt)
            
            # Create message following Coffee AGNTCY pattern
            message = Message(
                messageId=str(uuid4()),
                role=Role.agent,
                metadata={"name": self.agent_card["name"]},
                parts=[Part(TextPart(text=agent_response))]
            )
            
            # Enqueue the response using event_queue
            await event_queue.enqueue_event(message)
                    
        except Exception as e:
            logger.error(f"An error occurred while processing request: {e}")
            raise ServerError(error=InternalError()) from e
            
    async def cancel(
        self, 
        request: RequestContext, 
        event_queue: EventQueue
    ) -> Optional[Task]:
        """Cancel agent execution."""
        raise ServerError(error=UnsupportedOperationError())