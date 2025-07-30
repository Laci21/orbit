"""Agent executor for the Fact Checker agent."""

import asyncio
import logging
from uuid import uuid4
from typing import Dict, Any
import json

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
from common.slim_client import call_agent_slim

logger = logging.getLogger("orbit.fact_checker_agent.agent_executor")


class FactCheckerAgentExecutor(AgentExecutor):
    """Agent executor for fact-checking crisis content."""
    
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
            logger.info(f"Processing fact check request with prompt: {prompt}")
            agent_response = await self.agent.ainvoke(prompt)
            logger.info(f"Agent response: {agent_response} (type: {type(agent_response)})")
            
            # Handle None response
            if agent_response is None:
                agent_response = "Error: Agent returned None response"
                logger.error("Agent ainvoke returned None")
            
            # ------------------------------------------------------------------
            # Build **structured** fact_check_data so downstream agents (Risk Score)
            # can always rely on a dict, never a plain string.
            # ------------------------------------------------------------------
            fact_check_data: Dict[str, Any]
            try:
                if isinstance(agent_response, dict):
                    # Already structured → use as-is
                    fact_check_data = {"fact_check_analysis": agent_response}
                elif isinstance(agent_response, str):
                    # Try to parse JSON string returned by LLM
                    parsed: Dict[str, Any] | None = None
                    try:
                        parsed_json = json.loads(agent_response)
                        if isinstance(parsed_json, dict):
                            parsed = parsed_json
                    except Exception:
                        parsed = None
                    if parsed is not None:
                        fact_check_data = {"fact_check_analysis": parsed}
                    else:
                        # Fallback – wrap raw text so it is still a dict
                        fact_check_data = {"fact_check_analysis": {"raw_text": agent_response}}
                else:
                    # Unexpected type – store stringified version
                    fact_check_data = {"fact_check_analysis": {"raw_text": str(agent_response)}}

                logger.info(f"Structured fact check data: {fact_check_data}")
            except Exception as e:
                logger.error(f"Error structuring fact check data: {e}")
                fact_check_data = {"fact_check_analysis": {"raw_text": str(agent_response)}, "error": str(e)}
            
            # Call Legal Counsel for legal review if we have fact check analysis
            legal_review_data = None
            if fact_check_data:
                legal_review_data = await self._call_legal_counsel(prompt, fact_check_data)
            
            # Create message metadata with both fact check and legal review data
            message_metadata = {
                "name": self.agent_card["name"],
                "fact_check": fact_check_data
            }
            
            # Include legal review in metadata if available
            if legal_review_data:
                message_metadata["legal_review"] = legal_review_data
            
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
    
    async def _call_legal_counsel(self, original_prompt: str, fact_check_data: dict) -> dict:
        """Call the Legal Counsel agent for legal review using SLIM."""
        try:
            # Enhanced prompt that includes both original content and fact check results
            prompt = f"""
Please provide a legal review of this crisis content and its fact check analysis:

Original content: {original_prompt}
Fact check analysis: {fact_check_data.get('fact_check_analysis', 'No analysis available')}

Please assess legal risks, compliance issues, and provide recommendations.
"""
            
            # JSON-RPC request payload for A2A communication
            request_payload = {
                "jsonrpc": "2.0",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": f"legal-review-{uuid4()}",
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
            
            # Call legal counsel via SLIM
            result = await call_agent_slim(
                self.config.legal_counsel_endpoint,
                request_payload,
                timeout=30.0
            )
            
            if "error" not in result:
                logger.info("Legal Counsel called successfully via SLIM")
                
                # Try to extract legal_review from the response structure
                try:
                    # Expected path: result -> result -> message -> metadata -> legal_review
                    if (
                        isinstance(result, dict)
                        and "result" in result
                        and isinstance(result["result"], dict)
                    ):
                        inner = result["result"]
                        if (
                            "message" in inner
                            and isinstance(inner["message"], dict)
                            and "metadata" in inner["message"]
                            and isinstance(inner["message"]["metadata"], dict)
                        ):
                            metadata = inner["message"]["metadata"]
                            if "legal_review" in metadata:
                                legal_review = metadata["legal_review"]
                                logger.info(f"Extracted legal review: {legal_review}")
                                return legal_review
                    
                    # Fallback: extract text content as legal review
                    if (
                        isinstance(result, dict)
                        and "result" in result
                        and isinstance(result["result"], dict)
                        and "message" in result["result"]
                        and isinstance(result["result"]["message"], dict)
                        and "parts" in result["result"]["message"]
                    ):
                        parts = result["result"]["message"]["parts"]
                        if parts and len(parts) > 0 and "text" in parts[0]:
                            legal_text = parts[0]["text"]
                            logger.info(f"Using text content as legal review: {legal_text}")
                            return {"legal_analysis": legal_text}
                    
                    logger.warning(f"Could not extract legal review from response structure: {result}")
                    return {"legal_analysis": str(result)}
                    
                except Exception as e:
                    logger.error(f"Error extracting legal review data: {e}")
                    return {"legal_analysis": str(result), "extraction_error": str(e)}
            else:
                logger.error(f"Legal Counsel call failed via SLIM: {result.get('error', 'Unknown error')}")
                return {"error": result.get("error", "Unknown error")}
                
        except Exception as e:
            logger.error(f"Error calling Legal Counsel via SLIM: {e}")
            return {"error": str(e)}
            
    async def cancel(
        self, 
        request: RequestContext, 
        event_queue: EventQueue
    ) -> Task | None:
        """Cancel agent execution."""
        raise ServerError(error=UnsupportedOperationError())