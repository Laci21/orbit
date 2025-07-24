# Technical Implementation Guide - Orbit Crisis Management System

This document provides detailed technical guidance for implementing the event-driven multi-agent architecture in the Orbit system.

## Architecture Overview

### Event-Driven Multi-Agent System
- **SLIM Transport**: Central message broker for agent communication
- **Dual Bridge Pattern**: Transport bridge (A2A) + Broadcast bridge (events)
- **Dependency Management**: Agents wait for prerequisite events before processing
- **Parallel Processing**: Independent agents process simultaneously when possible

### Communication Flow

```
SLIM Broker (ghcr.io/agntcy/slim:0.3.15)
    ↕️
Agent Bridges (Transport + Broadcast)
    ↕️
Agent Event Handlers
    ↕️
Agent Business Logic
```

## SLIM Message Implementation

### SLIMMessage Class
All agents must use the standardized SLIMMessage format for transport compatibility:

```python
class SLIMMessage:
    """Message format compatible with SLIM transport."""
    def __init__(self, payload):
        self.payload = payload
        self.headers = {}
        self.reply_to = None
        self.correlation_id = None  
        self.message_id = None
        
    def serialize(self):
        """Serialize message for SLIM transport."""
        import json
        data = {
            'payload': self.payload,
            'headers': self.headers,
            'reply_to': self.reply_to,
            'correlation_id': self.correlation_id,
            'message_id': self.message_id
        }
        return json.dumps(data).encode('utf-8')
```

### Event Publishing Pattern

```python
async def publish_event(self, event_type: str, data: dict):
    """Publish event to SLIM transport."""
    event_payload = {
        "event_type": event_type,
        "agent_id": self.agent_id,
        "timestamp": datetime.utcnow().isoformat(),
        "crisis_id": self.current_crisis_id,
        **data
    }
    
    message = SLIMMessage(payload=event_payload)
    
    if self.transport:
        await self.transport.publish(
            topic=f"orbit.{event_type}",
            message=message
        )
```

## Agent Implementation Template

### Base Agent Structure

```python
"""Template for implementing Orbit crisis management agents."""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import Message, Role, TextPart, Part
from agntcy_app_sdk.factory import GatewayFactory

class BaseOrbitAgent:
    """Base class for Orbit crisis management agents."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.transport = None
        self.subscribed_topics = []
        self.current_crisis_id = None
        self.logger = logging.getLogger(f"orbit.{agent_id}")
        
    async def initialize(self):
        """Initialize agent with SLIM transport."""
        factory = GatewayFactory()
        self.transport = factory.create_transport(
            "SLIM", 
            endpoint=self.config.get("transport_endpoint", "http://localhost:46357")
        )
        
    async def subscribe_to_events(self, topics: List[str]):
        """Subscribe to relevant SLIM topics."""
        self.subscribed_topics = topics
        # TODO: Implement SLIM subscription mechanism
        
    async def handle_event(self, event: Dict[str, Any]):
        """Handle incoming event - override in subclasses."""
        event_type = event.get("event_type")
        self.logger.info(f"Received event: {event_type}")
        
        if event_type == "crisis_detected":
            await self.handle_crisis_detected(event)
        elif event_type == "fact_check_complete":
            await self.handle_fact_check_complete(event)
        # Add other event handlers as needed
            
    async def handle_crisis_detected(self, event: Dict[str, Any]):
        """Handle crisis detection event - override in subclasses."""
        pass
        
    async def publish_completion(self, result_data: Dict[str, Any]):
        """Publish completion event."""
        await self.publish_event(f"{self.agent_id.replace('-', '_')}_complete", result_data)
```

### Agent-Specific Implementation

```python
class SentimentAnalystAgent(BaseOrbitAgent):
    """Sentiment analysis agent implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("sentiment-analyst-agent", config)
        self.openai_client = None  # Initialize OpenAI client
        
    async def initialize(self):
        """Initialize sentiment analyst with LLM."""
        await super().initialize()
        await self.subscribe_to_events(["orbit.crisis.detected"])
        
    async def handle_crisis_detected(self, event: Dict[str, Any]):
        """Analyze sentiment for detected crisis."""
        crisis_data = event.get("crisis", {})
        content = crisis_data.get("content", "")
        
        # Perform sentiment analysis
        sentiment_result = await self.analyze_sentiment(content)
        
        # Publish completion event
        await self.publish_completion({
            "analysis": sentiment_result,
            "crisis_id": event.get("crisis_id")
        })
        
    async def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """Perform LLM-based sentiment analysis."""
        # TODO: Implement OpenAI/LangChain sentiment analysis
        return {
            "overall_sentiment": -0.7,
            "confidence": 0.85,
            "emotions": ["anger", "concern"]
        }
```

## Dependency Management Implementation

### Waiting for Multiple Events

