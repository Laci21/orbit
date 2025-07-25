"""Core agent logic for the Sentiment Analyst agent."""

import json
import logging
import os
from typing import Dict, List, Any, Literal
from datetime import datetime

from langgraph.graph import MessagesState, StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph.message import add_messages
from typing_extensions import Annotated
from pydantic import BaseModel, Field, ValidationError

from common.llm import get_llm

logger = logging.getLogger("orbit.sentiment_analyst_agent.agent")

# Node states for the workflow
NodeState = Literal["SUPERVISOR", "ANALYZE_SENTIMENT", "PROCESS_CRISIS_EVENT", "GENERAL_RESPONSE"]


class SentimentDistribution(BaseModel):
    """Schema for sentiment distribution breakdown."""
    negative: float = Field(ge=0.0, le=1.0, description="Percentage of negative sentiment")
    neutral: float = Field(ge=0.0, le=1.0, description="Percentage of neutral sentiment")  
    positive: float = Field(ge=0.0, le=1.0, description="Percentage of positive sentiment")
    
    def model_post_init(self, __context) -> None:
        """Validate that percentages sum to approximately 1.0."""
        total = self.negative + self.neutral + self.positive
        if not (0.95 <= total <= 1.05):  # Allow small floating point errors
            raise ValueError(f"Sentiment percentages must sum to 1.0, got {total}")


class SentimentAnalysisResponse(BaseModel):
    """Schema for validating LLM sentiment analysis response."""
    overall_sentiment: float = Field(
        ge=-1.0, le=1.0, 
        description="Overall sentiment score from -1.0 (very negative) to 1.0 (very positive)"
    )
    sentiment_distribution: SentimentDistribution = Field(
        description="Breakdown of sentiment percentages"
    )
    key_emotions: List[str] = Field(
        min_length=1, max_length=10,
        description="List of primary emotions detected"
    )
    emotional_intensity: float = Field(
        ge=0.0, le=1.0,
        description="Emotional intensity from 0.0 (calm) to 1.0 (highly emotional)"
    )
    crisis_indicators: List[str] = Field(
        default_factory=list,
        description="List of sentiment-based crisis risk factors"
    )
    public_reaction_summary: str = Field(
        min_length=10, max_length=500,
        description="Brief summary of public emotional response"
    )
    trend_direction: Literal["escalating", "stable", "de-escalating"] = Field(
        description="Sentiment trend direction"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score for the analysis"
    )
    reputational_risk: Literal["low", "medium", "high", "critical"] = Field(
        description="Assessed reputational risk level"
    )


class GraphState(MessagesState):
    """Graph state extending MessagesState."""
    messages: Annotated[list, add_messages]
    current_action: str = ""
    crisis_data: Dict[str, Any] = {}
    sentiment_result: Dict[str, Any] = {}


class SentimentAnalystAgent:
    """Core agent for analyzing sentiment from crisis-related social media content."""
    
    def __init__(self):
        self.llm = get_llm()
        # Build and compile LangGraph workflow
        self.workflow = self._create_workflow().compile()
        self.sentiment_prompt = self._create_sentiment_prompt()
        
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for the agent."""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("analyze_sentiment", self._analyze_sentiment_node) 
        workflow.add_node("process_crisis_event", self._process_crisis_event_node)
        workflow.add_node("general_response", self._general_response_node)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_message,
            {
                "sentiment": "analyze_sentiment",
                "crisis_event": "process_crisis_event", 
                "general": "general_response"
            }
        )
        
        # All nodes end the workflow
        workflow.add_edge("analyze_sentiment", END)
        workflow.add_edge("process_crisis_event", END)
        workflow.add_edge("general_response", END)
        
        return workflow
    
    def _create_sentiment_prompt(self) -> PromptTemplate:
        """Create the sentiment analysis prompt template."""
        template = """You are an expert sentiment analyst specializing in crisis communication and public relations.

Analyze the sentiment of the following social media content related to a potential PR crisis:

CONTENT TO ANALYZE:
{content}

CONTEXT:
- This content is part of a potential PR crisis situation
- Focus on public sentiment, emotional reactions, and potential reputational impact
- Consider both explicit sentiment and underlying emotional themes

Please provide a comprehensive sentiment analysis in the following JSON format:

{{
    "overall_sentiment": <float between -1.0 (very negative) and 1.0 (very positive)>,
    "sentiment_distribution": {{
        "negative": <percentage as decimal 0.0-1.0>,
        "neutral": <percentage as decimal 0.0-1.0>,
        "positive": <percentage as decimal 0.0-1.0>
    }},
    "key_emotions": [<list of 3-5 primary emotions detected, e.g., "anger", "disappointment", "concern", "shock", "outrage">],
    "emotional_intensity": <float between 0.0 (calm) and 1.0 (highly emotional)>,
    "crisis_indicators": [<list of sentiment-based crisis risk factors>],
    "public_reaction_summary": "<brief 1-2 sentence summary of the public's emotional response>",
    "trend_direction": "<'escalating', 'stable', or 'de-escalating' based on content tone>",
    "confidence": <float between 0.0 and 1.0 indicating confidence in this analysis>,
    "reputational_risk": "<'low', 'medium', 'high', or 'critical' based on sentiment severity>"
}}

