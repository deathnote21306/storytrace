# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**StoryTrace — "Git for News"**: A multi-agent system that takes a news article URL or topic, finds the original wire story, crawls 15 outlets, scores how much each outlet's coverage drifted from the original, and visualizes the mutation chain as a D3.js tree. See `STORYTRACE_FULL_CONTEXT.md` for the complete spec.

---

## Development Commands

### Backend (Python 3.14.3)
```bash
# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run FastAPI dev server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Test GDELT API (no key needed)
curl "https://api.gdeltproject.org/api/v2/doc/doc?query=Iran&mode=artlist&format=json"
```

### Frontend (Next.js 14)
```bash
cd frontend
npm install
npm run dev       # http://localhost:3000
npm run build
npm run lint
```

### Docker (full stack)
```bash
docker-compose up -d        # start all services
docker-compose logs -f api  # stream backend logs
docker-compose down
```

### Database
```bash
# Run migrations (PostgreSQL must be up)
psql $DATABASE_URL -f backend/db/migrations.sql
```

---

## Architecture

### Agent Pipeline (sequential, via LangGraph `StateGraph`)

```
FastAPI POST /analyze
  └── LangGraph orchestrator (backend/orchestrator.py)
        ├── seed_agent      — GDELT → finds root story, extracts entities (spaCy); short-circuits to END on error
        ├── crawler_agent   — feedparser, 15 RSS feeds, entity-matched headlines
        ├── translator      — Gemini 2.0 Flash, mutates articles in-place; fires only for non-English text
        ├── dna_extractor   — Featherless API (Qwen2.5-7B primary), parallel ThreadPoolExecutor; also extracts root DNA
        ├── drift_scorer    — pure Python math, zero tokens
        ├── geo_builder     — writes country back into scored_list; builds D3-ready nested tree JSON
        └── alert_agent     — fires webhook when drift_score >= 70
```

`forecast_agent.py` is separate — called on demand via `POST /forecast/{job_id}`, not part of the main pipeline.

Results stored in PostgreSQL (`stories` + `outlet_versions` tables). Redis caches repeat queries.

### Shared LangGraph State

Every agent receives and returns the same `state: dict`. The exact key names are a hard contract — a typo silently breaks downstream agents:

| Key | Written by | Read by |
|-----|-----------|---------|
| `state['job_id']` | FastAPI | alert_agent |
| `state['input']` | FastAPI | seed_agent |
| `state['entities']` | seed_agent | crawler_agent |
| `state['root']` | seed_agent | dna_extractor, drift_scorer, geo_builder |
| `state['articles']` | crawler_agent | translator (mutates in-place), dna_extractor |
| `state['dna_list']` | dna_extractor | drift_scorer |
| `state['scored_list']` | drift_scorer | geo_builder, alert_agent, update_story |
| `state['tree']` | geo_builder | FastAPI response |
| `state['alerts_fired']` | alert_agent | logging only |
| `state['error']` | seed_agent | FastAPI (check before saving) |

### Article dict shape (flows through `articles`, `dna_list`, `scored_list`)
```python
{
    'outlet':        str,   # e.g. "BBC"
    'country':       str,   # set by geo_builder before update_story
    'url':           str,
    'headline':      str,
    'text':          str,   # first 300 words; translator mutates in-place
    'language':      str,   # 'en' default; updated by translator
    'dna':           dict,  # added by dna_extractor
    'drift_score':   int,   # added by drift_scorer
    'parent_outlet': str,   # added by drift_scorer
}
```

### API Endpoints

- `POST /analyze` — accepts `{ url?, topic? }`, returns `{ job_id, status, poll_url }` (202)
- `GET /story/{job_id}` — poll for results; returns full tree JSON when `status == "complete"`
- `GET /story/recent` — returns list of recent story jobs from DB
- `POST /forecast/{job_id}` — on-demand Gemini 2.5 Pro geopolitical impact forecast
- `GET /health`

Full JSON shapes in `STORYTRACE_FULL_CONTEXT.md` section 8.

### Frontend

Uses Next.js App Router (not Pages Router). Key files:

