"""Agent executor for the Legal Counsel agent."""

import asyncio
import json
import logging
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

from agents.legal_counsel.agent import LegalCounselAgent
from agents.legal_counsel.card import AGENT_CARD
from agents.legal_counsel.config import LegalCounselConfig

logger = logging.getLogger("orbit.legal_counsel_agent.agent_executor")


class LegalCounselAgentExecutor(AgentExecutor):
    """Agent executor for legal review of crisis content."""
    
    def __init__(self):
        self.agent = LegalCounselAgent()
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)
        self.config = LegalCounselConfig()
        
    def _validate_request(self, context: RequestContext) -> JSONRPCResponse | None:
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
        """Execute the agent's logic for legal review."""
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
            # Check if this is a legal review request from fact checker
            if "Please review the legal implications of this crisis based on fact checking results:" in prompt:
                # Extract fact checking analysis from the prompt
                content_start = prompt.find("Please review the legal implications of this crisis based on fact checking results:") + len("Please review the legal implications of this crisis based on fact checking results:")
                fact_analysis = prompt[content_start:].strip()
                
                # Perform legal review
                legal_result = await self.agent.analyze_legal_implications(fact_analysis)
                
                # Create response with legal review results
                response_text = f"Legal review completed. " \
                               f"Legal risk: {legal_result.get('legal_risk', 'unknown')}, " \
                               f"Escalation needed: {legal_result.get('escalation_needed', False)}, " \
                               f"Compliance issues: {len(legal_result.get('compliance_issues', []))}"
                
                # Store legal result for potential future use
                message = Message(
                    messageId=str(uuid4()),
                    role=Role.agent,
                    metadata={
                        "name": self.agent_card["name"],
                        "legal_review": legal_result,
                        "crisis_id": "extracted_from_prompt"  # Could be enhanced to extract actual crisis ID
                    },
                    parts=[Part(TextPart(text=response_text))]
                )
            else:
                # Regular workflow processing for general queries
                output = await self.agent.ainvoke(prompt)
                
                # Create standard response message
                message = Message(
                    messageId=str(uuid4()),
                    role=Role.agent,
                    metadata={"name": self.agent_card["name"]},
                    parts=[Part(TextPart(text=output))]
                )
            
            event_queue.enqueue_event(message)
                    
        except Exception as e:
            logger.error(f"An error occurred while processing legal review: {e}")
            raise ServerError(error=InternalError()) from e
    
    async def cancel(
        self, 
        request: RequestContext, 
        event_queue: EventQueue
    ) -> Task | None:
        """Cancel agent execution."""
        raise ServerError(error=UnsupportedOperationError()) 