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

| # | Agent | Purpose | Key Inputs | Key Outputs |
|---|-------|---------|-----------|-------------|
| 1 | Ear-to-the-Ground | Stream tweets from prefetched JSON (mocks live X feed). | local JSON | `tweet` events |
| 2 | Sentiment Analyst | Score sentiment of each tweet + rolling window. | tweet text | `sentiment` events |
| 3 | Risk Score Agent | Map sentiment + virality to 1–100 risk. | sentiment, retweets | `risk_score` events |
| 4 | Fact Checker | Look up crisis playbook. | tweet assertions | `fact_check` notes |
| 5 | Legal Counsel | Provide “do-not-say / must-say” constraints. | tweet text, playbook | legal guidance |
| 6 | Press Secretary | Draft holding statement that satisfies facts + legal guidance. | tweet, facts, legal | `draft_statement` |

All inherit CoffeeAgntcy’s **LangChain-based `LLMAgent` skeleton**; prompts + adapters are customised.

---

## 4  System Architecture
```
[Browser UI] (gateway/frontend/)
    ⇅ HTTP (poll 3 s)
[FastAPI Gateway] (gateway/main.py)  <--ACP-->  [Individual Agents]
                                                   ├─ agents/ear_to_ground/
                                                   ├─ agents/sentiment_analyst/
                                                   ├─ agents/risk_score/
                                                   ├─ agents/fact_checker/
                                                   ├─ agents/legal_counsel/
                                                   └─ agents/press_secretary/
           ⇵ OASF Registry (local)
           ⇵ Agent Directory (local)
           ⇵ SLIM Broker (local)
```
Docker-Compose services:
1. `oasf` – OASF registry
2. `directory` – Agent Directory Service
3. `slim` – SLIM broker (gRPC pub/sub)
4. Individual agent services (6 agents)
5. `gateway` – FastAPI REST facade + React UI

---

## 5  Functional Requirements
FR-1  Prefetched tweet file streamed at ≥ 1 msg/s.  
FR-2  Sentiment Analyst posts per-tweet score and 30-sec rolling average.  
FR-3  Risk Score Agent emits overall crisis score; UI turns red when > 70.  
FR-4  Fact Checker returns “true / questionable / false” + citation lines.  
FR-5  Legal Counsel outputs `forbidden_phrases`, `required_phrases`.  
FR-6  Press Secretary builds ≤ 280 char statement satisfying all constraints.  
FR-7  Gateway aggregates latest outputs at `/status`.  
FR-8  UI polls `/status` every 3 s; updates dashboard widgets.  
FR-9  On “Approve”, UI POSTs `/publish`; Press Secretary pushes `published` event.  
FR-10 Dashboard resets 10 s after publish.

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