- `app/page.tsx` — home page: URL/topic input + VoiceInput
- `app/story/[id]/page.tsx` — drift tree + diff panel, polls `GET /story/{id}`
- `app/explore/page.tsx` — explore page: lists recent stories via `GET /story/recent`
- `app/layout.tsx` — root layout with StoryTrace branding
- `components/DriftTree.jsx` — D3.js v7 tree; nodes colored green→amber→red by drift score; country branch grouping
- `components/DiffPanel.jsx` — facts added/dropped on node click
- `components/DriftLegend.tsx` — color legend for drift scores
- `components/VoiceInput.tsx` — Speechmatics WebSocket real-time transcription
- `components/ErrorBoundary.tsx` — React error boundary for graceful degradation

---

## Environment Variables

Copy `.env.example` to `.env`. Required keys:

| Variable | Used by |
|---|---|
| `DATABASE_URL` | psycopg2 everywhere |
| `REDIS_URL` | cache layer |
| `NEWSAPI_KEY` | seed_agent fallback |
| `FEATHERLESS_API_KEY` | dna_extractor (Mistral-7B via OpenAI-compatible API) |
| `GEMINI_API_KEY` | translator + optional forecast |
| `WEBHOOK_URL` | alert_agent |
| `NEXT_PUBLIC_API_URL` | frontend → backend |
| `SPEECHMATICS_KEY` | server-side only — Next.js API route exchanges it for a short-lived JWT; never `NEXT_PUBLIC_` |

---

## Package Version Notes

`requirements.txt` has been updated to versions current as of May 2026. All breaking changes from the original spec are already applied in the codebase:

1. **`google-generativeai` is deprecated — `google-genai` is used throughout.**
   All agents use the new SDK pattern (already implemented):
   ```python
   from google import genai
   client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY', ''))
   r = client.models.generate_content(model='gemini-2.0-flash', contents=...)
   ```

2. **`openai` 2.x is in use.** The Featherless DNA Extractor uses `openai.OpenAI(base_url='https://api.featherless.ai/v1', api_key=...)` — this custom base URL pattern is unchanged in 2.x and works as-is.

3. **`langgraph` 1.x** — `StateGraph` / `add_node` / `add_edge` / `compile()` pattern is in use in `backend/orchestrator.py`.

4. **spaCy + Python 3.14.3**: spaCy 3.8.13 works correctly. If `en_core_web_sm` is missing: `python -m spacy download en_core_web_sm`.

5. **DNA Extractor model**: The primary Featherless model is `Qwen/Qwen2.5-7B-Instruct` (not Mistral-7B as in the original spec). Fallback chain: `Qwen/Qwen2.5-3B-Instruct` → `microsoft/Phi-3-mini-4k-instruct`.

---

## Token Efficiency Rules

- spaCy NER runs locally — filters articles before any LLM call (zero tokens)
- RSS headline matching is local — zero tokens
- Only first 300 words per article sent to any LLM
- Featherless extracts structured JSON only (not open-ended summarization)
- Translator fires only when `langdetect` identifies non-English content
- Target: ~4,000–6,000 tokens per full pipeline run

---

## Branch Convention

```
main  ← protected, submission-only
  └── dev  ← all PRs target this
        ├── feature/backend-infra    (D1)
        ├── feature/core-agents      (D2)
        ├── feature/ai-agents        (D3)
        └── feature/frontend         (D4)
```

Commit prefix format: `[D1]`, `[D2]`, `[D3]`, `[D4]` matching which team wrote it.

---

## PR Plan

Full details for every PR are in [plan.md](plan.md). Summary:

