# Orbit – Implementation Task Breakdown

> This checklist is optimised for AI-assisted execution (e.g. GitHub Copilot or another LLM).  Each task is self-contained, lists prerequisites, includes acceptance criteria, and links back to the PRD sections.

---

## Legend
- **ID** – unique reference used in commits/PR titles (e.g. `M1-02`).
- **Status** – `todo` · `wip` · `review` · `done`.
- **Est.** – estimated effort in ideal hours.

---

| ID | Task | Depends on | Est. | Status | PRD Ref |
|----|------|-----------|------|--------|---------|
| M0-01 | Initialise AGNTCY structure (`agents/`, `gateway/`, `common/`, `config/`) | – | 0.5h | done | 9-M0 |
| M0-02 | Add `.env.example` with `OPENAI_API_KEY`, `ORBIT_TWEET_FILE` | M0-01 | 0.1h | done | 6 |
| M0-03 | Copy existing React UI into `gateway/frontend/` | M0-01 | 0.1h | done | 8 |
| M0-04 | Create root `README.md` with quick-start commands | M0-01 | 0.2h | done | 6 |
| M1-01 | Draft `docker-compose.yml` scaffolding all six services | M0-01 | 1h | done | 4,5 |
| M1-02 | Provide minimal `pyproject.toml` inc. AGNTCY SDK | M1-01 | 0.2h | done | – |
| M2-01 | Implement agents/ear_to_ground/ with SLIM crisis event publishing | M1-01 | 0.5h | done | 5-FR1 |
| M2-02 | Implement agents/sentiment_analyst/ with crisis event subscription | M2-01 | 0.5h | wip | 5-FR2 |
| M3-01 | Implement agents/fact_checker/ with crisis event subscription | M2-01 | 0.8h | todo | 5-FR3 |
| M3-02 | Implement agents/risk_score/ with dual event dependency (fact+sentiment) | M2-02,M3-01 | 0.5h | todo | 5-FR4 |
| M4-01 | Add `crisis_playbook.md`, `legal_rubric.md` data files | M0-02 | 0.1h | done | 7 |
| M4-02 | Implement agents/legal_counsel/ with fact event subscription | M3-01 | 0.8h | todo | 5-FR5 |
| M5-01 | Implement agents/press_secretary/ with dual event dependency (risk+legal) | M3-02,M4-02 | 0.5h | todo | 5-FR6 |
| M5-02 | gateway/main.py SLIM status aggregation & `/status`, `/publish` endpoints | M2-01 | 0.5h | todo | 5-FR7-9 |
| M6-01 | Front-end polling hook `useOrbitStatus` | M5-02 | 0.3h | todo | 8 |
| M6-02 | Add risk alert visuals & success modal | M6-01 | 0.3h | todo | 5-FR8,7-item 7 |
| M6-03 | Add reset button (reseed tweet stream) | M5-02 | 0.2h | todo | 7-item 7 |
| M6-04 | Footer with AGNTCY logo & link | M6-01 | 0.1h | todo | 7-item 8 |
| M6-05 | Polish: confetti / animation on publish | M6-02 | 0.2h | todo | 7-item 7 |
| QA-01 | Scripted demo run (`scripts/demo.sh`) validates <120s | all core | 0.3h | todo | – |

Total planned effort ≈ **12.0 h** (under four dev-days).
