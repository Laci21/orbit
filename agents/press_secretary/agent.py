"""Core agent logic for the Press Secretary agent."""

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

logger = logging.getLogger("orbit.press_secretary_agent.agent")

# Node states for the workflow
NodeState = Literal["SUPERVISOR", "GENERATE_RESPONSE", "PROCESS_CRISIS_EVENT", "GENERAL_RESPONSE"]


class AlternativeResponse(BaseModel):
    """Schema for alternative response options."""
    tone: str = Field(description="Response tone (defensive, apologetic, etc.)")
    statement: str = Field(description="Alternative statement text")
    

class ChannelResponses(BaseModel):
    """Schema for channel-specific responses."""
    press_release: str = Field(description="Full formal press release statement")
    social_media: str = Field(description="Concise social media post")
    employee_memo: str = Field(description="Internal employee communication")


class PressResponse(BaseModel):
    """Schema for Press Secretary response generation."""
    primary_statement: str = Field(description="Main official response statement")
    tone: str = Field(description="Primary response tone")
    key_messages: List[str] = Field(description="3-5 key messages extracted from response")
    alternatives: List[AlternativeResponse] = Field(description="Alternative response options")
    channels: ChannelResponses = Field(description="Channel-specific customized responses")
    legal_compliance: bool = Field(description="Whether response complies with legal constraints")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in response appropriateness")


class PressSecretaryState(MessagesState):
    """Extended state for Press Secretary workflow."""
    crisis_data: Dict[str, Any] = Field(default_factory=dict)
    sentiment_analysis: Dict[str, Any] = Field(default_factory=dict) 
    fact_analysis: Dict[str, Any] = Field(default_factory=dict)
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    legal_review: Dict[str, Any] = Field(default_factory=dict)
    press_response: Dict[str, Any] = Field(default_factory=dict)
    node_state: NodeState = Field(default="SUPERVISOR")


