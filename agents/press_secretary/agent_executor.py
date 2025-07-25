"""Agent executor for the Press Secretary agent."""

import asyncio
import json
import logging
from typing import Any
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

from agents.press_secretary.agent import PressSecretaryAgent
from agents.press_secretary.card import AGENT_CARD
from agents.press_secretary.config import PressSecretaryConfig

logger = logging.getLogger("orbit.press_secretary_agent.agent_executor")


class PressSecretaryAgentExecutor(AgentExecutor):
    """Agent executor for generating crisis response statements."""
    
    def __init__(self):
        self.agent = PressSecretaryAgent()
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)
        self.config = PressSecretaryConfig()
        
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
        """Execute the agent's logic for crisis response generation."""
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
            # Check if this is a crisis response generation request
            if "Please generate official crisis response" in prompt:
                # Parse the comprehensive crisis data
                crisis_data = self._extract_crisis_data_from_prompt(prompt)
                
                if crisis_data:
                    # Extract all agent outputs
                    sentiment_analysis = crisis_data.get("sentiment_analysis", {})
                    fact_analysis = crisis_data.get("fact_analysis", {})  
                    risk_assessment = crisis_data.get("risk_assessment", {})
                    legal_review = crisis_data.get("legal_review", {})
                    original_crisis = crisis_data.get("crisis_data", {})
                    
                    # Generate comprehensive crisis response
                    press_result = await self.agent.generate_crisis_response(
                        original_crisis, sentiment_analysis, fact_analysis, 
                        risk_assessment, legal_review
                    )
                    
                    # Create response message with press response
                    response_message = self._create_response_message(
                        press_result, crisis_data.get("crisis_id", "unknown")
                    )
                    event_queue.enqueue_event(response_message)
                else:
                    logger.error("Failed to extract crisis data from prompt")
                    error_message = self._create_error_message("Invalid crisis data format")
                    event_queue.enqueue_event(error_message)
            
            else:
                # Regular workflow processing for general queries
                output = await self.agent.ainvoke(prompt)
                
                # Create standard response message
                response_message = Message(
                    messageId=str(uuid4()),
                    role=Role.agent,
                    parts=[TextPart(text=output)],
                    metadata={
                        "name": "Orbit Press Secretary",
                        "agent_type": "press_secretary",
                        "status": "completed"
                    }
                )
                event_queue.enqueue_event(response_message)
                
        except Exception as e:
            logger.error(f"An error occurred while processing press response: {e}")
            error_message = self._create_error_message(str(e))
            event_queue.enqueue_event(error_message)
    
    def _extract_crisis_data_from_prompt(self, prompt: str) -> dict[str, Any] | None:
        """Extract comprehensive crisis data from the A2A request prompt."""
        try:
            # Look for JSON data in the prompt
            start_marker = "CRISIS_DATA:"
            end_marker = "END_CRISIS_DATA"
            
            if start_marker in prompt and end_marker in prompt:
                start_idx = prompt.find(start_marker) + len(start_marker)
                end_idx = prompt.find(end_marker)
                crisis_json = prompt[start_idx:end_idx].strip()
                
                crisis_data = json.loads(crisis_json)
                logger.info(f"Extracted crisis data for ID: {crisis_data.get('crisis_id', 'unknown')}")
                return crisis_data
            
            logger.warning("No crisis data markers found in prompt")
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse crisis JSON data: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting crisis data: {e}")
            return None
    
    def _create_response_message(self, press_result: dict[str, Any], crisis_id: str) -> Message:
        """Create structured response message with press response."""
        # Create the response text
        response_text = (
            f"Crisis response generated successfully. "
            f"Primary tone: {press_result.get('tone', 'unknown')}, "
            f"Confidence: {press_result.get('confidence', 0):.2f}, "
            f"Channels: {len(press_result.get('channels', {}))}"
        )
        
        return Message(
            messageId=str(uuid4()),
            role=Role.agent,
            parts=[TextPart(text=response_text)],
            metadata={
                "name": "Orbit Press Secretary",
                "press_response": press_result,
                "crisis_id": crisis_id,
                "agent_type": "press_secretary",
                "status": "completed",
                "channels_generated": list(press_result.get("channels", {}).keys()),
                "alternatives_count": len(press_result.get("alternatives", [])),
                "legal_compliance": press_result.get("legal_compliance", False)
            }
        )
    
    def _create_error_message(self, error_details: str) -> Message:
        """Create error response message."""
        return Message(
            messageId=str(uuid4()),
            role=Role.agent,
            parts=[TextPart(text=f"Press Secretary error: {error_details}")],
            metadata={
                "name": "Orbit Press Secretary", 
                "press_response": {
                    "primary_statement": "We are aware of the situation and are reviewing it carefully.",
                    "tone": "professional_concerned",
                    "key_messages": ["Situation under review", "More information to follow"],
                    "alternatives": [
                        {"tone": "defensive", "statement": "We are reviewing these claims carefully."},
                        {"tone": "apologetic", "statement": "We apologize for any concerns this may have caused."}
                    ],
                    "channels": {
                        "press_release": "We are aware of the situation and are reviewing it carefully.",
                        "social_media": "We are reviewing the situation and will provide updates soon.",
                        "employee_memo": "Team, we are aware of recent developments and are reviewing the situation."
                    },
                    "legal_compliance": True,
                    "confidence": 0.1,
                    "error": f"Response generation failed: {error_details}"
                },
                "crisis_id": "unknown",
                "agent_type": "press_secretary",
                "status": "error"
            }
        )
    
    async def cancel(
        self, 
        request: RequestContext, 
        event_queue: EventQueue
    ) -> Task | None:
        """Cancel agent execution."""
        raise ServerError(error=UnsupportedOperationError()) 