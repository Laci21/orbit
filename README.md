# Orbit - AI-Powered Crisis Command Center

An AI-powered PR crisis management demonstration built with AGNTCY's multi-agent system, showcasing real-time collaboration between six AI agents to monitor, analyze, and respond to communications crises.

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <repository-url>
cd orbit

# 2. Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key

# 3. Start all services
docker compose up

# 4. Access the dashboard
open http://localhost:8000
```

## 🏗️ Architecture

```
orbit/
├── agents/              # 6 AI agents (individual services)
│   ├── ear_to_ground/   # Monitors tweet stream
│   ├── sentiment_analyst/ # Analyzes public sentiment  
│   ├── risk_score/      # Calculates crisis severity
│   ├── fact_checker/    # Validates claims against playbook
│   ├── legal_counsel/   # Provides legal constraints
│   └── press_secretary/ # Drafts response statements
├── gateway/             # FastAPI server + React UI
├── data/                # Tweet data & knowledge bases
└── docker-compose.yaml  # AGNTCY infrastructure
```

## 🤖 Agent Workflow

1. **Ear-to-Ground** streams crisis tweets from JSON data
2. **Sentiment Analyst** scores public mood and trending keywords  
3. **Risk Score** calculates overall crisis severity (0-100)
4. **Fact Checker** validates claims against company playbook
5. **Legal Counsel** provides compliance guidelines and constraints
6. **Press Secretary** drafts holding statements for approval

## 🎯 Demo Scenario

The system simulates a viral social media crisis involving Astronomer CEO allegations, demonstrating how AI agents collaborate to:
- Monitor social sentiment in real-time
- Fact-check claims against company policies
- Draft compliant response statements
- Enable one-click approval and publishing

**Target demo time:** < 2 minutes from crisis detection to published response

## 🛠️ Development

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- 16GB+ RAM recommended

### Environment Variables
```bash
OPENAI_API_KEY=your_key_here
ORBIT_TWEET_FILE=data/tweets_astronomer.json
SLIM_BROKER_URL=http://localhost:46357
CRISIS_THRESHOLD=70
```

### Services
- **SLIM Broker**: Agent communication (port 46357)
- **OASF Registry**: Agent identity (port 8080)  
- **Agent Directory**: Service discovery (port 8081)
- **6 Agent Services**: Individual AI agents (ports 9001-9006)
- **Gateway**: FastAPI + React UI (port 8000)

## 📊 Monitoring

Agent interactions are logged to `/tmp/orbit_run.log` during execution. The dashboard provides real-time visibility into:
- Agent status and current actions
- Inter-agent message flow
- Crisis progression timeline
- Sentiment analysis and risk scoring

## 🔗 Built With

- **[AGNTCY App SDK](https://github.com/agntcy/app-sdk)** - Multi-agent system framework
- **LangGraph** - Agent workflow orchestration  
- **FastAPI** - REST API gateway
- **React + TypeScript** - Dashboard interface
- **OpenAI GPT** - Natural language processing
- **Docker** - Containerized deployment

## 🧰 AI Tools Utilised During Development

| # | Tool | Purpose in This Project |
|---|------|-------------------------|
| 1 | [Manus](https://manus.im) | Ideation: Generated and refined the initial hackathon concept |
| 2 | [ChatPRD](https://www.chatprd.ai) | Drafted the very first Product Requirements Document |
| 3 | [Bolt](https://bolt.new) | Auto-generated the early mock UI used as Orbit’s starting point |
| 4 | [Cursor](https://cursor.sh) (o3 model) | Full-stack architecture planning |
| 5 | [Claude Code](https://www.anthropic.com) (Sonnet 4) | Implemented code and integrated AGNTCY backend |

---

**Powered by AGNTCY** - Demonstrating the future of AI-native enterprise applications.
