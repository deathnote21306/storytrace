# StoryTrace — Implementation Plan
> **This is the source of truth for every task. Each section = one pull request. PRs target `dev`, never `main`.**
> Branch convention: `feature/<pr-slug>` → `dev` (squash merge)

---

## Team Legend

| Team | Role |
|------|------|
| **D1** | Backend + Infrastructure |
| **D2** | Core Agents (Seed, Crawler, Alert) |
| **D3** | AI Agents (DNA, Translator, Drift, Geo, Forecast) |
| **D4** | Frontend |

---

## Who Can Work When

| From hour... | D1 | D2 | D3 | D4 |
|---|---|---|---|---|
| **H0** | ✅ PR-01, PR-05 | ⏳ blocked on PR-04 | ⏳ blocked on PR-04 | ✅ PR-14 |
| **H4** (API Contract Lock) | ✅ PR-04 | ✅ PR-06 | ✅ PR-09 | ✅ PR-15 |
| **H10+** | Integration | PR-07, PR-08 | PR-10, PR-11, PR-12 | PR-16, PR-17 |

**D1 and D4 are unblocked from hour 0.**

**D2 and D3 are blocked until D1 merges PR-04 (orchestrator stubs)** — because the stubs define the `run(state: dict) -> dict` interface everyone writes to. While waiting (H0–H4), D2 and D3 should:

- Set up local Python env: `pip install -r requirements.txt` + `python -m spacy download en_core_web_sm`
- **D2:** Test GDELT API connection — `curl "https://api.gdeltproject.org/api/v2/doc/doc?query=Iran&mode=artlist&format=json"`
- **D3:** Write a throwaway 10-line script to confirm Featherless and Gemini API keys authenticate
- Draft agent code locally — the `run(state)` signature is already known from the spec. Just can't push until PR-04 lands.

---

## Shared LangGraph State Schema
> **This is the shared data contract between all teams. Every agent reads and writes the same `state` dict. Use exactly these key names — one typo silently breaks downstream agents.**

| Key | Type | Written by | Read by | Set in PR |
|-----|------|-----------|---------|-----------|
| `state['job_id']` | `str` | FastAPI (main.py) | alert_agent | PR-03 |
| `state['input']` | `str` | FastAPI (main.py) | seed_agent | PR-03 |
| `state['entities']` | `list[str]` | seed_agent | crawler_agent | PR-06 |
| `state['root']` | `dict` | seed_agent | dna_extractor, drift_scorer, geo_builder | PR-06 |
| `state['articles']` | `list[dict]` | crawler_agent | translator (mutates in-place), dna_extractor | PR-07 |
| `state['dna_list']` | `list[dict]` | dna_extractor | drift_scorer | PR-09 |
| `state['scored_list']` | `list[dict]` | drift_scorer | geo_builder, alert_agent, update_story | PR-11 |
| `state['tree']` | `dict` | geo_builder | FastAPI response builder | PR-12 |
| `state['alerts_fired']` | `list[str]` | alert_agent | (logging only) | PR-08 |
| `state['error']` | `str` | seed_agent (on failure) | FastAPI (check before saving) | PR-06 |

**Article dict shape** (used in `state['articles']` and `state['dna_list']` and `state['scored_list']`):
```python
{
    'outlet':       str,   # e.g. "BBC"
    'country':      str,   # set by geo_builder BEFORE update_story runs — see PR-12 note
    'url':          str,
    'headline':     str,
    'text':         str,   # first 300 words; translator mutates this in-place
    'language':     str,   # 'en' default; translator updates if non-English
    'dna':          dict,  # added by dna_extractor
    'drift_score':  int,   # added by drift_scorer
    'parent_outlet':str,   # added by drift_scorer
}
```

---

## Critical Sync Points

| Milestone | Hour | Who | Gate |
|-----------|------|-----|------|
| **API Contract Lock** | H4 | All | D1 has published exact JSON shapes. No one writes agent or frontend code until this is done. |
| **Pipeline End-to-End** | H10 | D1 + D2 + D3 | A real URL runs through all 7 agents and returns tree JSON. |
| **Frontend Integration** | H16 | D1 + D4 | D4 switches from mock data to live API. Full stack working. |
| **Demo Run #1** | H20 | All | Voice input → pipeline → tree → forecast. Fix top 3 issues. |
| **Code Freeze** | H23 | All | No more changes. Record video. Submit. Tag `v1.0.0`. |

---

## Structure at a Glance

| PR | Team | What |
|----|------|------|
| 01 | D1 | Scaffold + .gitignore + .env.example + requirements.txt |
| 02 | D1 | DB schema (migrations.sql) + connection.py |
| 03 | D1 | **FastAPI skeleton — H4 API Contract Lock** (all others wait for this) |
| 04 | D1 | LangGraph orchestrator + agent stubs |
| 05 | D1 | Docker Compose + Dockerfiles (parallel with 02/03) |
| 06 | D2 | Agent 1 — Story Seed (GDELT + NewsAPI) |
| 07 | D2 | Agent 2 — Crawler (15 RSS feeds) |
| 08 | D2 | Agent 7 — Alert Agent (webhook) |
| 09 | D3 | Agent 3 — DNA Extractor (Featherless) |
| 10 | D3 | Agent 4 — Translator (Gemini Flash) |
| 11 | D3 | Agent 5 — Drift Scorer (pure Python math) |
| 12 | D3 | Agent 6 — Geo-Branch Builder |
| 13 | All | **E2E integration test — H10 Pipeline Check** |
| 14 | D4 | Next.js setup + routing (starts at hour 0, no backend dep) |
| 15 | D4 | DriftTree D3 component (static mock data) |
| 16 | D4 | DiffPanel component |
| 17 | D4 | **API integration — H16 Frontend Lock** |
| 18 | D4 | VoiceInput (Speechmatics WebSocket) |
| 19 | D4 | UI polish + mobile responsive |
| 20 | D3 | Forecast Agent — Gemini Pro (optional, only if ahead) |
| 21 | D1 | Vultr deployment + Nginx |
| 22 | All | README + tag v1.0.0 + submit |

