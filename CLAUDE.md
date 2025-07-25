# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Orbit is an AI-powered PR crisis command center demo application built with React, TypeScript, and Vite. It simulates a real-time crisis management scenario showcasing how multiple AI agents collaborate to monitor, analyze, and respond to communications crises. The application demonstrates AGNTCY's Multi-Agent System (MAS) capabilities through an interactive dashboard.

## Common Development Commands

### Development
- `npm run dev` - Start development server with Vite
- `npm run build` - Build production bundle
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint on codebase

### Testing
No test framework is currently configured in this project.

## Architecture & Key Components

### Multi-Agent System Architecture
The Orbit system uses a **direct agent communication architecture** with 6 AI agents communicating via JSON-RPC A2A calls:

#### Agent Communication Flow
```
Tweet with claim arrives
         ↓
    Ear-to-Ground Agent
         ↓ (JSON-RPC calls)
    ┌─────────────┐
    ↓             ↓
Fact Checker  Sentiment Analyst
    ↓ (A2A call)  ↓ (A2A call)
    ↓         Risk Score ←─┘
    ↓ (A2A call)
Legal Counsel
    ↓ (A2A call)
Press Secretary
```

#### The 6 AI Agents
1. **Ear-to-Ground Agent** (port 9001) - Monitors social media, detects crisis tweets, calls dependent agents
2. **Sentiment Analyst** (port 9002) - Analyzes public sentiment from crisis tweets
3. **Fact Checker** (port 9004) - Verifies claims in crisis content, provides factual analysis
4. **Risk Score Agent** (port 9003) - Calculates crisis severity/impact based on fact check + sentiment analysis
5. **Legal Counsel Agent** (port 9005) - Reviews legal implications based on fact checker output
6. **Press Secretary Agent** (port 9006) - Drafts official response statements using all agent outputs

#### Direct A2A Dependencies
- **Ear-to-Ground** → Fact Checker + Sentiment Analyst (parallel JSON-RPC calls)
- **Fact Checker** → Legal Counsel + Risk Score (direct JSON-RPC calls)
- **Sentiment Analyst** → Risk Score (direct JSON-RPC call)
- **Risk Score + Legal Counsel** → Press Secretary (direct JSON-RPC calls)

#### JSON-RPC A2A Communication
- **HTTP Servers** - Each agent runs A2AStarletteApplication on dedicated ports
- **Direct calls** - Agents call each other directly via HTTP JSON-RPC
- **Synchronous flow** - Agents wait for responses before proceeding
- **Message format** - Standard JSON-RPC 2.0 with agent-specific payloads

### Frontend Architecture
The React dashboard provides real-time visualization of agent coordination:

#### Core Components
- **AgentPanel** - Displays AI agent status and current actions
- **CrisisAlert** - Shows viral content that triggered the crisis
- **SentimentDisplay** - Visualizes public sentiment analysis
- **PolicyPanel** - Displays company crisis response protocols
- **StatementDraft** - Shows AI-generated response for approval
- **Timeline** - Tracks crisis response progress

#### State Management
- Agent status updates via REST API polling of gateway
- Gateway queries agents directly via JSON-RPC A2A calls
- Mission timer and crisis progression tracking

## Styling & UI

### Technology Stack
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Icon library
- **Design Theme** - Terminal/command center aesthetic with cyan/green accents on black background

### Visual Design
The interface mimics a mission control center with:
- Monospace font for technical feel
- Real-time status indicators
- Color-coded agent states (idle/active/complete)
- Animated elements for live data simulation

## Data Structure

### Agent Interface
```typescript
interface Agent {
  id: string;
  name: string;
  status: 'idle' | 'active' | 'complete';
  avatar: string;
  description: string;
  currentAction?: string;
}
```

### Crisis Event Interface
```typescript
interface CrisisEvent {
  id: string;
  timestamp: string;
  type: 'detection' | 'sentiment' | 'fact-check' | 'draft' | 'published';
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}
```

## Configuration Files

### Build & Development
- **vite.config.ts** - Vite configuration with React plugin and lucide-react optimization
- **tsconfig.json** - TypeScript project references configuration
- **tsconfig.app.json** - Main TypeScript configuration for application code
- **tsconfig.node.json** - TypeScript configuration for Node.js scripts

### Code Quality
- **eslint.config.js** - ESLint configuration with TypeScript, React hooks, and React refresh rules
- **tailwind.config.js** - Tailwind CSS configuration scanning src files and index.html
- **postcss.config.js** - PostCSS configuration for Tailwind processing

## Demo Context & Crisis Scenario

This is a hackathon/demo project specifically designed to showcase AGNTCY's multi-agent system capabilities. The application:
- Uses simulated data only (no live APIs or social feeds)
- Demonstrates real-time event-driven agent coordination
- Shows dependency management and parallel processing in multi-agent systems
- Targets PR/Communications professionals as the primary persona

### Crisis Scenario: Executive Misconduct Allegation

**Initial Crisis:** A viral social media post surfaces alleging executive misconduct at a major company.

**Agent Response Workflow:**

1. **Crisis Detection (Immediate)**
   - Ear-to-Ground agent detects viral post with serious allegations
   - Broadcasts `crisis_detected` event to trigger coordinated response

2. **Parallel Analysis Phase (0-30 seconds)**
   - **Fact Checker**: Verifies claims, checks sources, assesses credibility
   - **Sentiment Analyst**: Analyzes public reaction, tracks sentiment trends

3. **Risk Assessment Phase (30-45 seconds)**
   - **Risk Score Agent**: Calculates crisis severity using fact check + sentiment data
   - **Legal Counsel Agent**: Reviews legal implications based on fact checker findings

4. **Response Generation Phase (45-60 seconds)**
   - **Press Secretary Agent**: Drafts official response using all agent outputs
   - Considers: facts, sentiment, risk level, legal constraints

5. **Human Approval (Manual)**
   - Crisis management team reviews AI-generated response
   - Approves, modifies, or requests revision before publication

**Ongoing Monitoring:**
- Sentiment Analyst continues processing new tweets for real-time sentiment updates
- System adapts response strategy based on evolving public reaction

**Key Demo Value:**
- Shows autonomous agent coordination without human micromanagement
- Demonstrates dependency resolution (agents wait for prerequisites)
- Illustrates parallel processing for faster crisis response
- Provides transparency into AI decision-making process