"""Agent card for the Ear-to-Ground agent."""

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill
)

AGENT_SKILL = AgentSkill(
    id="stream_crisis_tweets",
    name="Stream Crisis Tweets",
    description="Monitors and streams tweet data from social media for crisis detection and analysis",
    tags=["crisis", "monitoring", "social-media"],
    examples=[
        "Start streaming crisis tweets",
        "Monitor social media for PR issues",
        "Stream crisis-related posts",
        "What crisis tweets are available?"
    ]
)

AGENT_CARD = AgentCard(
    name="Orbit Ear-to-Ground Monitor",
    id="ear-to-ground-agent",
    description="An AI agent that monitors and streams crisis-related social media posts for real-time PR analysis.",
    url="",
    version="1.0.0", 
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False
)