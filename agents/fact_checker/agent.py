"""Core agent logic for the Fact Checker agent."""

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

logger = logging.getLogger("orbit.fact_checker_agent.agent")

# Node states for the workflow
NodeState = Literal["SUPERVISOR", "ANALYZE_FACTS", "PROCESS_CRISIS_EVENT", "GENERAL_RESPONSE"]


class FactCheck(BaseModel):
    """Schema for individual fact check result."""
    claim: str = Field(description="The specific claim being fact-checked")
    status: Literal["verified", "unverified", "disputed"] = Field(description="Verification status")
    evidence_level: Literal["high", "medium", "low"] = Field(description="Quality of evidence available")
    sources: List[str] = Field(description="Types of sources available for verification")
    notes: str = Field(default="", description="Additional notes about the fact check")


class FactCheckAnalysisResponse(BaseModel):
    """Schema for validating LLM fact checking response."""
    claims_identified: int = Field(ge=0, description="Number of claims identified in the content")
    claims_verified: int = Field(ge=0, description="Number of claims that could be verified")
    claims_disputed: int = Field(ge=0, description="Number of claims that are disputed or false")
    overall_credibility: Literal["high", "medium", "low"] = Field(description="Overall credibility assessment")
    fact_checks: List[FactCheck] = Field(min_length=1, description="Detailed fact check results")
    risk_factors: List[str] = Field(description="Identified risk factors for the organization")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the analysis")
    misinformation_indicators: List[str] = Field(default_factory=list, description="Potential misinformation signals")


class GraphState(MessagesState):
    """Graph state extending MessagesState."""
    messages: Annotated[list, add_messages]
    current_action: str = ""
    crisis_data: Dict[str, Any] = {}
    fact_check_result: Dict[str, Any] = {}


class FactCheckerAgent:
    """Core agent for fact-checking crisis-related content."""
    
    def __init__(self):
        self.llm = get_llm()
        # Build and compile LangGraph workflow
        self.workflow = self._create_workflow().compile()
        self.fact_check_prompt = self._create_fact_check_prompt()
        
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for the agent."""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("analyze_facts", self._analyze_facts_node) 
        workflow.add_node("process_crisis_event", self._process_crisis_event_node)
        workflow.add_node("general_response", self._general_response_node)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_message,
            {
                "facts": "analyze_facts",
                "crisis_event": "process_crisis_event", 
                "general": "general_response"
            }
        )
        
        # All nodes end the workflow
        workflow.add_edge("analyze_facts", END)
        workflow.add_edge("process_crisis_event", END)
        workflow.add_edge("general_response", END)
        
        return workflow
    
    def _create_fact_check_prompt(self) -> PromptTemplate:
        """Create the fact checking prompt template."""
        template = """You are an expert fact-checker specializing in crisis communication and corporate affairs.

Analyze the following crisis-related content for factual claims and assess their credibility:

CONTENT TO ANALYZE:
{content}

CONTEXT:
- This content is part of a potential PR crisis situation
- Focus on verifiable claims, not opinions or sentiments
- Consider source credibility and evidence availability
- Identify potential misinformation or unsubstantiated allegations

Please provide a comprehensive fact-checking analysis in the following JSON format:

{{
    "claims_identified": <total number of factual claims found>,
    "claims_verified": <number of claims that can be verified>,
    "claims_disputed": <number of claims that are false or disputed>,
    "overall_credibility": "<'high', 'medium', or 'low' based on evidence quality>",
    "fact_checks": [
        {{
            "claim": "<specific claim text>",
            "status": "<'verified', 'unverified', or 'disputed'>",
            "evidence_level": "<'high', 'medium', or 'low'>",
            "sources": ["<types of sources available, e.g., 'public records', 'allegation only', 'news reports'>"],
            "notes": "<additional context or explanation>"
        }}
    ],
    "risk_factors": ["<list of risk factors for the organization, e.g., 'lack of evidence', 'credible source', 'viral spread'>"],
    "confidence": <float between 0.0 and 1.0 indicating confidence in this analysis>,
    "misinformation_indicators": ["<potential signs of misinformation if any>"]
}}

