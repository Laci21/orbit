"""Common LLM utilities for Orbit agents."""

import os
from langchain_openai import ChatOpenAI


def get_llm():
    """Get configured LLM instance."""
    return ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
        temperature=0.1
    )