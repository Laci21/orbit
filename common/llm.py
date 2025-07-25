"""Common LLM utilities for Orbit agents."""

import os
from langchain_openai import AzureChatOpenAI


def get_llm():
    """Get configured Azure OpenAI LLM instance."""
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    
    return AzureChatOpenAI(
        azure_deployment=azure_deployment,
        azure_endpoint=azure_endpoint,
        api_version=api_version,
        temperature=0.1,
        max_retries=2,
        timeout=30
    )
