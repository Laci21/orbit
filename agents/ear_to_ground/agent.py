"""Core agent logic for the Ear-to-Ground agent."""

import json
import logging
import os
from typing import Dict, List, Any, Literal

from langgraph.graph import MessagesState, StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langgraph.graph.message import add_messages
from typing_extensions import Annotated

from common.llm import get_llm

logger = logging.getLogger(__name__)

# Node states for the workflow
NodeState = Literal["SUPERVISOR", "STREAM_TWEETS", "MONITOR_STATUS", "GENERAL_RESPONSE"]


class GraphState(MessagesState):
    """Graph state extending MessagesState."""
    messages: Annotated[list, add_messages]
    current_action: str = ""
    streaming_status: str = "idle"


class EarToGroundAgent:
    """Core agent for monitoring and streaming crisis-related social media posts."""
    
    def __init__(self):
        self.tweet_file = os.getenv("ORBIT_TWEET_FILE", "data/tweets_astronomer.json")
        self.tweets: List[Dict[str, Any]] = []
        self._load_tweets()
        # Build and compile LangGraph workflow
        self.workflow = self._create_workflow().compile()
        
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for the agent."""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("stream_tweets", self._stream_tweets_node) 
        workflow.add_node("monitor_status", self._monitor_status_node)
        workflow.add_node("general_response", self._general_response_node)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_message,
            {
                "stream": "stream_tweets",
                "status": "monitor_status", 
                "general": "general_response"
            }
        )
        
        # All nodes end the workflow
        workflow.add_edge("stream_tweets", END)
        workflow.add_edge("monitor_status", END)
        workflow.add_edge("general_response", END)
        
        return workflow
        
    async def ainvoke(self, prompt: str) -> str:
        """Async invoke the agent workflow."""
        try:
            logger.info(f"EarToGroundAgent.ainvoke called with prompt: {prompt}")
            state = GraphState(
                messages=[HumanMessage(content=prompt)],
                current_action="",
                streaming_status="active"  # Streaming is handled by server
            )
            
            logger.info("Calling workflow.ainvoke...")
            result = await self.workflow.ainvoke(state)
            logger.info(f"Workflow result: {result}")
            
            # Return the last AI message
            if result["messages"]:
                last_message = result["messages"][-1]
                logger.info(f"Last message: {last_message}, type: {type(last_message)}")
                if isinstance(last_message, AIMessage):
                    logger.info(f"AI message content: {last_message.content}")
                    content = last_message.content
                    if content is None:
                        logger.error("AI message content is None!")
                        return "Error: AI message content is None"
                    return content
                else:
                    logger.error(f"Last message is not AIMessage: {type(last_message)}")
                    
            logger.error("No messages in result")
            return "Unable to process request"
            
        except Exception as e:
            logger.error(f"Error in agent workflow: {e}")
            return f"Error processing request: {str(e)}"
            
    def _supervisor_node(self, state: GraphState) -> GraphState:
        """Supervisor node that routes messages to appropriate handlers."""
        logger.info("Processing message in supervisor node")
        
        # Get the latest human message
        last_message = state["messages"][-1]
        user_input = last_message.content.lower()
        
        # Determine intent and route
        if "stream" in user_input or "start" in user_input or "tweets" in user_input:
            action = "stream"
        elif "status" in user_input or "monitor" in user_input:
            action = "status"  
        else:
            action = "general"
            
        state["current_action"] = action
        return state
        
    def _route_message(self, state: GraphState) -> str:
        """Route messages based on supervisor decision."""
        action = state.get("current_action", "general")
        logger.info(f"Routing to: {action}")
        return action
        
    def _stream_tweets_node(self, state: GraphState) -> GraphState:
        """Handle tweet streaming requests."""
        response_content = f"Initiating tweet streaming from {len(self.tweets)} crisis tweets. " \
                          f"Monitoring {self.tweet_file} for social media activity."
        
        state["messages"].append(AIMessage(content=response_content))
        state["streaming_status"] = "active"
        return state
        
    def _monitor_status_node(self, state: GraphState) -> GraphState:
        """Handle status monitoring requests."""
        summary = self.get_tweet_summary()
        response_content = f"Crisis monitoring status: {summary['total_tweets']} tweets loaded, " \
                          f"{summary['total_engagement']} total engagement, " \
                          f"streaming status: {self._get_streaming_status()}"
                          
        state["messages"].append(AIMessage(content=response_content))
        return state
        
    def _general_response_node(self, state: GraphState) -> GraphState:
        """Handle general queries about the monitoring system."""
        response_content = "I'm the Ear-to-Ground monitoring agent. I can stream crisis tweets, " \
                          "provide status updates, and monitor social media for PR crises. " \
                          "Ask me to 'start streaming' or check 'status'."
                          
        state["messages"].append(AIMessage(content=response_content))
        return state
        
    def _get_streaming_status(self) -> str:
        """Get current streaming status."""
        return "active"  # Streaming is handled by server
        
    def _load_tweets(self) -> None:
        """Load tweets from JSON file."""
        try:
            with open(self.tweet_file, 'r') as f:
                self.tweets = json.load(f)
            logger.info(f"Loaded {len(self.tweets)} tweets from {self.tweet_file}")
        except FileNotFoundError:
            logger.error(f"Tweet file not found: {self.tweet_file}")
            self.tweets = []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing tweet file: {e}")
            self.tweets = []
            
    def get_tweet_count(self) -> int:
        """Get total number of tweets available."""
        return len(self.tweets)
        
    def get_sample_tweet(self) -> Dict[str, Any] | None:
        """Get a sample tweet for demonstration."""
        return self.tweets[0] if self.tweets else None
        
    def get_crisis_keywords(self) -> List[str]:
        """Extract crisis-related keywords from all tweets."""
        keywords = set()
        for tweet in self.tweets:
            if "sentiment_keywords" in tweet:
                keywords.update(tweet["sentiment_keywords"])
        return list(keywords)
        
    def get_tweet_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the tweet dataset."""
        if not self.tweets:
            return {"total_tweets": 0}
            
        total_engagement = sum(
            tweet.get("retweets", 0) + tweet.get("likes", 0) + tweet.get("replies", 0)
            for tweet in self.tweets
        )
        
        verified_count = sum(1 for tweet in self.tweets if tweet.get("verified", False))
        
        return {
            "total_tweets": len(self.tweets),
            "total_engagement": total_engagement,
            "verified_authors": verified_count,
            "unverified_authors": len(self.tweets) - verified_count,
            "keywords": self.get_crisis_keywords()[:10]  # Top 10 keywords
        }