"""Common LLM utilities for Orbit agents."""

import os
from langchain_community.chat_models import AzureChatOpenAI


def get_llm():
    """Get configured Azure OpenAI LLM instance."""
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    return AzureChatOpenAI(
        deployment_name=deployment_name,
        model_name="gpt-4o",
        openai_api_key=api_key,
        openai_api_version="2024-02-01",
        temperature=0.1
    )