---

## PR-01 — Project Scaffold & Git Structure
**Team:** D1 | **Branch:** `feature/scaffold` | **Target hour:** 0–1

### What to build
- Root-level folder skeleton (no code yet, just the directories and stub files)
- `.gitignore`, `.env.example`, `README.md` with one-liner project description
- Create `dev` branch and push, share invite link with D2, D3, D4

### Files to create
```
storytrace/
├── backend/
│   ├── __init__.py          (empty)
│   ├── db/
│   │   └── __init__.py      (empty)
└── agents/
│   └── __init__.py          (empty)
├── frontend/
│   ├── pages/               (empty dir — .gitkeep)
│   └── components/          (empty dir — .gitkeep)
├── .gitignore
├── .env.example
├── requirements.txt
└── README.md
```

### `.gitignore` content
```
.env
__pycache__
*.pyc
node_modules
.next
.DS_Store
```

### `.env.example` content
```bash
# D1: Backend Infrastructure
DATABASE_URL=postgresql://user:password@localhost:5432/storytrace
REDIS_URL=redis://localhost:6379
WEBHOOK_URL=https://your-webhook-endpoint.com/alerts

# D2: Data Sources
GDELT_BASE_URL=https://api.gdeltproject.org/api/v2/doc/doc
NEWSAPI_KEY=your_newsapi_key_here

# D3: AI Models
FEATHERLESS_API_KEY=your_featherless_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# D4: Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000      # safe — public, just a URL
SPEECHMATICS_KEY=your_speechmatics_api_key_here  # NO NEXT_PUBLIC_ — stays server-side only
```

### `requirements.txt` content
```
fastapi==0.111.0
uvicorn==0.29.0
langgraph==0.1.0
langchain==0.2.0
openai==1.30.0
google-generativeai==0.7.0
feedparser==6.0.11
spacy==3.7.4
langdetect==1.0.9
psycopg2-binary==2.9.9
redis==5.0.4
requests==2.32.0
python-dotenv==1.0.1
pydantic==2.7.0
```

### Acceptance criteria
- [ ] `git clone` + `pip install -r requirements.txt` works
- [ ] All directories exist
- [ ] `.env` is in `.gitignore` (run `git check-ignore .env` to verify)
- [ ] `dev` branch exists on remote

---

## PR-02 — Database Schema & Connection Module
**Team:** D1 | **Branch:** `feature/database` | **Target hour:** 2–4 | **Depends on:** PR-01

### What to build
- SQL migrations file (create tables + indexes)
- `backend/db/connection.py` — three functions: `save_story`, `update_story`, `get_story`

### Files to create
**`backend/db/migrations.sql`**
```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE stories (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic         TEXT,
  input_url     TEXT,
  root_outlet   TEXT,
  root_url      TEXT,
  root_headline TEXT,
  root_text     TEXT,
  root_dna      JSONB,
  status        TEXT DEFAULT 'processing',
  created_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE outlet_versions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  story_id      UUID REFERENCES stories(id) ON DELETE CASCADE,
  outlet        TEXT NOT NULL,
  country       TEXT NOT NULL,
  url           TEXT,
  headline      TEXT,
  article_text  TEXT,
  dna           JSONB,
  drift_score   INTEGER CHECK (drift_score BETWEEN 0 AND 100),
  parent_outlet TEXT,
  language      TEXT DEFAULT 'en',
  crawled_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_outlet_story   ON outlet_versions(story_id);
CREATE INDEX idx_outlet_country ON outlet_versions(country);
CREATE INDEX idx_outlet_drift   ON outlet_versions(drift_score);
```

**`backend/db/connection.py`** — implement `get_conn()`, `save_story(job_id, user_input)`, `update_story(job_id, result, status)`, `get_story(job_id) -> dict | None`

Full reference implementation is in `STORYTRACE_FULL_CONTEXT.md` section 18.

> **Critical fix:** The raw `get_story` in the spec returns `{'job_id', 'status', 'versions': [raw tuples]}`. This does NOT match the API contract shape D4 depends on. You must add a `build_story_response()` helper that maps DB rows into the correct shape:

```python
def build_story_response(story_row, version_rows) -> dict:
    # story_row columns: id, topic, input_url, root_outlet, root_url,
    #                    root_headline, root_text, root_dna, status, created_at
    return {
        'job_id': str(story_row[0]),
        'status': story_row[8],
        'root': {
            'outlet':   story_row[3],
            'url':      story_row[4],
            'headline': story_row[5],
            'dna':      story_row[7] or {}
        },
        'tree': None  # reconstructed from version_rows in a future iteration
                      # for now, GET /story/{id} returns root + flat scored_list
    }
```

