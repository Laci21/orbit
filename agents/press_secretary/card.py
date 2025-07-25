"""Agent card for the Press Secretary agent."""

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill
)

AGENT_SKILL = AgentSkill(
    id="generate_crisis_response",
    name="Generate Crisis Response",
    description="Generates comprehensive crisis response statements based on combined analysis from all crisis management agents",
    tags=["crisis-response", "communications", "press-statement", "public-relations"],
    examples=[
        "Generate official crisis response for executive misconduct allegations",
        "Create press statement based on comprehensive crisis analysis",
        "Draft multi-channel crisis communication strategy",
        "Provide alternative response tones for crisis management"
    ]
)

AGENT_CARD = AgentCard(
    name="Orbit Press Secretary",
    id="press-secretary-agent",
    description="An AI agent that generates comprehensive crisis response statements by synthesizing insights from sentiment analysis, fact-checking, risk assessment, and legal review to create professional crisis communications.",
    url="",
    version="1.0.0", 
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False
) 