Respond with ONLY the JSON object, no additional text or explanation."""

        return PromptTemplate(
            input_variables=["content"],
            template=template
        )
        
    async def ainvoke(self, prompt: str) -> str:
        """Async invoke the agent workflow following lungo pattern."""
        try:
            # Check if this is a fact checking request with structured data
            crisis_data = {}
            if "Please verify the claims in this crisis content:" in prompt:
                # Extract crisis content from the prompt
                content_start = prompt.find("Please verify the claims in this crisis content:") + len("Please verify the claims in this crisis content:")
                content = prompt[content_start:].strip()
                crisis_data = {"text": content, "content": content}
            
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
                    
            return "Unable to process fact checking request"
            
        except Exception as e:
            logger.error(f"Error in fact checking workflow: {e}")
            return f"Error processing fact check: {str(e)}"
    
    async def analyze_crisis_facts(self, crisis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze facts for a specific crisis event."""
        try:
            content = crisis_data.get("text", crisis_data.get("content", ""))
            if not content:
                logger.error("No content provided for fact checking")
                return self._create_error_response("No content provided")
            
            # Use LLM to analyze facts
            prompt = self.fact_check_prompt.format(content=content)
            llm_response = await self.llm.ainvoke(prompt)
            
            # Parse and validate JSON response
            try:
                raw_response = json.loads(llm_response.content)
                
                # Validate response against schema
                try:
                    validated_response = FactCheckAnalysisResponse(**raw_response)
                    
                    # Convert to dict and add metadata
                    fact_analysis = validated_response.model_dump()
                    fact_analysis.update({
                        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                        "content_analyzed": content[:200] + "..." if len(content) > 200 else content,
                        "analysis_model": "gpt-4o-mini"
                    })
                    
                    logger.info(f"Fact checking completed: {fact_analysis['overall_credibility']} credibility")
                    return fact_analysis
                    
                except ValidationError as e:
                    logger.error(f"LLM response failed schema validation: {e}")
                    return self._create_error_response(f"Invalid LLM response format: {str(e)}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM fact check response as JSON: {e}")
                return self._create_error_response("Failed to parse fact check analysis")
                
        except Exception as e:
            logger.error(f"Error in fact checking analysis: {e}")
            return self._create_error_response(f"Analysis failed: {str(e)}")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response that matches our schema."""
        error_response = {
            "claims_identified": 0,
            "claims_verified": 0,
            "claims_disputed": 0,
            "overall_credibility": "low",
            "fact_checks": [{
                "claim": "Unable to analyze",
                "status": "unverified",
                "evidence_level": "low",
                "sources": ["error"],
                "notes": error_message
            }],
            "risk_factors": ["analysis_failed"],
            "confidence": 0.0,
            "misinformation_indicators": [],
            "error": error_message,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
        return error_response
            
    def _supervisor_node(self, state: GraphState) -> GraphState:
        """Supervisor node that routes messages to appropriate handlers."""
        logger.info("Processing message in fact checker supervisor node")
        
        # Get the latest human message
        last_message = state["messages"][-1]
        user_input = last_message.content.lower()
        
        # Check if crisis data is provided for direct analysis
        if state.get("crisis_data"):
            action = "crisis_event"
        # Check if this is a fact checking request
        elif "verify claims" in user_input or "fact check" in user_input or "claims" in user_input:
            action = "facts"
        elif "status" in user_input:
            action = "general"
        else:
            # Default to fact checking for direct A2A calls
            action = "facts"
            
        state["current_action"] = action
        return state
        
    def _route_message(self, state: GraphState) -> str:
        """Route messages based on supervisor decision."""
        action = state.get("current_action", "general")
        logger.info(f"Routing to: {action}")
        return action
        
    def _analyze_facts_node(self, state: GraphState) -> GraphState:
        """Handle direct fact checking requests."""
        response_content = "Fact checking capabilities ready. " \
                          "I can verify claims in crisis-related content, " \
                          "assess credibility, and identify potential misinformation."
        
        state["messages"].append(AIMessage(content=response_content))
        return state
    
    def _process_crisis_event_node(self, state: GraphState) -> GraphState:
        """Handle crisis event processing for fact checking."""
        crisis_data = state.get("crisis_data", {})
        crisis_id = crisis_data.get("crisis_id", "unknown")
        content = crisis_data.get("text", crisis_data.get("content", "No content available"))
        
        if content and content != "No content available":
            # Note: Actual fact checking will be performed in the agent executor
            # This node just acknowledges the crisis event
            response_content = f"Processing fact check for crisis {crisis_id}: " \
                              f"'{content[:100]}...' - Analysis will be performed by the agent executor."
        else:
            response_content = f"No content available for fact checking of crisis {crisis_id}"
        
        state["messages"].append(AIMessage(content=response_content))
        return state
        
    def _general_response_node(self, state: GraphState) -> GraphState:
        """Handle general queries about fact checking."""
        response_content = "I'm the Fact Checker agent. I verify claims in " \
                          "crisis-related content, assess credibility, identify misinformation, " \
                          "and provide detailed fact-checking analysis to support crisis response decisions."
                          
        state["messages"].append(AIMessage(content=response_content))
        return state