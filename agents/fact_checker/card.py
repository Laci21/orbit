"""Agent card for the Fact Checker agent."""

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill
)

AGENT_SKILL = AgentSkill(
    id="verify_crisis_claims",
    name="Verify Crisis Claims",
    description="Verifies factual claims in crisis-related content to assess credibility and identify misinformation",
    tags=["fact-checking", "verification", "claims", "credibility"],
    examples=[
        "Verify claims in this crisis tweet",
        "Check the credibility of these allegations",
        "Assess evidence level for executive misconduct claim",
        "Identify unsubstantiated claims in social media post"
    ]
)

AGENT_CARD = AgentCard(
    name="Orbit Fact Checker",
    id="fact-checker-agent",
    description="An AI agent that verifies factual claims in crisis-related content to assess credibility and identify misinformation.",
    url="",
    version="1.0.0", 
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False
)