"""Configuration for the Fact Checker agent."""

import os
from typing import Optional


class FactCheckerConfig:
    """Configuration class for the Fact Checker agent."""
    
    def __init__(self):
        self.agent_port: int = int(os.getenv("AGENT_PORT", "9004"))
        self.azure_openai_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
        
        # Agent endpoints for direct A2A calls
        self.legal_counsel_endpoint = os.getenv("LEGAL_COUNSEL_URL", "http://legal-counsel:9005")
        self.risk_score_endpoint = os.getenv("RISK_SCORE_URL", "http://risk-score:9003")
        
        # Validate required configuration
        self._validate()
    
    def _validate(self) -> None:
        """Validate required configuration parameters."""
        if not self.azure_openai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable is required")
            
        if self.agent_port <= 0 or self.agent_port > 65535:
            raise ValueError(f"Invalid agent port: {self.agent_port}")