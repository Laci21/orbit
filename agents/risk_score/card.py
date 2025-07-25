"""Agent card for the Risk Score agent."""

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill
)

AGENT_SKILL = AgentSkill(
    id="assess_crisis_risk",
    name="Assess Crisis Risk",
    description="Analyzes crisis risk by combining fact checking and sentiment analysis data to provide comprehensive risk assessment",
    tags=["risk-assessment", "crisis-management", "business-impact", "mitigation"],
    examples=[
        "Assess risk for this crisis with combined analysis",
        "Calculate risk score for executive misconduct allegations",
        "Evaluate business impact from negative social media sentiment",
        "Provide mitigation recommendations for viral crisis content"
    ]
)

AGENT_CARD = AgentCard(
    name="Orbit Risk Score",
    id="risk-score-agent",
    description="An AI agent that assesses crisis risk by combining fact checking and sentiment analysis data to calculate risk scores and provide mitigation recommendations.",
    url="",
    version="1.0.0", 
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[AGENT_SKILL],
    supportsAuthenticatedExtendedCard=False
) 