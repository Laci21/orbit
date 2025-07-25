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
        self.streaming_service = None
        
    def set_streaming_service(self, streaming_service):
        """Set the streaming service reference for manual triggering."""
        self.streaming_service = streaming_service
        
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
            # enqueue_event is synchronous; no need to await
            event_queue.enqueue_event(validation_error)
            return
            
        try:
            # Extract user input using their pattern
            prompt = context.get_user_input()
            
            # Create task if needed
            task = context.current_task
            if not task:
                task = new_task(context.message)
                # enqueue_event is synchronous; no need to await
                event_queue.enqueue_event(task)
            
            # Use LangGraph workflow to process the request
            logger.info(f"Processing request with prompt: {prompt}")
            agent_response = await self.agent.ainvoke(prompt)
            logger.info(f"Agent response: {agent_response} (type: {type(agent_response)})")
            
            # Handle None response
            if agent_response is None:
                agent_response = "Error: Agent returned None response"
                logger.error("Agent ainvoke returned None")
            
            # Check if this is a streaming request and trigger streaming service
            if self.streaming_service and ("stream" in prompt.lower() or "start" in prompt.lower() or "trigger" in prompt.lower()):
                logger.info("Triggering crisis streaming workflow...")
                # Clear any previous final response before starting new crisis
                self.streaming_service.clear_final_response()
                # Start streaming service in background (don't await)
                import asyncio
                try:
                    asyncio.create_task(self.streaming_service.start())
                    agent_response = f"{agent_response} - Crisis streaming initiated!"
                    logger.info("Crisis streaming task created successfully")
                except Exception as e:
                    logger.error(f"Failed to start streaming service: {e}")
                    agent_response = f"{agent_response} - Error starting crisis streaming: {e}"
            
            # Check if this is a status request that should include final response
            elif "status" in prompt.lower():
                if self.streaming_service:
                    final_response = self.streaming_service.get_final_response()
                    if final_response:
                        # Include the final crisis response in the agent response metadata
                        agent_response = f"{agent_response} - Final crisis response available"
                        # We'll attach this in the message metadata below
                    else:
                        agent_response = f"{agent_response} - No final response available yet"
            
            # Create message following Coffee AGNTCY pattern
            message_metadata = {"name": self.agent_card["name"]}
            
            # If we have a final response from streaming service, include it
            if self.streaming_service and "status" in prompt.lower():
                final_response = self.streaming_service.get_final_response()
                if final_response:
                    message_metadata["final_crisis_response"] = final_response
            
            message = Message(
                messageId=str(uuid4()),
                role=Role.agent,
                metadata=message_metadata,
                parts=[Part(TextPart(text=agent_response))]
            )
            
            # Enqueue the response using event_queue
            # enqueue_event is synchronous; no need to await
            event_queue.enqueue_event(message)
                    
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