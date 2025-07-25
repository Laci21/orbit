"""Event handling service for the Sentiment Analyst agent."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from agntcy_app_sdk.protocols.message import Message

from agents.sentiment_analyst.card import AGENT_CARD
from agents.sentiment_analyst.agent import SentimentAnalystAgent

logger = logging.getLogger("orbit.sentiment_analyst_agent.event_service")




class SentimentEventService:
    """Service responsible for handling crisis events and publishing sentiment analysis."""
    
    def __init__(self, transport, broadcast_topic: str, crisis_topic: str):
        self.transport = transport
        self.broadcast_topic = broadcast_topic
        self.crisis_topic = crisis_topic
        self.agent = SentimentAnalystAgent()
        self._is_running = False
        # Convert agent card to dict following Coffee AGNTCY pattern
        self.agent_card = AGENT_CARD.model_dump(mode="json", exclude_none=True)
        
    async def start(self) -> None:
        """Start the sentiment event service."""
        if self._is_running:
            logger.warning("Sentiment event service is already running")
            return
            
        # Wait for server to fully initialize
        await asyncio.sleep(5)
        
        logger.info("Starting sentiment event service...")
        self._is_running = True
        
        try:
            await self._subscribe_to_crisis_events()
        except Exception as e:
            logger.error(f"Error in sentiment event service: {e}")
            raise
        finally:
            self._is_running = False
            
    async def _subscribe_to_crisis_events(self) -> None:
        """Subscribe to crisis detection events from SLIM transport."""
        logger.info(f"Subscribed to crisis events on topic: {self.crisis_topic}")
        
        # The actual SLIM transport subscription is handled by the server's crisis bridge
        # This service stays alive to handle events when they're received
        while self._is_running:
            try:
                # Keep service alive and ready to process crisis events
                # Event handling will be triggered externally via handle_crisis_event()
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in event service loop: {e}")
                continue
                
    async def handle_crisis_event(self, event_data: Dict[str, Any]) -> None:
        """Handle incoming crisis event and perform sentiment analysis."""
        try:
            event_type = event_data.get("event_type")
            if event_type != "crisis_detected":
                logger.debug(f"Ignoring non-crisis event: {event_type}")
                return
                
            crisis_data = event_data.get("crisis", {})
            crisis_id = event_data.get("crisis_id") or crisis_data.get("id", "unknown")
            
            logger.info(f"Processing crisis event for sentiment analysis: {crisis_id}")
            
            # Perform sentiment analysis using the agent
            sentiment_result = await self.agent.analyze_crisis_sentiment(crisis_data)
            
            # Publish sentiment analysis completion event
            await self._publish_sentiment_complete(crisis_id, sentiment_result)
            
        except Exception as e:
            logger.error(f"Error handling crisis event: {e}")
            
    async def _publish_sentiment_complete(self, crisis_id: str, sentiment_result: Dict[str, Any]) -> None:
        """Publish sentiment analysis completion event."""
        completion_data = {
            "event_type": "sentiment_complete",
            "agent_id": "sentiment-analyst-agent",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "crisis_id": crisis_id,
            "analysis": sentiment_result
        }
        
        # Create proper SDK Message
        payload_json = json.dumps(completion_data)
        message = Message(
            type="sentiment_complete",
            payload=payload_json.encode('utf-8'),
            headers={"content-type": "application/json"},
            method="POST"
        )
        
        if self.transport:
            await self.transport.publish(
                topic="orbit.sentiment.complete",
                message=message
            )
            
        logger.info(f"Published sentiment analysis completion for crisis: {crisis_id}")
        
    def stop(self) -> None:
        """Stop the event service."""
        self._is_running = False
        logger.info("Sentiment event service stopped")