# Orbit – Event-Driven Crisis Management Architecture

## System Overview

The Orbit system uses an **event-driven, dependency-based architecture** where AI agents coordinate through SLIM transport messaging to handle PR crises autonomously.

## High-Level Architecture

```mermaid
graph TD
  subgraph "Frontend Layer"
    BrowserUI["React Dashboard\n(Crisis Command Center)"]
  end

  subgraph "Gateway Layer"
    Gateway["FastAPI Gateway\n(Orchestration & Status)"]
  end

  subgraph "Message Broker"
    SLIM["SLIM Broker\n(Event Streaming Hub)"]
  end

  subgraph "AI Agent Layer"
    Ear["Ear-to-Ground\n(Crisis Detection)"]
    Sent["Sentiment Analyst\n(Public Opinion)"]
    Risk["Risk Score\n(Impact Assessment)"]
    Fact["Fact Checker\n(Claim Verification)"]
    Legal["Legal Counsel\n(Compliance Review)"]
    Press["Press Secretary\n(Response Generation)"]
  end

  subgraph "Data Layer"
    TweetData["Crisis Tweet Data"]
    Playbook["Crisis Playbook"]
    LegalRubric["Legal Guidelines"]
  end

  BrowserUI <--> |"REST API\n(Status/Control)"| Gateway
  Gateway <--> |"Agent Queries"| SLIM
  
  Ear --> |"crisis_detected"| SLIM
  SLIM --> |"crisis_detected"| Fact
  SLIM --> |"crisis_detected"| Sent
  
  Fact --> |"fact_check_complete"| SLIM
  Sent --> |"sentiment_complete"| SLIM
  
  SLIM --> |"fact_check_complete"| Legal
  SLIM --> |"fact_check_complete\n+ sentiment_complete"| Risk
  
  Risk --> |"risk_score_complete"| SLIM
  Legal --> |"legal_review_complete"| SLIM
  
  SLIM --> |"risk_score_complete\n+ legal_review_complete"| Press
  
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

## Agent Communication Topics

| Topic | Publisher | Subscribers | Purpose |
|-------|-----------|-------------|---------|
| `orbit.crisis.detected` | Ear-to-Ground | Fact Checker, Sentiment Analyst | Initial crisis trigger |
| `orbit.fact.complete` | Fact Checker | Legal Counsel, Risk Score | Claim verification results |
| `orbit.sentiment.complete` | Sentiment Analyst | Risk Score | Public opinion analysis |
| `orbit.risk.complete` | Risk Score | Press Secretary | Crisis severity assessment |
| `orbit.legal.complete` | Legal Counsel | Press Secretary | Legal risk evaluation |
| `orbit.response.ready` | Press Secretary | Gateway | Draft response available |

## Technology Stack

### Communication Layer
- **SLIM Broker**: Central event streaming hub (ghcr.io/agntcy/slim:0.3.15)
- **AGNTCY App SDK**: Agent framework and transport abstraction
- **Dual Bridge Pattern**: A2A (requests) + Broadcast (events)

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