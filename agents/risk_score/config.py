"""Configuration for the Risk Score agent."""

import os
from typing import Optional


class RiskScoreConfig:
    """Configuration class for the Risk Score agent."""
    
    def __init__(self):
        self.agent_port: int = int(os.getenv("AGENT_PORT", "9003"))
        self.azure_openai_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
        
        # Crisis threshold for risk assessment
        self.crisis_threshold: float = float(os.getenv("CRISIS_THRESHOLD", "7.0"))
        
        # Agent endpoints for potential future direct A2A calls
        self.press_secretary_endpoint = os.getenv("PRESS_SECRETARY_URL", "http://press-secretary:9006")
        
        # Validate required configuration
        self._validate()
    
    def _validate(self) -> None:
        """Validate required configuration parameters."""
        if not self.azure_openai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable is required")
            
        if self.agent_port <= 0 or self.agent_port > 65535:
            raise ValueError(f"Invalid agent port: {self.agent_port}")
            
        if self.crisis_threshold < 0.0 or self.crisis_threshold > 100.0:
            raise ValueError(f"Invalid crisis threshold: {self.crisis_threshold}") 