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
        timeout=30,
        model_kwargs={
            # Ask the OpenAI API to return a pure JSON object so that downstream
            # agents can safely json.loads() the content without extra parsing.
            # Supported as of 2023-10-17 preview API and later.
            "response_format": {"type": "json_object"}
        }
    )