class PressSecretaryAgent:
    """Press Secretary agent for crisis response generation."""
    
    def __init__(self):
        self.llm = get_llm()
        # Build and compile LangGraph workflow
        self.workflow = self._create_workflow()
        self.response_prompt = self._create_response_prompt()
    
    def _create_response_prompt(self) -> PromptTemplate:
        """Create the response generation prompt template."""
        template = """You are an expert crisis communications specialist and press secretary. 

You need to craft an official crisis response statement based on comprehensive analysis from multiple expert sources.

CRISIS SITUATION:
{crisis_content}

EXPERT ANALYSIS SUMMARY:
Sentiment Analysis: {sentiment_summary}
Fact Check Results: {fact_summary} 
Risk Assessment: {risk_summary}
Legal Constraints: {legal_summary}

LEGAL RESTRICTIONS TO FOLLOW:
{legal_restrictions}

TASK: Generate a comprehensive crisis response package with the following components:

1. PRIMARY STATEMENT (professional_concerned tone)
2. KEY MESSAGES (3-5 bullet points)
3. ALTERNATIVE RESPONSES (2 different tones: defensive, apologetic)
4. CHANNEL-SPECIFIC VERSIONS (press release, social media, employee memo)

GUIDELINES:
- Maintain professional credibility while addressing concerns
- Incorporate factual findings appropriately
- Respect all legal constraints and restrictions
- Tailor tone and length for each communication channel
- Ensure consistency across all versions
- Be authentic and avoid corporate speak when possible

Respond with ONLY the JSON object in this exact format:

{{
    "primary_statement": "<professional_concerned tone statement>",
    "tone": "professional_concerned",
    "key_messages": [
        "<key message 1>",
        "<key message 2>", 
        "<key message 3>",
        "<key message 4>",
        "<key message 5>"
    ],
    "alternatives": [
        {{
            "tone": "defensive",
            "statement": "<defensive tone statement>"
        }},
        {{
            "tone": "apologetic", 
            "statement": "<apologetic tone statement>"
        }}
    ],
    "channels": {{
        "press_release": "<formal 200-300 word press release>",
        "social_media": "<concise 280 character social media post>",
        "employee_memo": "<internal employee communication 150-200 words>"
    }},
    "legal_compliance": true,
    "confidence": <float 0.0-1.0>
}}

Respond with ONLY the JSON object, no additional text or explanation."""

        return PromptTemplate(
            input_variables=["crisis_content", "sentiment_summary", "fact_summary", "risk_summary", "legal_summary", "legal_restrictions"],
            template=template
        )
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for press response generation."""
        workflow = StateGraph(PressSecretaryState)
        
        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("process_crisis_event", self._process_crisis_event_node)
        workflow.add_node("general_response", self._general_response_node)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Add edges
        workflow.add_conditional_edges(
            "supervisor",
            self._route_request,
            {
                "GENERATE_RESPONSE": "generate_response",
                "PROCESS_CRISIS_EVENT": "process_crisis_event", 
                "GENERAL_RESPONSE": "general_response"
            }
        )
        
        workflow.add_edge("generate_response", END)
        workflow.add_edge("process_crisis_event", END)
        workflow.add_edge("general_response", END)
        
        return workflow.compile()
    
    def _supervisor_node(self, state: PressSecretaryState) -> PressSecretaryState:
        """Supervisor node to route requests."""
        if state["messages"]:
            last_message = state["messages"][-1]
            if isinstance(last_message, HumanMessage):
                content = last_message.content.lower()
                
                if "generate crisis response" in content:
                    state["node_state"] = "GENERATE_RESPONSE"
                elif "process crisis event" in content:
                    state["node_state"] = "PROCESS_CRISIS_EVENT"
                else:
                    state["node_state"] = "GENERAL_RESPONSE"
        
        return state
    
    def _route_request(self, state: PressSecretaryState) -> str:
        """Route request based on supervisor decision."""
        return state["node_state"]
    
    def _generate_response_node(self, state: PressSecretaryState) -> PressSecretaryState:
        """Generate crisis response using LLM."""
        try:
            # Extract data from state
            crisis_data = state.get("crisis_data", {})
            sentiment_analysis = state.get("sentiment_analysis", {})
            fact_analysis = state.get("fact_analysis", {})
            risk_assessment = state.get("risk_assessment", {})
            legal_review = state.get("legal_review", {})
            
            # Create summaries for the prompt
            crisis_content = crisis_data.get("content", crisis_data.get("text", ""))
            sentiment_summary = f"Overall sentiment: {sentiment_analysis.get('overall_sentiment', 'unknown')}, Risk: {sentiment_analysis.get('reputational_risk', 'unknown')}"
            fact_summary = f"Accuracy: {fact_analysis.get('overall_accuracy', 'unknown')}, Verified claims: {len(fact_analysis.get('claim_verification', []))}"
            risk_summary = f"Risk score: {risk_assessment.get('overall_risk_score', 'unknown')}/10, Level: {risk_assessment.get('risk_level', 'unknown')}"
            legal_summary = f"Legal risk: {legal_review.get('legal_risk', 'unknown')}, Escalation needed: {legal_review.get('escalation_needed', 'unknown')}"
            legal_restrictions = ", ".join(legal_review.get('restrictions', ['None specified']))
            
            # Generate response using LLM
            prompt = self.response_prompt.format(
                crisis_content=crisis_content,
                sentiment_summary=sentiment_summary,
                fact_summary=fact_summary,
                risk_summary=risk_summary,
                legal_summary=legal_summary,
                legal_restrictions=legal_restrictions
            )
            
            llm_response = self.llm.ainvoke(prompt)
            
            # Parse and validate JSON response
            try:
                raw_response = json.loads(llm_response.content)
                validated_response = PressResponse(**raw_response)
                
                state["press_response"] = validated_response.model_dump()
                
                # Add success message
                state["messages"] = add_messages(state["messages"], [
                    AIMessage(content=f"Crisis response generated successfully. Primary tone: {validated_response.tone}")
                ])
                
                logger.info(f"Press response generated with tone: {validated_response.tone}")
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Failed to parse/validate LLM response: {e}")
                state["messages"] = add_messages(state["messages"], [
                    AIMessage(content="Failed to generate crisis response - invalid format")
                ])
                
        except Exception as e:
            logger.error(f"Error in response generation: {e}")
            state["messages"] = add_messages(state["messages"], [
                AIMessage(content=f"Error generating crisis response: {str(e)}")
            ])
        
        return state
    
    def _process_crisis_event_node(self, state: PressSecretaryState) -> PressSecretaryState:
        """Process crisis event and coordinate response generation."""
        try:
            # This would handle parsing incoming crisis data with all agent outputs
            state["messages"] = add_messages(state["messages"], [
                AIMessage(content="Crisis event processed, ready for response generation")
            ])
            
        except Exception as e:
            logger.error(f"Error processing crisis event: {e}")
            state["messages"] = add_messages(state["messages"], [
                AIMessage(content=f"Error processing crisis event: {str(e)}")
            ])
        
        return state
    
    def _general_response_node(self, state: PressSecretaryState) -> PressSecretaryState:
        """Handle general queries about press response capabilities."""
        state["messages"] = add_messages(state["messages"], [
            AIMessage(content="I am the Press Secretary agent. I generate official crisis response statements based on comprehensive analysis from sentiment, fact-checking, risk assessment, and legal review agents.")
        ])
        return state
    
    async def ainvoke(self, prompt: str) -> str:
        """Async invoke the agent workflow following lungo pattern."""
        try:
            state = PressSecretaryState(
                messages=[HumanMessage(content=prompt)]
            )
            
            result = await self.workflow.ainvoke(state)
            
            # Return the last AI message
            if result["messages"]:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    return last_message.content
                    
            return "Unable to process press response request"
            
        except Exception as e:
            logger.error(f"Error in press response workflow: {e}")
            return f"Error processing press response: {str(e)}"
    
    async def generate_crisis_response(self, crisis_data: Dict[str, Any], sentiment_analysis: Dict[str, Any], 
                                     fact_analysis: Dict[str, Any], risk_assessment: Dict[str, Any], 
                                     legal_review: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive crisis response based on all agent analyses."""
        try:
            # Create summaries for the prompt
            crisis_content = crisis_data.get("content", crisis_data.get("text", ""))
            sentiment_summary = f"Overall sentiment: {sentiment_analysis.get('overall_sentiment', 'unknown')}, Risk: {sentiment_analysis.get('reputational_risk', 'unknown')}"
            fact_summary = f"Accuracy: {fact_analysis.get('overall_accuracy', 'unknown')}, Verified claims: {len(fact_analysis.get('claim_verification', []))}"
            risk_summary = f"Risk score: {risk_assessment.get('overall_risk_score', 'unknown')}/10, Level: {risk_assessment.get('risk_level', 'unknown')}"
            legal_summary = f"Legal risk: {legal_review.get('legal_risk', 'unknown')}, Escalation needed: {legal_review.get('escalation_needed', 'unknown')}"
            legal_restrictions = ", ".join(legal_review.get('restrictions', ['None specified']))
            
            # Generate response using LLM
            prompt = self.response_prompt.format(
                crisis_content=crisis_content,
                sentiment_summary=sentiment_summary,
                fact_summary=fact_summary,
                risk_summary=risk_summary,
                legal_summary=legal_summary,
                legal_restrictions=legal_restrictions
            )
            
            llm_response = await self.llm.ainvoke(prompt)
            
            # Parse and validate JSON response
            try:
                raw_response = json.loads(llm_response.content)
                validated_response = PressResponse(**raw_response)
                
                # Convert to dict and add metadata
                press_response = validated_response.model_dump()
                press_response.update({
                    "response_timestamp": datetime.now(timezone.utc).isoformat(),
                    "crisis_id": crisis_data.get("id", "unknown"),
                    "analysis_model": "gpt-4o"
                })
                
                logger.info(f"Crisis response generated: {press_response['tone']} tone")
                return press_response
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"LLM response failed validation: {e}")
                return self._create_error_response(f"Invalid LLM response format: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error in crisis response generation: {e}")
            return self._create_error_response(str(e))
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response for failed crisis response generation."""
        return {
            "primary_statement": "We are aware of the situation and are reviewing it carefully.",
            "tone": "professional_concerned",
            "key_messages": ["Situation under review", "More information to follow"],
            "alternatives": [
                {"tone": "defensive", "statement": "We are reviewing these claims carefully."},
                {"tone": "apologetic", "statement": "We apologize for any concerns this may have caused."}
            ],
            "channels": {
                "press_release": "We are aware of the situation and are reviewing it carefully. More information will be provided as it becomes available.",
                "social_media": "We are reviewing the situation and will provide updates soon.",
                "employee_memo": "Team, we are aware of recent developments and are reviewing the situation. Updates will be shared as appropriate."
            },
            "legal_compliance": True,
            "confidence": 0.1,
            "error": f"Response generation failed: {error_message}",
            "response_timestamp": datetime.now(timezone.utc).isoformat()
        } 