Respond with ONLY the JSON object, no additional text or explanation."""

        return PromptTemplate(
            input_variables=["content"],
            template=template
        )
        
    async def ainvoke(self, prompt: str) -> str:
        """Async invoke the agent workflow following lungo pattern."""
        try:
            # Check if this is a crisis analysis request with structured data
            crisis_data = {}
            if "Please analyze the sentiment of this crisis content:" in prompt:
                # Extract crisis content from the prompt
                content_start = prompt.find("Please analyze the sentiment of this crisis content:") + len("Please analyze the sentiment of this crisis content:")
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
                    
            return "Unable to process sentiment analysis request"
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis workflow: {e}")
            return f"Error processing sentiment analysis: {str(e)}"
    
    async def analyze_crisis_sentiment(self, crisis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment for a specific crisis event."""
        try:
            content = crisis_data.get("text", crisis_data.get("content", ""))
            if not content:
                logger.error("No content provided for sentiment analysis")
                return self._create_error_response("No content provided")
            
            # Use LLM to analyze sentiment
            prompt = self.sentiment_prompt.format(content=content)
            llm_response = await self.llm.ainvoke(prompt)
            
            # Parse and validate JSON response
            try:
                raw_response = json.loads(llm_response.content)
                
                # Validate response against schema
                try:
                    validated_response = SentimentAnalysisResponse(**raw_response)
                    
                    # Convert to dict and add metadata
                    sentiment_analysis = validated_response.model_dump()
                    sentiment_analysis.update({
                        "analysis_timestamp": datetime.now(datetime.UTC).isoformat(),
                        "content_analyzed": content[:200] + "..." if len(content) > 200 else content,
                        "analysis_model": "gpt-4o-mini"
                    })
                    
                    logger.info(f"Sentiment analysis completed: {sentiment_analysis['overall_sentiment']:.2f}")
                    return sentiment_analysis
                    
                except ValidationError as e:
                    logger.error(f"LLM response failed schema validation: {e}")
                    return self._create_error_response(f"Invalid LLM response format: {str(e)}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM sentiment response as JSON: {e}")
                return self._create_error_response("Failed to parse sentiment analysis")
                
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return self._create_error_response(f"Analysis failed: {str(e)}")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response that matches our schema."""
        error_response = {
            "overall_sentiment": 0.0,
            "sentiment_distribution": {"negative": 0.0, "neutral": 1.0, "positive": 0.0},
            "key_emotions": ["unknown"],
            "emotional_intensity": 0.0,
            "crisis_indicators": [],
            "public_reaction_summary": "Unable to analyze sentiment due to error",
            "trend_direction": "stable",  # Use valid enum value
            "confidence": 0.0,
            "reputational_risk": "low",  # Use valid enum value
            "error": error_message,
            "analysis_timestamp": datetime.now(datetime.UTC).isoformat()
        }
        return error_response
            
    def _supervisor_node(self, state: GraphState) -> GraphState:
        """Supervisor node that routes messages to appropriate handlers."""
        logger.info("Processing message in sentiment analyst supervisor node")
        
        # Get the latest human message
        last_message = state["messages"][-1]
        user_input = last_message.content.lower()
        
        # Check if crisis data is provided for direct analysis
        if state.get("crisis_data"):
            action = "crisis_event"
        # Check if this is a crisis analysis request
        elif "analyze sentiment" in user_input or "crisis" in user_input:
            action = "sentiment"
        elif "status" in user_input:
            action = "general"
        else:
            # Default to sentiment analysis for direct A2A calls
            action = "sentiment"
            
        state["current_action"] = action
        return state
        
    def _route_message(self, state: GraphState) -> str:
        """Route messages based on supervisor decision."""
        action = state.get("current_action", "general")
        logger.info(f"Routing to: {action}")
        return action
        
    def _analyze_sentiment_node(self, state: GraphState) -> GraphState:
        """Handle direct sentiment analysis requests."""
        response_content = "Sentiment analysis capabilities ready. " \
                          "I can analyze public sentiment from crisis-related social media content " \
                          "to assess emotional impact and reputational risk."
        
        state["messages"].append(AIMessage(content=response_content))
        return state
    
    def _process_crisis_event_node(self, state: GraphState) -> GraphState:
        """Handle crisis event processing for sentiment analysis."""
        crisis_data = state.get("crisis_data", {})
        crisis_id = crisis_data.get("crisis_id", "unknown")
        content = crisis_data.get("text", crisis_data.get("content", "No content available"))
        
        if content and content != "No content available":
            # Note: Actual sentiment analysis will be performed in the agent executor
            # This node just acknowledges the crisis event
            response_content = f"Processing sentiment analysis for crisis {crisis_id}: " \
                              f"'{content[:100]}...' - Analysis will be performed by the agent executor."
        else:
            response_content = f"No content available for sentiment analysis of crisis {crisis_id}"
        
        state["messages"].append(AIMessage(content=response_content))
        return state
        
    def _general_response_node(self, state: GraphState) -> GraphState:
        """Handle general queries about sentiment analysis."""
        response_content = "I'm the Sentiment Analyst agent. I analyze public sentiment from " \
                          "crisis-related social media content to assess emotional impact, " \
                          "identify key emotions, and evaluate reputational risk. " \
                          "I subscribe to crisis events and publish sentiment analysis results."
                          
        state["messages"].append(AIMessage(content=response_content))
        return state