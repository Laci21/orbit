"""Agent card for the Legal Counsel agent."""

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill
)

AGENT_SKILL = AgentSkill(
    id="review_legal_implications",
    name="Review Legal Implications",
    description="Reviews crisis situations for legal implications and provides compliance guidance based on fact checking analysis",
    tags=["legal-review", "compliance", "risk-assessment", "crisis-management"],
    examples=[
        "Review legal implications of executive misconduct allegations",
        "Assess compliance requirements for crisis response",
        "Provide legal guidance for public statement",
        "Evaluate litigation risk from fact checking results"
    ]
)

AGENT_CARD = AgentCard(
    name="Orbit Legal Counsel",
    id="legal-counsel-agent",
    description="An AI legal agent that reviews crisis situations for legal implications, provides compliance guidance, and recommends communication strategies based on legal risk assessment.",
    url="",
    version="1.0.0", 
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False
) 