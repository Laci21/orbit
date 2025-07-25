# Orbit – Direct Agent Communication Architecture

## System Overview

The Orbit system uses a **direct agent communication architecture** where AI agents coordinate through JSON-RPC A2A calls to handle PR crises autonomously. The gateway provides REST APIs for frontend monitoring and control.

## High-Level Architecture

```mermaid
graph TD
  subgraph "Frontend Layer"
    BrowserUI["React Dashboard\n(Crisis Command Center)"]
  end

  subgraph "Gateway Layer"
    Gateway["FastAPI Gateway\n(Agent Orchestration)"]
  end

  subgraph "AI Agent Layer"
    Ear["Ear-to-Ground\n:9001"]
    Sent["Sentiment Analyst\n:9002"]
    Risk["Risk Score\n:9003"]
    Fact["Fact Checker\n:9004"]
    Legal["Legal Counsel\n:9005"]
    Press["Press Secretary\n:9006"]
  end

  subgraph "Data Layer"
    TweetData["Crisis Tweet Data"]
    Playbook["Crisis Playbook"]
    LegalRubric["Legal Guidelines"]
  end

  BrowserUI <--> |"REST API"| Gateway
  Gateway <--> |"JSON-RPC A2A"| Ear
  Gateway <--> |"JSON-RPC A2A"| Sent
  Gateway <--> |"JSON-RPC A2A"| Risk
  Gateway <--> |"JSON-RPC A2A"| Fact
  Gateway <--> |"JSON-RPC A2A"| Legal
  Gateway <--> |"JSON-RPC A2A"| Press
  
  Ear --> |"JSON-RPC A2A"| Sent
  Ear --> |"JSON-RPC A2A"| Fact
  
  Fact --> |"JSON-RPC A2A"| Legal
  Sent --> |"JSON-RPC A2A"| Risk
  Fact --> |"JSON-RPC A2A"| Risk
  
  Risk --> |"JSON-RPC A2A"| Press
  Legal --> |"JSON-RPC A2A"| Press
  
  Risk --> |"JSON-RPC A2A"| Press
  Legal --> |"JSON-RPC A2A"| Press
  
  TweetData --> Ear
  Playbook --> Fact
  LegalRubric --> Legal
```

## Event-Driven Crisis Flow

```mermaid
sequenceDiagram
    participant Tweet as Tweet Stream
    participant Ear as Ear-to-Ground
    participant SLIM as SLIM Broker
    participant Fact as Fact Checker
    participant Sent as Sentiment Analyst
    participant Risk as Risk Score
    participant Legal as Legal Counsel
    participant Press as Press Secretary
    participant UI as Dashboard

    Tweet->>Ear: Crisis tweet detected
    Ear->>SLIM: crisis_detected event
    
    par Parallel Analysis
        SLIM->>Fact: crisis_detected
        SLIM->>Sent: crisis_detected
    end
    
    Fact->>SLIM: fact_check_complete
    Sent->>SLIM: sentiment_complete
    
    par Secondary Analysis
        SLIM->>Legal: fact_check_complete
        SLIM->>Risk: fact_check_complete + sentiment_complete
    end
    
    Legal->>SLIM: legal_review_complete
    Risk->>SLIM: risk_score_complete
    
    SLIM->>Press: All prerequisites met
    Press->>SLIM: response_ready
    
    UI->>Gateway: Poll for status
    Gateway->>UI: Response ready for approval
```

## Agent Communication Endpoints

| Agent | Port | A2A Endpoint | Purpose |
|-------|------|--------------|---------|  
| Ear-to-Ground | 9001 | `http://ear-to-ground:9001/` | Crisis detection and coordination |
| Sentiment Analyst | 9002 | `http://sentiment-analyst:9002/` | Public opinion analysis |
| Risk Score | 9003 | `http://risk-score:9003/` | Crisis severity assessment |
| Fact Checker | 9004 | `http://fact-checker:9004/` | Claim verification |
| Legal Counsel | 9005 | `http://legal-counsel:9005/` | Legal risk evaluation |
| Press Secretary | 9006 | `http://press-secretary:9006/` | Response generation |
| Gateway | 8000 | `http://gateway:8000/api/` | REST API for frontend |

## Technology Stack

### Communication Layer
- **JSON-RPC A2A**: Direct agent-to-agent communication
- **A2AStarletteApplication**: HTTP server for each agent
- **AGNTCY App SDK**: Agent framework and request handling
- **REST API**: Gateway-to-frontend communication

### AI Agent Layer  
- **LangGraph**: Agent workflow orchestration
- **LangChain**: LLM integration framework
- **OpenAI GPT**: Language model for analysis and generation
- **Python**: Agent implementation language

### Frontend Layer
- **React + TypeScript**: Interactive crisis dashboard
- **Tailwind CSS**: Terminal-style UI design
- **Vite**: Development and build tooling

### Infrastructure
- **Docker Compose**: Multi-service orchestration
- **FastAPI**: Gateway REST API
- **Uvicorn**: ASGI server for Python services 