For the hackathon, returning a flat `scored_list` from `outlet_versions` rows (sorted by drift_score) is acceptable. D4 can render the tree from the flat list using `parent_outlet` as the parent key.

### Acceptance criteria
- [ ] `psql $DATABASE_URL -f backend/db/migrations.sql` runs without errors
- [ ] `save_story("test-uuid", "Iran nuclear")` inserts a row
- [ ] `get_story("test-uuid")` returns `{"job_id": ..., "status": "processing", "root": {...}, ...}` — matching API contract shape
- [ ] `update_story("test-uuid", {}, "failed")` updates the status column
- [ ] `get_story` response shape matches `StoryResponse` Pydantic model from PR-03

---

## PR-03 — FastAPI Skeleton & Pydantic Models
**Team:** D1 | **Branch:** `feature/fastapi-skeleton` | **Target hour:** 2–4 | **Depends on:** PR-02

> **This PR is the API Contract. It MUST be merged by Hour 4. D2, D3, D4 block on this.**

### What to build
- `backend/models.py` — Pydantic request/response models
- `backend/main.py` — FastAPI app with all routes (stubs are fine, real logic comes in PR-05)
- `/health`, `POST /analyze`, `GET /story/{job_id}`, `POST /forecast/{job_id}`

### Files to create
**`backend/models.py`**
```python
from pydantic import BaseModel
from typing import Optional, List

class AnalyzeRequest(BaseModel):
    url:   Optional[str] = None
    topic: Optional[str] = None

class AnalyzeResponse(BaseModel):
    job_id:   str
    status:   str
    poll_url: str

class DNASchema(BaseModel):
    facts_kept:    List[str]
    facts_dropped: List[str]
    tone:          str
    framing:       str
    political_lean:str

class TreeNode(BaseModel):
    id:           str
    outlet:       str
    country:      str
    url:          Optional[str]
    headline:     str
    drift_score:  int
    parent_id:    Optional[str]
    dna:          Optional[DNASchema]
    children:     Optional[List['TreeNode']] = []

class StoryResponse(BaseModel):
    job_id:  str
    status:  str
    root:    Optional[dict]
    tree:    Optional[list]
```

**`backend/main.py`** — full implementation per `STORYTRACE_FULL_CONTEXT.md` section 18, plus the four fixes below.

**Fix 1 — load_dotenv at the very top of main.py (before any agent import):**
```python
from dotenv import load_dotenv
load_dotenv()
```
Without this, `os.environ['FEATHERLESS_API_KEY']` raises `KeyError` in local dev (outside Docker).

**Fix 2 — CORS middleware (add immediately after `app = FastAPI(...)`):**
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Without this, every browser `fetch()` from D4's Next.js app gets a CORS error.

**Fix 3 — run_and_save must not block the event loop:**
```python
import asyncio

async def run_and_save(job_id: str, user_input: str):
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, run_pipeline, job_id, user_input)
        update_story(job_id, result, status='complete')
    except Exception as e:
        update_story(job_id, {}, status='failed')
```
`run_pipeline` calls LangGraph's synchronous `.invoke()`. Calling it directly inside `async def` blocks the entire FastAPI event loop for 30–60 seconds, making the API unresponsive during a run.

**Fix 4 — Add GET /story/recent (needed by PR-19 /explore page):**
```python
@app.get("/story/recent")
async def get_recent_stories():
    from backend.db.connection import get_recent
    return get_recent()
```
Also add to `connection.py`:
```python
def get_recent() -> list:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, topic, root_headline, root_outlet, status, created_at "
                "FROM stories WHERE status='complete' ORDER BY created_at DESC LIMIT 10"
            )
            rows = cur.fetchall()
            return [{"job_id": str(r[0]), "topic": r[1], "headline": r[2],
                     "outlet": r[3], "created_at": str(r[5])} for r in rows]
```

**Fix 5 — Redis cache on GET /story/{job_id}:**
```python
import redis, json as json_lib
r = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))

@app.get("/story/{job_id}")
async def get_story_result(job_id: str):
    cached = r.get(f"story:{job_id}")
    if cached:
        return json_lib.loads(cached)
    story = get_story(job_id)
    if not story:
        return {"error": "Story not found"}
    if story['status'] == 'complete':
        r.setex(f"story:{job_id}", 3600, json_lib.dumps(story))  # cache 1 hour
    return story
```

### Acceptance criteria
- [ ] `uvicorn backend.main:app --reload` starts without errors
- [ ] `GET /health` returns `{"status": "ok"}`
- [ ] `POST /analyze` with `{"topic": "test"}` returns 202 with `job_id` and `poll_url`
- [ ] `GET /story/{fake-uuid}` returns `{"error": "Story not found"}` — not a 500
- [ ] `GET /story/recent` returns a list (empty list is fine at this stage)
- [ ] `GET /docs` (Swagger) shows all 5 routes with correct schemas
- [ ] `fetch('http://localhost:8000/health')` from browser console on port 3000 returns without CORS error
- [ ] **Post the Swagger URL in the group chat when merged** — this is the H4 API Contract Lock

---

## PR-04 — LangGraph Orchestrator
**Team:** D1 | **Branch:** `feature/orchestrator` | **Target hour:** 4–7 | **Depends on:** PR-03

