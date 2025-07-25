"""Core agent logic for the Legal Counsel agent."""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Literal
from datetime import datetime, timezone

from langgraph.graph import MessagesState, StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph.message import add_messages
from typing_extensions import Annotated
from pydantic import BaseModel, Field, ValidationError

from common.llm import get_llm

logger = logging.getLogger("orbit.legal_counsel_agent.agent")

# Node states for the workflow
NodeState = Literal["SUPERVISOR", "REVIEW_LEGAL", "PROCESS_FACT_CHECK", "GENERAL_RESPONSE"]


class LegalReviewResponse(BaseModel):
    """Schema for validating LLM legal review response."""
    legal_risk: Literal["low", "medium", "high", "critical"] = Field(description="Overall legal risk level")
    compliance_issues: List[str] = Field(description="List of compliance concerns identified")
    recommended_approach: str = Field(description="Recommended communication approach")
    restrictions: List[str] = Field(description="List of communication restrictions and guidelines")
    escalation_needed: bool = Field(description="Whether escalation to senior legal counsel is needed")
    mandatory_inclusions: List[str] = Field(description="Required phrases/statements that must be included")
    forbidden_elements: List[str] = Field(description="Elements that must be avoided in communication")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the legal assessment")
    key_legal_factors: List[str] = Field(description="Primary legal factors influencing the assessment")


class GraphState(MessagesState):
    """Graph state extending MessagesState."""
    messages: Annotated[list, add_messages]
    current_action: str = ""
    fact_check_data: Dict[str, Any] = {}
    legal_review: Dict[str, Any] = {}


