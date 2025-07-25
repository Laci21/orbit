"""Configuration for the Ear-to-Ground agent."""

import os


class EarToGroundConfig:
    """Configuration settings for the Ear-to-Ground agent."""
    
    def __init__(self):
        self.agent_port = int(os.getenv("AGENT_PORT", "9001"))
        self.transport_endpoint = os.getenv("SLIM_BROKER_URL", "http://localhost:46357")
        self.tweet_file = os.getenv("ORBIT_TWEET_FILE", "data/tweets_astronomer.json")
        self.tweet_rate = float(os.getenv("TWEET_STREAM_RATE", "1.0"))
        self.broadcast_topic = "orbit.crisis.detected"
        
        self._validate()
        
    def _validate(self) -> None:
        """Validate configuration values."""
        if self.agent_port <= 0 or self.agent_port > 65535:
            raise ValueError(f"Invalid agent port: {self.agent_port}")
            
        if self.tweet_rate <= 0:
            raise ValueError(f"Tweet rate must be positive: {self.tweet_rate}")
            
        if not os.path.exists(self.tweet_file):
            raise FileNotFoundError(f"Tweet file not found: {self.tweet_file}")