### What to build
- `backend/orchestrator.py` — LangGraph `StateGraph` wiring all 7 agents in sequence
- Agent stubs in `agents/` so the graph compiles (each stub's `run()` just returns state unchanged)

### Agent execution order
```
seed → crawler → translator → dna → scorer → geo → alert → END
```

### Files to create/modify
**`backend/orchestrator.py`** — full implementation per `STORYTRACE_FULL_CONTEXT.md` section 17

**Agent stubs** (D2 and D3 will replace these bodies — just make them importable):
```python
# agents/seed_agent.py  (stub)
def run(state: dict) -> dict:
    return state

# agents/crawler_agent.py (stub)
# agents/translator.py    (stub)
# agents/dna_extractor.py (stub)
# agents/drift_scorer.py  (stub)
# agents/geo_builder.py   (stub)
# agents/alert_agent.py   (stub)
```

> **Contract note to add as a comment in orchestrator.py:**
> The Translator mutates `state['articles']` in-place — it updates `art['text']` and `art['language']` directly on each dict in the list. The DNA Extractor then reads the already-translated text from `state['articles']`. Do NOT have the Translator produce a new list under a different key — it writes back into the same list.

### Acceptance criteria
- [ ] `from backend.orchestrator import pipeline` imports without errors
- [ ] `pipeline.invoke({"job_id": "test", "input": "Iran nuclear"})` runs without raising (even with stub agents)
- [ ] Running the full pipeline through `/analyze` creates a DB row and updates it to `complete`

---

## PR-05 — Docker Compose & Backend Dockerfile
**Team:** D1 | **Branch:** `feature/docker` | **Target hour:** 1–3 | **Depends on:** PR-01

> Can run in parallel with PR-02 and PR-03.

### What to build
- `docker-compose.yml` — postgres, redis, api, frontend services
- `backend/Dockerfile`
- Vultr one-time server setup script (document in `README.md`)

### Files to create
**`docker-compose.yml`** — full content per `STORYTRACE_FULL_CONTEXT.md` section 22

**`backend/Dockerfile`**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`frontend/Dockerfile`** (missing from spec — required by docker-compose `build: ./frontend`):
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### Acceptance criteria
- [ ] `docker-compose up -d db redis` starts Postgres and Redis
- [ ] `docker-compose up api` starts without errors after PR-03 is merged
- [ ] `docker-compose up frontend` builds and starts without errors after PR-14 is merged
- [ ] `curl http://localhost:8000/health` returns `{"status": "ok"}`

---

## PR-06 — Agent 1: Story Seed
**Team:** D2 | **Branch:** `feature/agent-seed` | **Target hour:** 2–5 | **Depends on:** PR-04

### What to build
Replace stub `agents/seed_agent.py` with the real implementation.

### Logic
1. Extract named entities from user input using spaCy (local — zero tokens)
2. Query GDELT API for earliest matching article (root story)
3. If GDELT returns nothing → fallback to NewsAPI
4. Populate `state['root']` and `state['entities']`

### Full implementation
See `STORYTRACE_FULL_CONTEXT.md` section 10. Copy the pseudocode exactly — it is production-ready.

### Key details
- GDELT params: `mode=artlist`, `maxrecords=5`, `sort=DateAsc` (earliest = root)
- spaCy labels to keep: `PERSON`, `ORG`, `GPE`, `EVENT`, `NORP`
- Never raise from `run()` — set `state['error']` and return

### Acceptance criteria
- [ ] `seed_agent.run({"input": "Iran nuclear talks"})` returns a dict with `state['root']` populated
- [ ] `state['entities']` contains at least one string
- [ ] Works when GDELT times out (NewsAPI fallback returns root)
- [ ] Never raises an exception — always returns state

---

## PR-07 — Agent 2: Crawler
**Team:** D2 | **Branch:** `feature/agent-crawler` | **Target hour:** 5–9 | **Depends on:** PR-06

### What to build
Replace stub `agents/crawler_agent.py` with the real implementation.

### Logic
1. For each of 15 RSS feeds: parse feed with feedparser
2. Check each entry's headline for entity match (local string comparison — zero tokens)
3. On match: fetch first 300 words of the article URL
4. One article per outlet maximum
5. Failures silently continue — never block the pipeline

### RSS feeds to implement (all 15)
```
BBC, Al Jazeera, Dawn, CNN, RT, Times of India, Guardian,
Fox News, DW, France24, NDTV, Arab News, Sputnik, NHK, TASS
```
Full URLs in `STORYTRACE_FULL_CONTEXT.md` section 11.

### Full implementation
See `STORYTRACE_FULL_CONTEXT.md` section 11.

### Acceptance criteria
- [ ] `crawler_agent.run({"entities": ["Iran", "nuclear"]})` returns `state['articles']` as a list
- [ ] Each article dict has keys: `outlet`, `url`, `headline`, `text`, `language`
- [ ] `text` is capped at 300 words
- [ ] If a feed is unreachable, that outlet is silently skipped (no exception)
- [ ] Test with a real entity — should match at least 3–5 outlets

---

## PR-08 — Agent 7: Alert Agent
**Team:** D2 | **Branch:** `feature/agent-alert` | **Target hour:** 12–16 | **Depends on:** PR-04

### What to build
Replace stub `agents/alert_agent.py` with the real implementation.

### Logic
- Iterate `state['scored_list']`
- For each article where `drift_score >= 70`: POST JSON payload to `WEBHOOK_URL`
- Webhook POST is best-effort — exception must not block the pipeline
- Set `state['alerts_fired']` to list of outlet names that triggered

### Full implementation
See `STORYTRACE_FULL_CONTEXT.md` section 16.

### Acceptance criteria
- [ ] When `drift_score >= 70` and `WEBHOOK_URL` is set, a POST is made
- [ ] When `WEBHOOK_URL` is empty, no exception is raised
- [ ] `state['alerts_fired']` is always set (even if empty list)
- [ ] Pipeline completes normally even if webhook endpoint is unreachable

---

## PR-09 — Agent 3: DNA Extractor
**Team:** D3 | **Branch:** `feature/agent-dna` | **Target hour:** 2–7 | **Depends on:** PR-04

### What to build
Replace stub `agents/dna_extractor.py` with the real implementation.

### Logic
1. For each article in `state['articles']`: call Featherless API (OpenAI-compatible)
2. Model: `mistralai/Mistral-7B-Instruct-v0.3`
3. Extract structured DNA JSON: `facts_kept`, `facts_dropped`, `tone`, `framing`, `political_lean`
4. Strip markdown fences if model wraps output in ` ```json ` blocks
5. On failure: return safe fallback dict (empty lists, `"unknown"` strings)
6. Set `state['dna_list']`

### Full implementation
See `STORYTRACE_FULL_CONTEXT.md` section 12. The prompt template is finalized — do not change it.

### Acceptance criteria
- [ ] `dna_extractor.run(state)` returns `state['dna_list']` — one entry per article
- [ ] Each entry has `dna` key with all 5 fields
- [ ] Invalid JSON from model falls back gracefully — no exception
- [ ] Test with a real article text + root text → verify JSON parses cleanly

---

## PR-10 — Agent 4: Translator
**Team:** D3 | **Branch:** `feature/agent-translator` | **Target hour:** 15–18 | **Depends on:** PR-04

> Build this after PR-09 (DNA Extractor). It runs before DNA in the pipeline but is simpler.

### What to build
Replace stub `agents/translator.py` with the real implementation.

### Logic
1. For each article in `state['articles']`: use `langdetect` to detect language
2. If non-English: call Gemini 1.5 Flash to translate, preserving tone and framing
3. Write translated text back into `art['text']`, set `art['language']` to detected lang code
4. `LangDetectException` → assume English, skip
5. English articles → skip entirely (zero cost)

### Full implementation
See `STORYTRACE_FULL_CONTEXT.md` section 13.

### Acceptance criteria
- [ ] English articles are untouched (no Gemini call made)
- [ ] Non-English text is translated and `art['language']` is set correctly
- [ ] `LangDetectException` is caught silently
- [ ] Test with a known non-English string (e.g., French or Arabic article excerpt)

---

## PR-11 — Agent 5: Drift Scorer
**Team:** D3 | **Branch:** `feature/agent-drift-scorer` | **Target hour:** 7–11 | **Depends on:** PR-09

### What to build
Replace stub `agents/drift_scorer.py` with the real implementation.

### Algorithm (pure Python, zero tokens)
- **Fact score (0–60 pts):** ratio of root facts dropped by this outlet × 60
- **Tone score (0–40 pts):** absolute tone distance from root using `TONE_MAP`
- **Total drift = fact_score + tone_score, capped at 100**
- **Parent outlet:** the lowest-drift outlet scored so far (contagion chain heuristic)

### Tone map
```python
TONE_MAP = {
    'neutral': 0, 'supportive': 20,
    'dismissive': 35, 'alarming': 50, 'unknown': 0
}
```

### Full implementation
See `STORYTRACE_FULL_CONTEXT.md` section 14.

### Acceptance criteria
- [ ] `compute_drift({}, {})` returns 0 without error
- [ ] An outlet that drops all root facts and uses "alarming" tone scores 100
- [ ] An outlet that keeps all root facts and is neutral scores 0
- [ ] `state['scored_list']` is sorted by `drift_score` ascending
- [ ] Every entry has both `drift_score` (int 0–100) and `parent_outlet` (string)

---

## PR-12 — Agent 6: Geo-Branch Builder
**Team:** D3 | **Branch:** `feature/agent-geo-builder` | **Target hour:** 11–15 | **Depends on:** PR-11

### What to build
Replace stub `agents/geo_builder.py` with the real implementation.

### Logic
1. Group `state['scored_list']` by country using `OUTLET_COUNTRY` map
2. Build nested tree: root node → country branch nodes → outlet leaf nodes
3. Each country branch has `avg_drift` of its outlets
4. Sort country branches by avg drift (lowest first)
5. Set `state['tree']`

### Outlet-to-country mapping (full list in spec section 15)
```
BBC → UK, Guardian → UK, Reuters → US, CNN → US, Fox News → US,
Al Jazeera → Qatar, Arab News → Saudi Arabia, Dawn → Pakistan,
RT → Russia, Sputnik → Russia, TASS → Russia, DW → Germany,
France24 → France, NDTV → India, Times of India → India, NHK → Japan
```

### Full implementation
See `STORYTRACE_FULL_CONTEXT.md` section 15.

> **Critical fix:** The Crawler agent never sets `art['country']` — only `outlet`, `url`, `headline`, `text`, `language`. The `update_story` DB function reads `art.get('country', 'Unknown')` from `scored_list`. If Geo-Builder doesn't write `country` back into each article dict, every `outlet_versions.country` row will be `'Unknown'`.
>
> Add this at the top of `geo_builder.run()`, before building the tree:
> ```python
> for art in state.get('scored_list', []):
>     art['country'] = OUTLET_COUNTRY.get(art['outlet'], 'Other')
> ```

### Acceptance criteria
- [ ] `state['tree']` is a dict with `id: "root"` and a `children` list
- [ ] Country branch nodes have `type: "country_branch"` and `drift_score` (average)
- [ ] Outlet leaf nodes have `type: "outlet"` and all required D3-ready fields
- [ ] Unknown outlets go under country `"Other"`
- [ ] Tree is valid JSON — paste into `JSON.parse()` in browser console to verify
- [ ] After the pipeline runs, `SELECT DISTINCT country FROM outlet_versions` returns real country names (not all `'Unknown'`)

---

## PR-13 — Agent Integration End-to-End Test
**Team:** D1 + D2 + D3 | **Branch:** `feature/e2e-pipeline` | **Target hour:** 10–12 | **Depends on:** PR-04 through PR-12

> This is the H10 sync point. Do not skip it.

### What to build
- `tests/__init__.py` (empty)
- `tests/test_pipeline.py` — runs the full 7-agent pipeline against a real topic
- Add `pytest==8.2.0` to `requirements.txt`

### Test script
```python
# tests/test_pipeline.py
from dotenv import load_dotenv
load_dotenv()

from backend.orchestrator import run_pipeline

def test_full_pipeline():
    result = run_pipeline("test-job-001", "Iran nuclear talks")
    assert result.get('root') is not None, "root story not found"
    assert isinstance(result.get('scored_list'), list), "scored_list missing"
    assert len(result['scored_list']) >= 3, "fewer than 3 outlets matched"
    assert isinstance(result.get('tree'), dict), "tree not built"
    assert 'children' in result['tree'], "tree has no children"
    assert len(result['tree']['children']) >= 2, "fewer than 2 country branches"
    print(f"\nOutlets found: {len(result['scored_list'])}")
    print(f"Tree branches: {len(result['tree']['children'])}")
```

### How to run
```bash
pytest tests/test_pipeline.py -v -s
```

### Acceptance criteria
- [ ] `pytest tests/test_pipeline.py -v -s` runs without exceptions
- [ ] `result['root']` has a non-empty `headline` and `outlet`
- [ ] `result['scored_list']` has at least 3 entries, each with `drift_score` and `parent_outlet`
- [ ] `result['tree']['children']` has at least 2 country branches
- [ ] Every article in `scored_list` has `country` set (not `'Unknown'`) — verifies PR-12 fix
- [ ] `GET /story/{job_id}` after the run returns `status: complete` with `root` and tree data
- [ ] **Share the tree JSON output in the group chat at H10**

---

## PR-14 — Frontend Setup & Routing
**Team:** D4 | **Branch:** `feature/frontend-setup` | **Target hour:** 0–2 | **Depends on:** PR-01

> Can start immediately — no backend dependency.

### What to build
```bash
cd storytrace
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend
npm install d3
```

- Basic layout component with StoryTrace branding
- Route structure: `/` (home), `/story/[id]` (drift view), `/explore` (cached dashboard)
- Global color tokens in Tailwind config:
  - `navy: #1B3A6B`, `blue: #2E5FA3`, `green: #27A06A`, `amber: #F59E0B`, `red: #E8562A`

### Files to create
```
frontend/
├── app/
│   ├── layout.tsx          ← global nav, fonts
│   ├── page.tsx            ← redirect to pages/index or home content
│   ├── story/[id]/
│   │   └── page.tsx        ← placeholder: "Story view coming in PR-17"
│   └── explore/
│       └── page.tsx        ← placeholder: "Explore coming soon"
├── components/             ← empty, ready for PR-15 through PR-19
└── tailwind.config.ts      ← add custom color tokens
```

### Acceptance criteria
- [ ] `npm run dev` starts on port 3000
- [ ] `/` renders without errors
- [ ] `/story/abc` renders without errors (dynamic route works)
- [ ] Tailwind custom colors are available in className props

---

## PR-15 — DriftTree D3 Component (Static Mock Data)
**Team:** D4 | **Branch:** `feature/drift-tree` | **Target hour:** 2–6 | **Depends on:** PR-14

### What to build
`frontend/components/DriftTree.jsx` — the hero visual. Use hardcoded mock tree JSON so it renders independently of the backend.

### Full implementation
See `STORYTRACE_FULL_CONTEXT.md` section 19 — the full D3.js component code is there. Copy it exactly.

### Mock data to use during development
```json
{
  "id": "root", "outlet": "Reuters", "country": "US",
  "drift_score": 0, "type": "root",
  "children": [
    {
      "id": "branch-UK", "country": "UK", "type": "country_branch", "drift_score": 15,
      "children": [
        { "id": "node-BBC", "outlet": "BBC", "drift_score": 18, "type": "outlet",
          "headline": "Iran steps back from nuclear site", "dna": {
            "facts_kept": ["withdrawal", "Fordow"],
            "facts_dropped": ["IAEA inspection"],
            "tone": "neutral", "framing": "Diplomatic de-escalation", "political_lean": "center"
          }, "children": [] }
      ]
    },
    {
      "id": "branch-Russia", "country": "Russia", "type": "country_branch", "drift_score": 72,
      "children": [
        { "id": "node-RT", "outlet": "RT", "drift_score": 72, "type": "outlet",
          "headline": "Western pressure forces Iran compromise", "dna": {
            "facts_kept": ["Fordow"],
            "facts_dropped": ["IAEA inspection", "partial withdrawal"],
            "tone": "alarming", "framing": "Western aggression narrative", "political_lean": "right"
          }, "children": [] }
      ]
    }
  ]
}
```

### Color scale
- `drift_score 0` → `#27A06A` (green)
- `drift_score 50` → `#F59E0B` (amber)
- `drift_score 100` → `#E8562A` (red)

### Acceptance criteria
- [ ] Tree renders in browser with at least 2 country branches
- [ ] Nodes are colored by drift score (green/amber/red gradient)
- [ ] Drift score number is visible inside each circle
- [ ] Outlet name is visible below each circle
- [ ] Clicking a node calls `onNodeClick(nodeData)` — verify with `console.log`

---

## PR-16 — DiffPanel Component
**Team:** D4 | **Branch:** `feature/diff-panel` | **Target hour:** 6–10 | **Depends on:** PR-15

### What to build
`frontend/components/DiffPanel.jsx` — shows facts diff when a tree node is clicked.

### Full implementation
See `STORYTRACE_FULL_CONTEXT.md` section 19 — the full component code is there. Copy it exactly.

### Wire it to DriftTree
In the story page (`/story/[id]/page.tsx`):
```tsx
const [selectedNode, setSelectedNode] = useState(null)

<DriftTree treeData={mockData} onNodeClick={setSelectedNode} />
<DiffPanel node={selectedNode} root={mockData} />
```

### Acceptance criteria
- [ ] Clicking a tree node shows the DiffPanel below the tree
- [ ] "Facts Dropped" column shows red pills for facts in root but not in the node
- [ ] "Facts Kept" column shows green pills for facts present in both
- [ ] Tone and political lean badges are visible at the bottom
- [ ] Clicking the root node shows "None dropped" in the dropped column

---

## PR-17 — Home Page & API Integration
**Team:** D4 | **Branch:** `feature/api-integration` | **Target hour:** 10–14 | **Depends on:** PR-15, PR-03 (backend must be running)

### What to build
- `frontend/pages/index.jsx` (or `app/page.tsx`) — URL/topic input + submit button
- API integration: `POST /analyze` → poll `GET /story/{id}` every 2 seconds → render tree when complete
- Loading state: show progress message while polling

### Logic flow
```
User submits URL or topic
  → POST /analyze → receive { job_id, poll_url }
  → setInterval poll GET /story/{job_id} every 2000ms
  → while status === "processing": show "Analyzing..." + progress message
  → when status === "complete": clear interval, render DriftTree + DiffPanel
  → when status === "failed": show error message
```

### Environment variable
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```
All fetch calls: `fetch(process.env.NEXT_PUBLIC_API_URL + '/analyze')`

### Acceptance criteria
- [ ] Submitting a topic triggers a POST to `/analyze`
- [ ] A spinner/loading message appears while polling
- [ ] The drift tree renders when pipeline completes
- [ ] A failure status shows a readable error message
- [ ] Input is disabled while polling is in progress

---

## PR-18 — VoiceInput Component (Speechmatics)
**Team:** D4 | **Branch:** `feature/voice-input` | **Target hour:** 14–18 | **Depends on:** PR-17

### What to build
- `frontend/components/VoiceInput.jsx` — microphone button using Speechmatics real-time WebSocket
- `frontend/pages/api/speechmatics-token.js` — Next.js API route to exchange Speechmatics key for JWT (key stays server-side)
- Wire voice transcript into the home page input box

### Full implementation
See `STORYTRACE_FULL_CONTEXT.md` section 19 for the VoiceInput component code.

### Speechmatics API route
```js
// pages/api/speechmatics-token.js
export default async function handler(req, res) {
  const r = await fetch('https://mp.speechmatics.com/v1/api_keys?type=rt', {
    method: 'POST',
    headers: {
      // IMPORTANT: use SPEECHMATICS_KEY, NOT NEXT_PUBLIC_SPEECHMATICS_KEY
      // NEXT_PUBLIC_ prefix bundles the value into client JS and exposes it in the browser
      'Authorization': `Bearer ${process.env.SPEECHMATICS_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ ttl: 60 })
  })
  const data = await r.json()
  res.json({ token: data.key_value })
}
```

> **Key naming fix:** `.env.example` in PR-01 uses `NEXT_PUBLIC_SPEECHMATICS_KEY`. Rename it to `SPEECHMATICS_KEY` (no `NEXT_PUBLIC_` prefix). The `NEXT_PUBLIC_` prefix tells Next.js to bundle the value into client-side JavaScript — visible to anyone who opens DevTools. The secret key must stay server-side only; the JWT short-lived token is what the browser receives.

### Acceptance criteria
- [ ] Clicking the mic button starts recording (button turns red + pulses)
- [ ] Speaking a topic populates the text input in real time
- [ ] Clicking Stop closes the WebSocket connection
- [ ] Opening DevTools → Network tab shows NO request that contains the raw Speechmatics API key
- [ ] The API route `/api/speechmatics-token` returns a short-lived JWT, not the raw key

---

## PR-19 — UI Polish & Loading States
**Team:** D4 | **Branch:** `feature/ui-polish` | **Target hour:** 18–22 | **Depends on:** PR-17, PR-18

### What to build
- Skeleton loader while tree is loading
- Error boundary for failed API calls
- Mobile responsive layout (tree scrolls horizontally on small screens)
- `/explore` page — list of recent completed stories from `GET /story/recent` (if D1 adds that route) or a static placeholder
- Empty state for DiffPanel ("Click a node to see facts diff")
- Drift score legend (green/amber/red color key)

### Acceptance criteria
- [ ] App works on iPhone-sized screen (375px wide) without horizontal overflow
- [ ] Submitting an empty form shows a validation message
- [ ] Network error during polling shows a retry button
- [ ] No console errors in the browser on happy path

---

## PR-20 — Forecast Agent (Optional — D3 only if ahead of schedule)
**Team:** D3 | **Branch:** `feature/agent-forecast` | **Target hour:** 18–22 | **Depends on:** PR-13

> Only build this after H16 integration check confirms Use Case 1 is fully working.

### What to build
`agents/forecast_agent.py` — Gemini Pro analysis of the root story's geopolitical impact.

### Full implementation
See `STORYTRACE_FULL_CONTEXT.md` section 20.

### Acceptance criteria
- [ ] `POST /forecast/{job_id}` returns structured JSON with `countries`, `event_type`, `panic_forecasts`
- [ ] Works only when story status is `complete`
- [ ] JSON parse failure returns `{"error": "..."}` — never a 500

---

## PR-21 — Vultr Deployment & Nginx
**Team:** D1 | **Branch:** `feature/deployment` | **Target hour:** 20–23 | **Depends on:** PR-13

> Run after Demo Run #1 confirms the pipeline is stable.

### What to build
- Nginx config for Vultr Ubuntu 22.04 VM
- `docker-compose up -d` all services on Vultr
- Public URL verified and shared with team

### Server setup steps
1. `ssh root@<vultr-ip>`
2. `apt update && apt install -y docker.io docker-compose nginx certbot`
3. `git clone <repo> && cd storytrace`
4. `cp .env.example .env && nano .env` — fill all API keys
5. `docker-compose up -d`
6. Configure Nginx per `STORYTRACE_FULL_CONTEXT.md` section 22
7. `sudo nginx -t && sudo systemctl restart nginx`

### Acceptance criteria
- [ ] `curl http://<vultr-ip>/health` returns `{"status": "ok"}`
- [ ] `curl http://<vultr-ip>/` serves the Next.js frontend
- [ ] Full pipeline runs on Vultr with a real topic
- [ ] **Share public URL in group chat**

---

## PR-22 — Final Integration, README & Submission Tag
**Team:** All | **Branch:** `feature/submission` | **Target hour:** 22–23 | **Depends on:** All PRs

### What to build
- `README.md` — project overview, demo GIF or screenshot, setup instructions, API reference
- Merge `dev` → `main` (D1 does this)
- Tag: `git tag v1.0.0 && git push origin v1.0.0`

### README must include
1. What StoryTrace does (2 sentences)
2. Live demo URL (Vultr)
3. Local setup: `git clone`, `cp .env.example .env`, `docker-compose up`
4. API reference: the 4 endpoints with example curl commands
5. Tech stack table (copy from spec section 6)
6. Team names

### Acceptance criteria
- [ ] `main` branch is clean and passes a fresh `docker-compose up`
- [ ] `v1.0.0` tag exists on remote
- [ ] Demo video recorded (voice input → tree renders → node click → diff panel)
- [ ] Submission form submitted before deadline

---

## Dependency Graph

```
PR-01 (scaffold)
  ├── PR-02 (database)
  │     └── PR-03 (FastAPI) ← H4 API Contract Lock
  │           └── PR-04 (orchestrator)
  │                 ├── PR-06 (seed agent)        [D2]
  │                 │     └── PR-07 (crawler)     [D2]
  │                 ├── PR-08 (alert agent)       [D2]
  │                 ├── PR-09 (DNA extractor)     [D3]
  │                 │     └── PR-11 (drift scorer)[D3]
  │                 │           └── PR-12 (geo builder) [D3]
  │                 └── PR-10 (translator)        [D3]
  │
  └── PR-05 (docker)        [D1 — parallel with PR-02]

PR-04 + PR-06..PR-12 → PR-13 (e2e test) ← H10 Pipeline Check

PR-01 → PR-14 (frontend setup)  [D4 — starts at hour 0]
  └── PR-15 (drift tree)
        ├── PR-16 (diff panel)
        └── PR-17 (API integration) ← H16 Frontend Integration
              └── PR-18 (voice input)
                    └── PR-19 (UI polish)

PR-13 → PR-20 (forecast agent)  [optional]
PR-13 → PR-21 (deployment)
All  → PR-22 (submission)
```

---

## Commit Message Format

```
[D1] Add FastAPI skeleton with /analyze and /story endpoints
[D2] Implement Story Seed agent with GDELT + NewsAPI fallback
[D3] Add Featherless DNA extractor with strict JSON schema validation
[D4] Render D3.js drift tree with static mock data
```

## PR Rules
1. PR from `feature/*` → `dev` only. Never directly to `main`.
2. One teammate reviews and approves — max 10 minutes. Do not block the sprint.
3. Squash merge to keep history clean.
4. If blocked for more than 30 minutes → message group chat immediately.