```python
class RiskScoreAgent(BaseOrbitAgent):
    """Risk score agent with dependency management."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("risk-score-agent", config)
        self.waiting_for = {"fact_check": False, "sentiment": False}
        self.collected_data = {}
        
    async def initialize(self):
        await super().initialize()
        await self.subscribe_to_events([
            "orbit.fact.complete",
            "orbit.sentiment.complete"
        ])
        
    async def handle_event(self, event: Dict[str, Any]):
        """Handle dependency events."""
        event_type = event.get("event_type")
        
        if event_type == "fact_check_complete":
            self.waiting_for["fact_check"] = True
            self.collected_data["fact_data"] = event
            
        elif event_type == "sentiment_analysis_complete":
            self.waiting_for["sentiment"] = True
            self.collected_data["sentiment_data"] = event
            
        # Check if all dependencies are met
        if all(self.waiting_for.values()):
            await self.calculate_risk_score()
            
    async def calculate_risk_score(self):
        """Calculate risk score using all collected data."""
        fact_data = self.collected_data["fact_data"]
        sentiment_data = self.collected_data["sentiment_data"]
        
        # Combine data to calculate risk score
        risk_result = await self.assess_risk(fact_data, sentiment_data)
        
        await self.publish_completion(risk_result)
        
        # Reset for next crisis
        self.waiting_for = {"fact_check": False, "sentiment": False}
        self.collected_data = {}
```

## Server Setup Pattern

### Agent Server Implementation

```python
"""Server setup for individual agents."""

import asyncio
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from agntcy_app_sdk.factory import GatewayFactory

class OrbitAgentServer:
    """Generic server for Orbit agents."""
    
    def __init__(self, agent_card, agent_executor, config):
        self.agent_card = agent_card
        self.agent_executor = agent_executor
        self.config = config
        self.transport = None
        self.app = None
        
    async def start(self):
        """Start agent server with dual bridge pattern."""
        # Create A2A application
        request_handler = DefaultRequestHandler(
            agent_executor=self.agent_executor,
            task_store=InMemoryTaskStore()
        )
        
        self.app = A2AStarletteApplication(
            agent_card=self.agent_card,
            http_handler=request_handler
        )
        
        # Create SLIM transport
        factory = GatewayFactory()
        self.transport = factory.create_transport(
            "SLIM", 
            endpoint=self.config.transport_endpoint
        )
        
        # Create dual bridges
        tasks = []
        
        # Transport bridge for A2A communication
        transport_bridge = factory.create_bridge(self.app, transport=self.transport)
        tasks.append(asyncio.create_task(transport_bridge.start()))
        
        # Broadcast bridge for event communication
        broadcast_bridge = factory.create_bridge(
            self.app,
            transport=self.transport,
            topic=self.config.broadcast_topic
        )
        tasks.append(asyncio.create_task(broadcast_bridge.start()))
        
        # Start event processing service
        if hasattr(self.agent_executor, 'event_service'):
            tasks.append(asyncio.create_task(self.agent_executor.event_service.start()))
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
```

## Testing Framework

### Agent Testing Pattern

```python
"""Testing framework for Orbit agents."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from your_agent import YourAgent

@pytest.fixture
async def agent():
    """Create agent instance for testing."""
    config = {"transport_endpoint": "http://test:46357"}
    agent = YourAgent(config)
    agent.transport = AsyncMock()  # Mock SLIM transport
    return agent

@pytest.mark.asyncio
async def test_crisis_detection_handling(agent):
    """Test agent handles crisis detection events."""
    crisis_event = {
        "event_type": "crisis_detected",
        "crisis_id": "test_001",
        "crisis": {"content": "Test crisis content"}
    }
    
    # Mock agent processing
    agent.process_crisis = AsyncMock(return_value={"result": "processed"})
    
    # Handle event
    await agent.handle_event(crisis_event)
    
    # Verify processing was called
    agent.process_crisis.assert_called_once()
    
    # Verify completion event was published
    agent.transport.publish.assert_called_once()

@pytest.mark.asyncio  
async def test_dependency_management(risk_agent):
    """Test agent waits for all dependencies."""
    # Send first dependency
    await risk_agent.handle_event({
        "event_type": "fact_check_complete",
        "data": "fact_result"
    })
    
    # Verify agent hasn't processed yet
    assert not risk_agent.transport.publish.called
    
    # Send second dependency
    await risk_agent.handle_event({
        "event_type": "sentiment_analysis_complete", 
        "data": "sentiment_result"
    })
    
    # Verify agent now processes and publishes
    risk_agent.transport.publish.assert_called_once()
```

## Deployment Configuration

### Docker Compose Integration

```yaml
# Example agent service in docker-compose.yml
sentiment-analyst:
  build:
    context: .
    dockerfile: docker/Dockerfile.sentiment-analyst
  environment:
    - AGENT_PORT=9002
    - SLIM_BROKER_URL=http://slim:46357
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - BROADCAST_TOPIC=orbit.sentiment.events
  depends_on:
    - slim
  networks:
    - orbit-network
```

### Environment Configuration

```python
# Agent configuration class
class AgentConfig:
    """Configuration for Orbit agents."""
    
    def __init__(self):
        self.agent_port = int(os.getenv("AGENT_PORT", "9001"))
        self.transport_endpoint = os.getenv("SLIM_BROKER_URL", "http://localhost:46357")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.broadcast_topic = os.getenv("BROADCAST_TOPIC", "orbit.events")
        
        self._validate()
        
    def _validate(self):
        """Validate required configuration."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
```

This technical implementation guide provides the foundation for building robust, event-driven agents that communicate effectively through SLIM transport while maintaining proper dependency management and error handling.