| PR | Team | Branch | What | Depends on | Status |
|----|------|--------|------|------------|--------|
| **01** | D1 | `PR01-init-structure` | Scaffold — folders, .gitignore, .env.example, requirements.txt | — | ✅ done |
| **02** | D1 | `feature/database` | DB schema (migrations.sql) + connection.py | PR-01 | ✅ done |
| **03** | D1 | `feature/fastapi-skeleton` | **FastAPI skeleton — H4 API Contract Lock** | PR-02 | ✅ done |
| **04** | D1 | `feature/orchestrator` | LangGraph orchestrator + agent stubs | PR-03 | ✅ done |
| **05** | D1 | `feature/docker` | Docker Compose + Dockerfiles | PR-01 | ✅ done |
| **06** | D2 | `feature/agent-seed` | Agent 1 — Story Seed (GDELT + NewsAPI) | PR-04 | ✅ done |
| **07** | D2 | `feature/agent-crawler` | Agent 2 — Crawler (15 RSS feeds) | PR-06 | ✅ done |
| **08** | D2 | `feature/agent-alert` | Agent 7 — Alert Agent (webhook) | PR-04 | ✅ done |
| **09** | D3 | `feature/agent-dna` | DNA Extractor (Featherless/Qwen) | PR-04 | ✅ done |
| **10** | D3 | `feature/agent-translator` | Translator (Gemini Flash) | PR-04 | ✅ done |
| **11** | D3 | `feature/agent-drift-scorer` | Drift Scorer (pure Python) | PR-09 | ✅ done |
| **12** | D3 | `feature/agent-geo-builder` | Geo-Branch Builder | PR-11 | ✅ done |
| **13** | All | `feature/e2e-pipeline` | **E2E integration test — H10 Pipeline Check** | PR-04–12 | ✅ done |
| **14** | D4 | `feature/frontend-setup` | Next.js App Router setup + routing | PR-01 | ✅ done |
| **15** | D4 | `feature/drift-tree` | DriftTree D3 + DiffPanel components | PR-14 | ✅ done |
| **16** | D4 | `feature/diff-panel` | DiffPanel component | PR-15 | ✅ done |
| **17** | D4 | `feature/api-integration` | **API integration — H16 Frontend Lock** | PR-15, PR-03 | ✅ done |
| **18** | D4 | `feature/voice-input` | VoiceInput (Speechmatics WebSocket) | PR-17 | ✅ done |
| **19** | D4 | `feature/ui-polish` | UI polish, skeleton loader, ErrorBoundary, Explore page, mobile | PR-17, PR-18 | ✅ done |
| **20** | D3 | `feature/agent-forecast` | Forecast Agent — Gemini 2.5 Pro (optional) | PR-13 | ✅ done |
| **21** | D1 | `feature/deployment` | Vultr deployment + Nginx | PR-13 | — |
| **22** | All | `feature/submission` | README + tag v1.0.0 + submit | All | — |

### Critical gates
- **H4** — PR-03 merged → API contract locked; D2 and D3 unblock
- **H10** — PR-13 passes → pipeline end-to-end confirmed
- **H16** — PR-17 merged → frontend wired to live API
- **H23** — code freeze, tag `v1.0.0`, submit

### Implementation notes (current state)

- **orchestrator**: `translator` runs before `dna_extractor` — translator mutates `state['articles']` in-place so DNA sees translated text. Do NOT change this order.
- **dna_extractor**: extracts DNA for the root story too (`state['root']['dna']`) so drift_scorer has facts to compare against. Root DNA is only extracted if `root['dna']['facts_kept']` is empty.
- **dna_extractor**: uses `ThreadPoolExecutor(max_workers=6)` for parallel article extraction — model fallback chain: `Qwen2.5-7B-Instruct` → `Qwen2.5-3B-Instruct` → `Phi-3-mini-4k-instruct`. Each call has a 15 s timeout.
- **drift_scorer**: `find_parent_outlet` assigns the lowest-drift outlet seen so far as parent (not a true provenance tree). `fact_score` is 60 pts max; `tone_score` is 40 pts max.
- **geo_builder**: maps known outlets to countries via `OUTLET_COUNTRY` dict; unknown outlets get `'Other'`. Writes `art['country']` back into `scored_list` dicts before building the tree.
- **main.py**: `GET /story/recent` uses `get_recent()` from `backend/db/connection.py`. CORS allows `localhost:3000` and `localhost:3001`.
- **forecast_agent**: uses `gemini-2.5-pro` (not flash). Called on demand from `POST /forecast/{job_id}`, not part of the main pipeline.
- **PR-18 / VoiceInput**: `SPEECHMATICS_KEY` has no `NEXT_PUBLIC_` prefix; the Next.js API route at `/api/speechmatics-token` exchanges it for a short-lived JWT the browser uses.
