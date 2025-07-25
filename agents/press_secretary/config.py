"""Configuration for the Press Secretary agent."""

import os
from typing import Optional


class PressSecretaryConfig:
    """Configuration class for the Press Secretary agent."""
    
    def __init__(self):
        """Initialize Press Secretary configuration from environment variables."""
        # Agent configuration
        self.agent_port: int = int(os.getenv("AGENT_PORT", "9006"))
        
        # Azure OpenAI configuration
        self.azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.azure_openai_deployment_name: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "")
        self.azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        
        # Validate required configuration
        self._validate()
    
    def _validate(self) -> None:
        """Validate required configuration parameters."""
        if not self.azure_openai_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY environment variable is required")
            
        if not self.azure_openai_deployment_name:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME environment variable is required")
            
        if not self.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
            
        if self.agent_port <= 0 or self.agent_port > 65535:
            raise ValueError(f"Invalid agent port: {self.agent_port}") 