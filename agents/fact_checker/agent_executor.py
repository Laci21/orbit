"""Agent executor for the Fact Checker agent."""

import asyncio
import logging
from uuid import uuid4

import aiohttp

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

from agents.fact_checker.agent import FactCheckerAgent
from agents.fact_checker.card import AGENT_CARD
from agents.fact_checker.config import FactCheckerConfig

logger = logging.getLogger("orbit.fact_checker_agent.agent_executor")


class FactCheckerAgentExecutor(AgentExecutor):
    """Agent executor for fact checking crisis content."""
    
    def __init__(self):
        self.agent = FactCheckerAgent()
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)
        self.config = FactCheckerConfig()
        
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
        """Execute the agent's logic for fact checking."""
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
            # Check if this is a crisis fact checking request
            if "Please verify the claims in this crisis content:" in prompt:
                # Extract crisis content and perform fact checking
                content_start = prompt.find("Please verify the claims in this crisis content:") + len("Please verify the claims in this crisis content:")
                content = prompt[content_start:].strip()
                
                crisis_data = {
                    "text": content,
                    "content": content,
                    "crisis_id": "unknown"  # Could be extracted from prompt if needed
                }
                
                # Perform fact checking analysis
                fact_result = await self.agent.analyze_crisis_facts(crisis_data)
                
                # Create response with fact checking results
                response_text = f"Fact checking completed. " \
                               f"Credibility: {fact_result.get('overall_credibility', 'unknown')}, " \
                               f"Claims verified: {fact_result.get('claims_verified', 0)}/{fact_result.get('claims_identified', 0)}, " \
                               f"Risk factors: {len(fact_result.get('risk_factors', []))}"
                
                # Call Legal Counsel immediately after fact checking
                await self._call_legal_counsel(crisis_data, fact_result)
                
                # Store fact result for potential Risk Score call later
                # (Risk Score will be called separately by Sentiment Analyst)
                
                message = Message(
                    messageId=str(uuid4()),
                    role=Role.agent,
                    metadata={
                        "name": self.agent_card["name"],
                        "fact_analysis": fact_result,
                        "crisis_id": crisis_data.get("crisis_id")
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
            
            logger.info("agent output message: %s", message)
            event_queue.enqueue_event(message)
                    
        except Exception as e:
            logger.error(f"An error occurred while processing fact check: {e}")
            raise ServerError(error=InternalError()) from e
    
    async def _call_legal_counsel(self, crisis_data: dict, fact_result: dict) -> None:
        """Call Legal Counsel agent immediately after fact checking."""
        try:
            prompt = f"Please review the legal implications of this crisis based on fact checking results: {fact_result['overall_credibility']} credibility, claims: {fact_result.get('fact_checks', [])}"
            
            # JSON-RPC request payload for Legal Counsel
            request_payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": f"legal-review-{crisis_data.get('crisis_id', 'unknown')}",
                        "role": "user",
                        "parts": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                },
                "id": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.legal_counsel_endpoint}/",
                    json=request_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Legal Counsel called successfully for crisis {crisis_data.get('crisis_id', 'unknown')}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Legal Counsel call failed: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            logger.error("Legal Counsel call timed out")
        except Exception as e:
            logger.error(f"Error calling Legal Counsel: {e}")
            
    async def cancel(
        self, 
        request: RequestContext, 
        event_queue: EventQueue
    ) -> Task | None:
        """Cancel agent execution."""
        raise ServerError(error=UnsupportedOperationError())