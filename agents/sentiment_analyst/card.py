"""Agent card for the Sentiment Analyst agent."""

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill
)

AGENT_SKILL = AgentSkill(
    id="analyze_crisis_sentiment",
    name="Analyze Crisis Sentiment",
    description="Analyzes public sentiment from crisis-related social media content to assess emotional impact and reputational risk",
    tags=["sentiment", "crisis", "analysis", "emotions"],
    examples=[
        "Analyze sentiment of this crisis tweet",
        "What's the public emotional reaction?",
        "Assess sentiment impact for PR crisis",
        "Evaluate emotional intensity of social media response"
    ]
)

AGENT_CARD = AgentCard(
    name="Orbit Sentiment Analyst",
    id="sentiment-analyst-agent",
    description="An AI agent that analyzes public sentiment from crisis-related social media content to assess emotional impact and reputational risk.",
    url="",
    version="1.0.0", 
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False
)