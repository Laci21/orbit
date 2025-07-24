# Orbit – Full-Stack AGNTCY-Powered PRD

---

## 1  Vision & Objectives
Build a live demonstration of PR-crisis management driven by **six collaborating AI agents** running on AGNTCY infrastructure and surfaced in a single-page React dashboard.

Success = the audience can watch agents discover, analyse, debate and publish a press statement in ≤ 2 minutes, while seeing:

1. Real (prefetched) tweets from the Astronomer CEO scandal.
2. Sentiment + risk spikes in real time.
3. Legal guard-rails and policy facts influence the final copy.
4. Clear trace of inter-agent messages (the “wow” moment).

---

## 2  Core User Stories (Comms Lead)
1. View live feed of crisis posts with risk score & sentiment trend.
2. Receive alert when risk > threshold.
3. Inspect supporting facts & legal constraints.
4. One-click approve AI-drafted statement.
5. See dashboard return to monitoring state.

---

## 3  Agent Catalogue (MVP)

| # | Agent | Purpose | SLIM Topic Subscriptions | SLIM Topic Publications |
|---|-------|---------|------------------------|------------------------|
| 1 | Ear-to-the-Ground | Stream tweets from prefetched JSON, detect crises | None (initiates workflow) | `orbit.crisis.detected` |
| 2 | Sentiment Analyst | Score sentiment of crisis content + ongoing analysis | `orbit.crisis.detected` | `orbit.sentiment.complete` |
| 3 | Fact Checker | Verify claims in crisis content against knowledge base | `orbit.crisis.detected` | `orbit.fact.complete` |
| 4 | Risk Score Agent | Calculate crisis severity from fact + sentiment data | `orbit.fact.complete`, `orbit.sentiment.complete` | `orbit.risk.complete` |
| 5 | Legal Counsel | Assess legal implications and response constraints | `orbit.fact.complete` | `orbit.legal.complete` |
| 6 | Press Secretary | Draft official response using all agent outputs | `orbit.risk.complete`, `orbit.legal.complete` | `orbit.response.ready` |

**Event-Driven Dependencies:**
- Crisis detected → Fact Checker + Sentiment Analyst (parallel)
- Fact check complete → Legal Counsel + Risk Score (partial dependency)
- Sentiment analysis complete → Risk Score (completes dependency)
- Risk score complete + Legal review complete → Press Secretary

All agents use **AGNTCY App SDK** with **SLIM transport** for event-driven communication.

---

## 4  System Architecture
```
[Browser UI] (gateway/frontend/)
    ⇅ HTTP (poll 3 s)
[FastAPI Gateway] (gateway/main.py)  <--HTTP-->  [Agent Status]
                    ⇅
[SLIM Broker] (ghcr.io/agntcy/slim:0.3.15)
    ├─ Topic: orbit.crisis.detected
    ├─ Topic: orbit.sentiment.complete
    ├─ Topic: orbit.fact.complete
    ├─ Topic: orbit.risk.complete
    ├─ Topic: orbit.legal.complete
    └─ Topic: orbit.response.ready
                    ⇅ SLIM Transport
[Individual Agents] (dual bridge pattern)
    ├─ agents/ear_to_ground/ (Transport + Broadcast)
    ├─ agents/sentiment_analyst/ (Transport + Broadcast)
    ├─ agents/risk_score/ (Transport + Broadcast)
    ├─ agents/fact_checker/ (Transport + Broadcast)
    ├─ agents/legal_counsel/ (Transport + Broadcast)
    └─ agents/press_secretary/ (Transport + Broadcast)
```

**Event-Driven Communication Flow:**
1. **Ear-to-Ground** detects crisis → publishes `orbit.crisis.detected`
2. **Sentiment Analyst** + **Fact Checker** subscribe to crisis events → process in parallel
3. **Risk Score Agent** waits for BOTH fact + sentiment completion events
4. **Legal Counsel** processes independently after fact check complete
5. **Press Secretary** waits for BOTH risk + legal completion events
6. **Gateway** polls agent status and serves UI updates

Docker-Compose services:
1. `slim` – SLIM broker (central message hub)
2. Individual agent services (6 agents with SLIM transport)
3. `gateway` – FastAPI REST facade + React UI

---

## 5  Functional Requirements
FR-1  Ear-to-Ground streams crisis events via SLIM `orbit.crisis.detected` topic.  
FR-2  Sentiment Analyst subscribes to crisis events, publishes sentiment analysis via `orbit.sentiment.complete`.  
FR-3  Fact Checker subscribes to crisis events, publishes verification results via `orbit.fact.complete`.  
FR-4  Risk Score Agent waits for BOTH sentiment + fact events, publishes crisis score via `orbit.risk.complete`.  
FR-5  Legal Counsel subscribes to fact events, publishes legal guidance via `orbit.legal.complete`.  
FR-6  Press Secretary waits for BOTH risk + legal events, publishes draft via `orbit.response.ready`.  
FR-7  All agents use SLIMMessage format with serialize() method for proper transport compatibility.  
FR-8  Gateway aggregates agent status from SLIM subscriptions at `/status` endpoint.  
FR-9  UI polls `/status` every 3 s; updates dashboard widgets showing agent coordination.  
FR-10 On "Approve", UI POSTs `/publish`; system resets for next crisis 10s after publish.

---

## 6  Non-Functional Requirements
• Local-only stack (offline once images pulled).  
• Setup ≤ 5 commands (`git clone` → `cp .env.example .env` → `docker compose up`).  
• OpenAI key via `.env`.
• Demo run < 2 min on 16 GB laptop.  
• Agent message log saved to `/tmp/orbit_run.log`.

---

## 7  Data Assets
1. `tweets_astronomer.json` – `id, text, author, ts, retweets, likes`.  
2. `crisis_playbook.md` – Fact Checker knowledge base.  
3. `legal_rubric.md` – bullet list for Legal Counsel.  
4. Agent prompt files in `agents/*/prompts/`.

---

## 8  Front-end Changes
1. `api.ts` with `getStatus()` & `publish()` (fetch).  
2. Polling hook `useOrbitStatus`.  
3. Extend `CrisisAlert` for risk & legal data.  
4. Animate agent icons on new messages.  
5. Minor Tailwind tweaks; no routing changes.

---

## 9  Milestones & Estimates
| ID | Task | Owner | ETC |
|----|------|-------|------|
| M0 | Repo prep | — | 0.5 d |
| M1 | Core infra (compose) | — | 1 d |
| M2 | Ear + Sentiment | — | 0.5 d |
| M3 | Risk Score | — | 0.5 d |
| M4 | Fact Checker & Legal Counsel | — | 1 d |
| M5 | Press Secretary & Publish | — | 0.5 d |
| M6 | Polish & Demo script | — | 0.5 d |
**Total ≈ 4 developer-days**
