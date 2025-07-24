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

### Core Application Structure
- **App.tsx** - Main application component managing crisis simulation state and timing
- **main.tsx** - React application entry point
- **mockData.ts** - Contains all simulation data including agents, crisis events, and timeline

### Component Architecture
The application uses a dashboard layout with specialized panels:

- **AgentPanel** - Displays AI agent status and current actions
- **CrisisAlert** - Shows viral content that triggered the crisis
- **SentimentDisplay** - Visualizes public sentiment analysis
- **PolicyPanel** - Displays company crisis response protocols
- **StatementDraft** - Shows AI-generated response for approval
- **Timeline** - Tracks crisis response progress

### State Management
The application uses React useState for local state management with automatic progression through crisis simulation steps. Key state includes:
- Agent statuses and actions
- Current simulation step
- Mission timer
- Publication status

### Simulation Flow
The crisis simulation auto-progresses through 5 steps:
1. Crisis detection (3s delay)
2. Sentiment analysis (step + 4s)
3. Policy retrieval (step + 4s) 
4. Statement drafting (step + 4s)
5. User approval required

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

## Demo Context

This is a hackathon/demo project specifically designed to showcase AGNTCY's multi-agent system capabilities. The application:
- Uses simulated data only (no live APIs or social feeds)
- Follows a predetermined narrative about a fictional crisis
- Demonstrates agent discovery, trust verification, and secure communication concepts
- Targets PR/Communications professionals as the primary persona

The current demo scenario involves a viral social media post about alleged executive misconduct, with agents working together to analyze sentiment, retrieve policies, and draft an appropriate response statement.