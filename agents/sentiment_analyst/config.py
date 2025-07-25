"""Configuration for the Sentiment Analyst agent."""

import os
from typing import Optional


class SentimentAnalystConfig:
    """Configuration class for the Sentiment Analyst agent."""
    
    def __init__(self):
        self.agent_port: int = int(os.getenv("AGENT_PORT", "9002"))
        self.transport_endpoint: str = os.getenv("SLIM_BROKER_URL", "http://localhost:46357")
        self.broadcast_topic: str = os.getenv("BROADCAST_TOPIC", "orbit.sentiment.complete")
        self.crisis_topic: str = os.getenv("CRISIS_TOPIC", "orbit.crisis.detected")
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        
        # Validate required configuration
        self._validate()
    
    def _validate(self) -> None:
        """Validate required configuration parameters."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
            
        if self.agent_port <= 0 or self.agent_port > 65535:
            raise ValueError(f"Invalid agent port: {self.agent_port}")