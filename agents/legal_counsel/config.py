"""Configuration for the Legal Counsel agent."""

import os
from typing import Optional


class LegalCounselConfig:
    """Configuration class for the Legal Counsel agent."""
    
    def __init__(self):
        self.agent_port: int = int(os.getenv("AGENT_PORT", "9005"))
        self.azure_openai_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
        
        # Agent endpoints for potential future direct A2A calls
        self.press_secretary_endpoint = os.getenv("PRESS_SECRETARY_URL", "http://press-secretary:9006")
        
        # Legal rubric path (relative to project root)
        self.legal_rubric_path = os.getenv("LEGAL_RUBRIC_PATH", "data/legal_rubric.md")
        
        # Validate required configuration
        self._validate()
    
    def _validate(self) -> None:
        """Validate required configuration parameters."""
        if not self.azure_openai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable is required")
            
        if self.agent_port <= 0 or self.agent_port > 65535:
            raise ValueError(f"Invalid agent port: {self.agent_port}") 