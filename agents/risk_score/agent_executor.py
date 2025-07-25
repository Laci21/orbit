"""Agent executor for the Risk Score agent."""

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

from agents.risk_score.agent import RiskScoreAgent
from agents.risk_score.card import AGENT_CARD
from agents.risk_score.config import RiskScoreConfig

logger = logging.getLogger("orbit.risk_score_agent.agent_executor")


class RiskScoreAgentExecutor(AgentExecutor):
    """Agent executor for risk assessment of crisis content."""
    
    def __init__(self):
        self.agent = RiskScoreAgent()
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)
        self.config = RiskScoreConfig()
        
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
        """Execute the agent's logic for risk assessment."""
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
            # Check if this is a crisis risk assessment request with combined analysis
            if "Please assess the risk for this crisis with combined analysis:" in prompt:
                # Extract and parse the combined analysis data
                content_start = prompt.find("Please assess the risk for this crisis with combined analysis:") + len("Please assess the risk for this crisis with combined analysis:")
                combined_data = prompt[content_start:].strip()
                
                try:
                    # Parse the combined analysis data (should be JSON from Ear-to-Ground)
                    analysis_data = json.loads(combined_data)
                    fact_analysis = analysis_data.get("fact_analysis", {})
                    sentiment_analysis = analysis_data.get("sentiment_analysis", {})
                    crisis_id = analysis_data.get("crisis_id", "unknown")
                    
                    # Perform risk assessment
                    risk_result = await self.agent.analyze_crisis_risk(fact_analysis, sentiment_analysis)
                    
                    # Create response with risk assessment results
                    response_text = f"Risk assessment completed. " \
                                   f"Risk level: {risk_result.get('risk_level', 'unknown')}, " \
                                   f"Score: {risk_result.get('risk_score', 0.0):.1f}/10.0, " \
                                   f"Urgency: {risk_result.get('urgency', 'unknown')}"
                    
                    # Store risk result for potential future use
                    message = Message(
                        messageId=str(uuid4()),
                        role=Role.agent,
                        metadata={
                            "name": self.agent_card["name"],
                            "risk_assessment": risk_result,
                            "crisis_id": crisis_id
                        },
                        parts=[Part(TextPart(text=response_text))]
                    )
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse combined analysis data: {e}")
                    error_response = "Error: Invalid combined analysis data format"
                    message = Message(
                        messageId=str(uuid4()),
                        role=Role.agent,
                        metadata={"name": self.agent_card["name"], "error": "parse_error"},
                        parts=[Part(TextPart(text=error_response))]
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing risk assessment: {e}")
                    error_response = f"Error processing risk assessment: {str(e)}"
                    message = Message(
                        messageId=str(uuid4()),
                        role=Role.agent,
                        metadata={"name": self.agent_card["name"], "error": "processing_error"},
                        parts=[Part(TextPart(text=error_response))]
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
            logger.error(f"An error occurred while processing risk assessment: {e}")
            raise ServerError(error=InternalError()) from e
    
    async def cancel(
        self, 
        request: RequestContext, 
        event_queue: EventQueue
    ) -> Task | None:
        """Cancel agent execution."""
        raise ServerError(error=UnsupportedOperationError()) 