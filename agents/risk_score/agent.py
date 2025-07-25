"""Core agent logic for the Risk Score agent."""

import json
import logging
import os
from typing import Dict, List, Any, Literal
from datetime import datetime, timezone

from langgraph.graph import MessagesState, StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph.message import add_messages
from typing_extensions import Annotated
from pydantic import BaseModel, Field, ValidationError

from common.llm import get_llm

logger = logging.getLogger("orbit.risk_score_agent.agent")

# Node states for the workflow
NodeState = Literal["SUPERVISOR", "ASSESS_RISK", "PROCESS_CRISIS_ANALYSIS", "GENERAL_RESPONSE"]


class ImpactAreas(BaseModel):
    """Schema for impact area assessment."""
    reputation: float = Field(ge=0.0, le=1.0, description="Reputational impact score")
    financial: float = Field(ge=0.0, le=1.0, description="Financial impact score")
    operational: float = Field(ge=0.0, le=1.0, description="Operational impact score")


class RiskAssessmentResponse(BaseModel):
    """Schema for validating LLM risk assessment response."""
    risk_score: float = Field(ge=0.0, le=10.0, description="Overall risk score from 0.0 (no risk) to 10.0 (critical risk)")
    risk_level: Literal["low", "medium", "high", "critical"] = Field(description="Risk classification level")
    impact_areas: ImpactAreas = Field(description="Detailed impact assessment by area")
    urgency: Literal["low", "medium", "high", "immediate"] = Field(description="Urgency level for response")
    recommendations: List[str] = Field(min_length=1, description="Specific recommendations for crisis response")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the risk assessment")
    key_risk_factors: List[str] = Field(description="Primary factors contributing to the risk score")
    mitigation_priority: List[str] = Field(description="Prioritized list of mitigation actions")


class GraphState(MessagesState):
    """Graph state extending MessagesState."""
    messages: Annotated[list, add_messages]
    current_action: str = ""
    crisis_data: Dict[str, Any] = {}
    risk_assessment: Dict[str, Any] = {}


class RiskScoreAgent:
    """Core agent for assessing crisis risk based on fact checking and sentiment analysis."""
    
    def __init__(self):
        self.llm = get_llm()
        # Build and compile LangGraph workflow
        self.workflow = self._create_workflow().compile()
        self.risk_assessment_prompt = self._create_risk_assessment_prompt()
        
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for the agent."""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("assess_risk", self._assess_risk_node) 
        workflow.add_node("process_crisis_analysis", self._process_crisis_analysis_node)
        workflow.add_node("general_response", self._general_response_node)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_message,
            {
                "risk": "assess_risk",
                "crisis_analysis": "process_crisis_analysis", 
                "general": "general_response"
            }
        )
        
        # All nodes end the workflow
        workflow.add_edge("assess_risk", END)
        workflow.add_edge("process_crisis_analysis", END)
        workflow.add_edge("general_response", END)
        
        return workflow
    
    def _create_risk_assessment_prompt(self) -> PromptTemplate:
        """Create the risk assessment prompt template."""
        template = """You are an expert crisis management consultant specializing in risk assessment and business impact analysis.

Analyze the following crisis situation using the provided fact checking and sentiment analysis data to assess overall risk:

FACT CHECKING ANALYSIS:
{fact_analysis}

SENTIMENT ANALYSIS:
{sentiment_analysis}

CRISIS CONTEXT:
- This is a corporate PR crisis requiring immediate risk assessment
- Consider both factual credibility and public sentiment impact
- Focus on business continuity, reputation management, and stakeholder impact
- Assess urgency for response and mitigation strategies

Please provide a comprehensive risk assessment in the following JSON format:

{{
    "risk_score": <float between 0.0 (no risk) and 10.0 (critical risk)>,
    "risk_level": "<'low', 'medium', 'high', or 'critical'>",
    "impact_areas": {{
        "reputation": <float between 0.0 and 1.0 for reputational impact>,
        "financial": <float between 0.0 and 1.0 for financial impact>,
        "operational": <float between 0.0 and 1.0 for operational impact>
    }},
    "urgency": "<'low', 'medium', 'high', or 'immediate'>",
    "recommendations": [
        "<specific actionable recommendations for crisis response>"
    ],
    "confidence": <float between 0.0 and 1.0 indicating confidence in this assessment>,
    "key_risk_factors": [
        "<primary factors contributing to the risk score>"
    ],
    "mitigation_priority": [
        "<prioritized list of mitigation actions>"
    ]
}}

Consider these factors in your assessment:
- Fact credibility (verified vs disputed claims)
- Public sentiment severity and emotional intensity
- Potential for viral spread and escalation
- Legal and compliance implications
- Stakeholder impact (customers, investors, employees)
- Brand reputation damage potential
- Business disruption likelihood

