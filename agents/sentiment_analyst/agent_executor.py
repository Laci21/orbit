"""Agent executor for the Sentiment Analyst agent."""

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
    Task,
    TextPart,
    Part,
    Task
)
from a2a.utils import (
    new_task,
)

from agents.sentiment_analyst.agent import SentimentAnalystAgent
from agents.sentiment_analyst.card import AGENT_CARD
from agents.sentiment_analyst.config import SentimentAnalystConfig

logger = logging.getLogger("orbit.sentiment_analyst_agent.agent_executor")


class SentimentAnalystAgentExecutor(AgentExecutor):
    """Agent executor for sentiment analysis of crisis content."""
    
    def __init__(self):
        self.agent = SentimentAnalystAgent()
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)
        self.config = SentimentAnalystConfig()
        
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
            # Check if this is a crisis sentiment analysis request
            if "Please analyze the sentiment of this crisis content:" in prompt:
                # Extract crisis content and perform sentiment analysis
                content_start = prompt.find("Please analyze the sentiment of this crisis content:") + len("Please analyze the sentiment of this crisis content:")
                content = prompt[content_start:].strip()
                
                crisis_data = {
                    "text": content,
                    "content": content,
                    "crisis_id": "unknown"  # Could be extracted from prompt if needed
                }
                
                # Perform sentiment analysis
                sentiment_result = await self.agent.analyze_crisis_sentiment(crisis_data)
                
                # Create response with sentiment analysis results
                response_text = f"Sentiment analysis completed. " \
                               f"Overall sentiment: {sentiment_result.get('overall_sentiment', 0.0):.2f}, " \
                               f"Reputational risk: {sentiment_result.get('reputational_risk', 'unknown')}, " \
                               f"Key emotions: {', '.join(sentiment_result.get('key_emotions', []))}"
                
                message = Message(
                    messageId=str(uuid4()),
                    role=Role.agent,
                    metadata={
                        "name": self.agent_card["name"],
                        "sentiment_analysis": sentiment_result,
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
            logger.error(f"An error occurred while processing sentiment analysis: {e}")
            raise ServerError(error=InternalError()) from e
            
    async def cancel(
        self, 
        request: RequestContext, 
        event_queue: EventQueue
    ) -> Task | None:
        """Cancel agent execution."""
        raise ServerError(error=UnsupportedOperationError())