class LegalCounselAgent:
    """Core agent for legal risk assessment and compliance review."""
    
    def __init__(self):
        self.llm = get_llm()
        # Build and compile LangGraph workflow
        self.workflow = self._create_workflow().compile()
        self.legal_review_prompt = self._create_legal_review_prompt()
        # Load legal rubric
        self.legal_rubric = self._load_legal_rubric()
        
    def _load_legal_rubric(self) -> str:
        """Load the legal rubric from the data directory."""
        try:
            rubric_path = Path("data/legal_rubric.md")
            if rubric_path.exists():
                with open(rubric_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning("Legal rubric file not found, using minimal guidelines")
                return """
# Basic Legal Guidelines
- Avoid admitting fault or liability
- Take allegations seriously  
- Commit to thorough investigation
- Maintain professional tone
"""
        except Exception as e:
            logger.error(f"Error loading legal rubric: {e}")
            return "# Minimal Legal Guidelines\n- Avoid admitting fault\n- Professional tone required"
        
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for the agent."""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("review_legal", self._review_legal_node) 
        workflow.add_node("process_fact_check", self._process_fact_check_node)
        workflow.add_node("general_response", self._general_response_node)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_message,
            {
                "legal": "review_legal",
                "fact_check": "process_fact_check", 
                "general": "general_response"
            }
        )
        
        # All nodes end the workflow
        workflow.add_edge("review_legal", END)
        workflow.add_edge("process_fact_check", END)
        workflow.add_edge("general_response", END)
        
        return workflow
    
    def _create_legal_review_prompt(self) -> PromptTemplate:
        """Create the legal review prompt template."""
        template = """You are an expert corporate legal counsel specializing in crisis communication and compliance.

Review the following fact checking analysis for legal implications and provide compliance guidance:

FACT CHECKING ANALYSIS:
{fact_analysis}

LEGAL RUBRIC AND GUIDELINES:
{legal_rubric}

CRISIS CONTEXT:
- This is a corporate PR crisis requiring legal review
- Focus on legal risk mitigation and compliance
- Consider potential liability, regulatory concerns, and reputational protection
- Provide clear guidance for crisis communication

Please provide a comprehensive legal review in the following JSON format:

{{
    "legal_risk": "<'low', 'medium', 'high', or 'critical'>",
    "compliance_issues": [
        "<specific compliance concerns or regulatory issues identified>"
    ],
    "recommended_approach": "<specific recommended communication strategy>",
    "restrictions": [
        "<specific communication restrictions and what to avoid>"
    ],
    "escalation_needed": <true/false for whether senior legal counsel involvement is needed>,
    "mandatory_inclusions": [
        "<required phrases or statements that must be included in any response>"
    ],
    "forbidden_elements": [
        "<specific elements that must be avoided in any communication>"
    ],
    "confidence": <float between 0.0 and 1.0 indicating confidence in this assessment>,
    "key_legal_factors": [
        "<primary legal factors that influenced this assessment>"
    ]
}}

Consider these legal factors in your assessment:
- Potential admissions of liability or fault
- Employment law implications
- Securities/disclosure requirements
- Privacy and confidentiality concerns
- Regulatory compliance obligations
- Litigation risk and document preservation
- Stakeholder communication requirements
- Reputational protection strategies

Base your risk level on:
- LOW: Minor issues, routine compliance, low litigation risk
- MEDIUM: Some compliance concerns, moderate litigation risk, careful communication needed
- HIGH: Significant legal implications, high litigation risk, legal team oversight required
- CRITICAL: Severe legal exposure, immediate legal intervention needed, potential regulatory action

Respond with ONLY the JSON object, no additional text or explanation."""

        return PromptTemplate(
            input_variables=["fact_analysis", "legal_rubric"],
            template=template
        )
        
    async def ainvoke(self, prompt: str) -> str:
        """Async invoke the agent workflow following lungo pattern."""
        try:
            # Check if this is a legal review request with fact checking data
            fact_check_data = {}
            if "Please review the legal implications of this crisis based on fact checking results:" in prompt:
                # Extract fact checking content from the prompt
                content_start = prompt.find("Please review the legal implications of this crisis based on fact checking results:") + len("Please review the legal implications of this crisis based on fact checking results:")
                content = prompt[content_start:].strip()
                fact_check_data = {"fact_analysis": content}
            
            state = GraphState(
                messages=[HumanMessage(content=prompt)],
                current_action="",
                fact_check_data=fact_check_data
            )
            
            result = await self.workflow.ainvoke(state)
            
            # Return the last AI message
            if result["messages"]:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    return last_message.content
                    
            return "Unable to process legal review request"
            
        except Exception as e:
            logger.error(f"Error in legal review workflow: {e}")
            return f"Error processing legal review: {str(e)}"
    
    async def analyze_legal_implications(self, fact_analysis: str) -> Dict[str, Any]:
        """Analyze legal implications based on fact checking results."""
        try:
            if not fact_analysis:
                logger.error("No fact analysis provided for legal review")
                return self._create_error_response("No fact analysis provided")
            
            # Use LLM to assess legal implications
            prompt = self.legal_review_prompt.format(
                fact_analysis=fact_analysis,
                legal_rubric=self.legal_rubric
            )
            llm_response = await self.llm.ainvoke(prompt)
            
            # Parse and validate JSON response
            try:
                raw_response = json.loads(llm_response.content)
                
                # Validate response against schema
                try:
                    validated_response = LegalReviewResponse(**raw_response)
                    
                    # Convert to dict and add metadata
                    legal_review = validated_response.model_dump()
                    legal_review.update({
                        "review_timestamp": datetime.now(timezone.utc).isoformat(),
                        "review_model": "gpt-4o-mini",
                        "rubric_version": "v1.0"
                    })
                    
                    logger.info(f"Legal review completed: {legal_review['legal_risk']} risk, escalation: {legal_review['escalation_needed']}")
                    return legal_review
                    
                except ValidationError as e:
                    logger.error(f"LLM response failed schema validation: {e}")
                    return self._create_error_response(f"Invalid LLM response format: {str(e)}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM legal review response as JSON: {e}")
                return self._create_error_response("Failed to parse legal review")
                
        except Exception as e:
            logger.error(f"Error in legal review analysis: {e}")
            return self._create_error_response(f"Analysis failed: {str(e)}")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response that matches our schema."""
        error_response = {
            "legal_risk": "medium",  # Default to medium risk when unable to assess
            "compliance_issues": ["legal_assessment_failed"],
            "recommended_approach": "Seek immediate legal counsel review",
            "restrictions": ["Do not issue any public statements until legal review is complete"],
            "escalation_needed": True,  # Always escalate on error
            "mandatory_inclusions": ["Legal review is ongoing"],
            "forbidden_elements": ["Any statements without legal approval"],
            "confidence": 0.0,
            "key_legal_factors": ["assessment_error"],
            "error": error_message,
            "review_timestamp": datetime.now(timezone.utc).isoformat()
        }
        return error_response
            
    def _supervisor_node(self, state: GraphState) -> GraphState:
        """Supervisor node that routes messages to appropriate handlers."""
        logger.info("Processing message in legal counsel supervisor node")
        
        # Get the latest human message
        last_message = state["messages"][-1]
        user_input = last_message.content.lower()
        
        # Check if fact check data is provided for direct analysis
        if state.get("fact_check_data"):
            action = "fact_check"
        # Check if this is a legal review request
        elif "legal implications" in user_input or "legal review" in user_input or "compliance" in user_input:
            action = "legal"
        elif "status" in user_input:
            action = "general"
        else:
            # Default to legal review for direct A2A calls
            action = "legal"
            
        state["current_action"] = action
        return state
        
    def _route_message(self, state: GraphState) -> str:
        """Route messages based on supervisor decision."""
        action = state.get("current_action", "general")
        logger.info(f"Routing to: {action}")
        return action
        
    def _review_legal_node(self, state: GraphState) -> GraphState:
        """Handle direct legal review requests."""
        response_content = "Legal review capabilities ready. " \
                          "I can assess legal implications of crisis content, " \
                          "provide compliance guidance, and recommend communication strategies."
        
        state["messages"].append(AIMessage(content=response_content))
        return state
    
    def _process_fact_check_node(self, state: GraphState) -> GraphState:
        """Handle fact check processing for legal review."""
        fact_check_data = state.get("fact_check_data", {})
        fact_analysis = fact_check_data.get("fact_analysis", "No fact analysis available")
        
        if fact_analysis and fact_analysis != "No fact analysis available":
            # Note: Actual legal review will be performed in the agent executor
            # This node just acknowledges the fact check data
            response_content = f"Processing legal review for fact checking analysis: " \
                              f"'{fact_analysis[:100]}...' - Review will be performed by the agent executor."
        else:
            response_content = "No fact analysis data available for legal review"
        
        state["messages"].append(AIMessage(content=response_content))
        return state
        
    def _general_response_node(self, state: GraphState) -> GraphState:
        """Handle general queries about legal counsel."""
        response_content = "I'm the Legal Counsel agent. I provide legal risk assessment " \
                          "and compliance guidance for crisis communications, ensuring " \
                          "proper legal safeguards and regulatory compliance."
                          
        state["messages"].append(AIMessage(content=response_content))
        return state 