Respond with ONLY the JSON object, no additional text or explanation."""

        return PromptTemplate(
            input_variables=["fact_analysis", "sentiment_analysis"],
            template=template
        )
        
    async def ainvoke(self, prompt: str) -> str:
        """Async invoke the agent workflow following lungo pattern."""
        try:
            # Check if this is a risk assessment request with structured data
            crisis_data = {}
            if "Please assess the risk for this crisis with combined analysis:" in prompt:
                # Extract crisis content from the prompt
                content_start = prompt.find("Please assess the risk for this crisis with combined analysis:") + len("Please assess the risk for this crisis with combined analysis:")
                content = prompt[content_start:].strip()
                crisis_data = {"combined_analysis": content}
            
            state = GraphState(
                messages=[HumanMessage(content=prompt)],
                current_action="",
                crisis_data=crisis_data
            )
            
            result = await self.workflow.ainvoke(state)
            
            # Return the last AI message
            if result["messages"]:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    return last_message.content
                    
            return "Unable to process risk assessment request"
            
        except Exception as e:
            logger.error(f"Error in risk assessment workflow: {e}")
            return f"Error processing risk assessment: {str(e)}"
    
    async def analyze_crisis_risk(self, fact_analysis: Dict[str, Any], sentiment_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk for a crisis based on fact checking and sentiment analysis data."""
        try:
            if not fact_analysis or not sentiment_analysis:
                logger.error("Missing fact or sentiment analysis data for risk assessment")
                return self._create_error_response("Missing required analysis data")
            
            # Use LLM to assess risk
            prompt = self.risk_assessment_prompt.format(
                fact_analysis=json.dumps(fact_analysis, indent=2),
                sentiment_analysis=json.dumps(sentiment_analysis, indent=2)
            )
            llm_response = await self.llm.ainvoke(prompt)
            
            # Parse and validate JSON response
            try:
                raw_response = json.loads(llm_response.content)
                
                # Validate response against schema
                try:
                    validated_response = RiskAssessmentResponse(**raw_response)
                    
                    # Convert to dict and add metadata
                    risk_assessment = validated_response.model_dump()
                    risk_assessment.update({
                        "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
                        "fact_analysis_summary": {
                            "overall_credibility": fact_analysis.get("overall_credibility", "unknown"),
                            "claims_verified": fact_analysis.get("claims_verified", 0),
                            "claims_disputed": fact_analysis.get("claims_disputed", 0)
                        },
                        "sentiment_analysis_summary": {
                            "overall_sentiment": sentiment_analysis.get("overall_sentiment", 0.0),
                            "reputational_risk": sentiment_analysis.get("reputational_risk", "unknown"),
                            "emotional_intensity": sentiment_analysis.get("emotional_intensity", 0.0)
                        },
                        "analysis_model": "gpt-4o-mini"
                    })
                    
                    logger.info(f"Risk assessment completed: {risk_assessment['risk_level']} risk (score: {risk_assessment['risk_score']:.1f})")
                    return risk_assessment
                    
                except ValidationError as e:
                    logger.error(f"LLM response failed schema validation: {e}")
                    return self._create_error_response(f"Invalid LLM response format: {str(e)}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM risk assessment response as JSON: {e}")
                return self._create_error_response("Failed to parse risk assessment")
                
        except Exception as e:
            logger.error(f"Error in risk assessment analysis: {e}")
            return self._create_error_response(f"Analysis failed: {str(e)}")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response that matches our schema."""
        error_response = {
            "risk_score": 5.0,  # Default medium risk when unable to assess
            "risk_level": "medium",
            "impact_areas": {
                "reputation": 0.5,
                "financial": 0.5,
                "operational": 0.5
            },
            "urgency": "medium",
            "recommendations": ["Unable to complete risk assessment", "Manual review required"],
            "confidence": 0.0,
            "key_risk_factors": ["assessment_failed"],
            "mitigation_priority": ["resolve_assessment_issue"],
            "error": error_message,
            "assessment_timestamp": datetime.now(timezone.utc).isoformat()
        }
        return error_response
            
    def _supervisor_node(self, state: GraphState) -> GraphState:
        """Supervisor node that routes messages to appropriate handlers."""
        logger.info("Processing message in risk score supervisor node")
        
        # Get the latest human message
        last_message = state["messages"][-1]
        user_input = last_message.content.lower()
        
        # Check if crisis data is provided for direct analysis
        if state.get("crisis_data"):
            action = "crisis_analysis"
        # Check if this is a risk assessment request
        elif "assess risk" in user_input or "risk assessment" in user_input or "combined analysis" in user_input:
            action = "risk"
        elif "status" in user_input:
            action = "general"
        else:
            # Default to risk assessment for direct A2A calls
            action = "risk"
            
        state["current_action"] = action
        return state
        
    def _route_message(self, state: GraphState) -> str:
        """Route messages based on supervisor decision."""
        action = state.get("current_action", "general")
        logger.info(f"Routing to: {action}")
        return action
        
    def _assess_risk_node(self, state: GraphState) -> GraphState:
        """Handle direct risk assessment requests."""
        response_content = "Risk assessment capabilities ready. " \
                          "I can analyze crisis risk by combining fact checking and sentiment analysis data " \
                          "to provide comprehensive risk scores and mitigation recommendations."
        
        state["messages"].append(AIMessage(content=response_content))
        return state
    
    def _process_crisis_analysis_node(self, state: GraphState) -> GraphState:
        """Handle crisis analysis processing for risk assessment."""
        crisis_data = state.get("crisis_data", {})
        combined_analysis = crisis_data.get("combined_analysis", "No analysis data available")
        
        if combined_analysis and combined_analysis != "No analysis data available":
            # Note: Actual risk assessment will be performed in the agent executor
            # This node just acknowledges the crisis analysis
            response_content = f"Processing risk assessment for combined crisis analysis: " \
                              f"'{combined_analysis[:100]}...' - Assessment will be performed by the agent executor."
        else:
            response_content = "No analysis data available for risk assessment"
        
        state["messages"].append(AIMessage(content=response_content))
        return state
        
    def _general_response_node(self, state: GraphState) -> GraphState:
        """Handle general queries about risk assessment."""
        response_content = "I'm the Risk Score agent. I assess crisis severity by combining " \
                          "fact checking and sentiment analysis data to calculate risk scores, " \
                          "evaluate business impact, and provide prioritized mitigation recommendations."
                          
        state["messages"].append(AIMessage(content=response_content))
        return state 