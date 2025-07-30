# Orbit - AI-Powered Crisis Command Center

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://hub.docker.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB)](https://reactjs.org/)

An AI-powered PR crisis management demonstration built with AGNTCY's multi-agent system, showcasing real-time collaboration between six AI agents to monitor, analyze, and respond to communications crises.

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/Laci21/orbit.git
cd orbit

# 2. Configure environment
cp .env.example .env
# Edit .env with your OpenAI API key (or Azure OpenAI credentials)

# 3. Start all services
docker compose up

# 4. Access the dashboard
open http://localhost:8000
```

### UI Development Setup

For frontend development with hot reloading:

```bash
# Navigate to frontend directory
cd gateway/frontend

# Install dependencies
npm install

# Start development server (runs on http://localhost:5173)
npm run dev

# In another terminal, start the backend services
docker compose up
```

The React frontend will proxy API calls to the backend services running in Docker.

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

## 🔌 Inter-Agent Communication via SLIM

Orbit’s six AI agents now talk to each other exclusively over **SLIM** (Secure Low-latency Interactive Messaging).

* A single SLIM broker runs inside Docker (`slim` service, port **46357**)
* Each agent connects to that broker at start-up (`SLIM gRPC bridge connected`)
* Communication uses **request-reply** pattern
* SLIM transport & clients are provided by **[AGNTCY App-SDK](https://github.com/agntcy/app-sdk)**, so no custom transport code was needed
* Implementation follows the proven pattern from the **[coffeeAgntcy *lungo* example](https://github.com/agntcy/coffeeAgntcy/tree/main/coffeeAGNTCY/coffee_agents/lungo)**
* Payloads remain JSON-RPC 2.0, simply wrapped in gRPC frames
* The legacy HTTP ports (9001-9006) now exist *only* so App-SDK can fetch `/.well-known/agent.json`; no business logic travels over HTTP anymore.

For the full migration steps see [`docs/slim-migration.md`](docs/slim-migration.md).

---

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

Copy `.env.example` to `.env` and configure:

**Azure OpenAI:**
```bash
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

**Additional Configuration:**
```bash
ORBIT_TWEET_FILE=data/tweets_astronomer.json
CRISIS_THRESHOLD=70
GATEWAY_PORT=8000
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

## 📖 Documentation

- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute to the project
- [Security Policy](SECURITY.md) - Security practices and vulnerability reporting
- [Technical Implementation](docs/TECHNICAL_IMPLEMENTATION.md) - Detailed technical architecture
- [Agent Specifications](docs/AGENT_SPECIFICATIONS.md) - Individual agent behaviors

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 🔒 Security

If you discover a security vulnerability, please see our [Security Policy](SECURITY.md) for how to report it responsibly.

---

**Powered by AGNTCY** - Demonstrating the future of AI-native enterprise applications.
