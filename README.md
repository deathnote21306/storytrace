# StoryTrace — Git for News

> Track how a news story mutates, drifts, and branches across 15+ global outlets — visualized as a Git commit tree.

---

## What Is StoryTrace?

When a major event happens — a military strike, an election result, a financial collapse — the story doesn't stay the same. It starts as a wire dispatch from AP or Reuters and, within hours, has been rewritten by dozens of outlets across the world. Facts get dropped. Quotes get reframed. Headlines shift from neutral to alarming. A story that started as "ceasefire talks stall" becomes "diplomacy collapses" in one country, and "peace process on track" in another.

**StoryTrace is the first system that tracks this mutation end-to-end.**

You paste any article URL — or simply speak a topic — and StoryTrace:

1. Finds the **original wire story** (the root of the narrative)
2. **Crawls 15+ global outlets** to find every version of that story
3. Extracts the **narrative DNA** of each version: who are the actors, what are the core claims, what facts were added or removed
4. **Scores narrative drift** from 0 to 100 — how far has this outlet's version drifted from the original facts
5. **Visualizes the full mutation chain** as a Git commit tree — root commit (wire source) → country branches → outlet leaves — with clickable diff panels showing exactly what changed at each node
6. **Fires alerts** when any outlet exceeds a drift threshold of 70, enabling real-time monitoring of misinformation spread

The analogy to Git is precise and intentional. Just as Git tracks every change to code, shows who made it, and lets you diff any two versions, StoryTrace tracks every change to a narrative, shows which outlet caused each mutation, and lets you compare any two outlet versions side-by-side.

---

## Why This Matters

### The Problem No One Has Solved

Misinformation research has historically been reactive: fact-checkers identify false claims after they've already spread. Existing tools (NewsGuard, AllSides, Ground News) rate outlets by general bias but have **no memory of how a specific story evolves over time**. They tell you an outlet leans left — they cannot tell you that this outlet, on this story, dropped three key facts and added two unverified claims.

Two research papers published in late 2024 and early 2025 explicitly identify this gap:

- **Fine-grained Narrative Classification in Biased News Articles** (arXiv:2512.03582, Dec 2025) — identifies that no temporal, cross-outlet, cross-country narrative tracking system exists
- **Media Bias Detector** (arXiv:2502.06009, Feb 2025) — analyzes one article at a time with no relational or temporal memory

StoryTrace is the answer to the gap both papers describe.

### Who Needs This

| User | How They Use It |
|---|---|
| **Journalists** | Trace a story back to its wire source; see which outlets diverged and when |
| **Intelligence analysts** | Monitor how a geopolitical narrative spreads and mutates across countries in real-time |
| **Newsrooms** | Know immediately when a competitor outlet makes a factual departure from the established record |
| **Media researchers** | Study narrative contagion patterns at scale, with structured drift scores rather than manual annotation |
| **Citizens** | Understand, at a glance, whether the article they're reading is close to the source or heavily mutated |

### Why the Git Metaphor Works

Version control is universally understood by technical audiences and increasingly by the general public. The metaphor carries the right cognitive load:

- **Root commit** = original wire story
- **Branch** = country or media ecosystem
- **Commit** = each outlet's rewrite
- **Diff** = the facts added, changed, or dropped
- **Drift score** = how many lines changed, in semantic terms

This isn't just a visual choice — it's a conceptual framework that makes narrative mutation legible.

---

## How It Works: The Agent Pipeline

StoryTrace runs a **LangGraph orchestration pipeline** of 7 specialized AI agents. Each agent is responsible for exactly one task, and they pass structured JSON state between them. This design is intentional: no single LLM handles everything. Instead, the right tool is used for each job.

```
User (URL or Voice)
        │
        ├── [Speechmatics WebSocket] — voice → text
        │
        ▼
FastAPI  POST /analyze
        │
        ▼
LangGraph Orchestrator
        │
        ├── Agent 1: Story Seed      → GDELT API
        │   Finds the original wire story from the given URL or topic.
        │   Queries GDELT to locate the earliest known version.
        │
        ├── Agent 2: Crawler         → 15 RSS feeds + spaCy NER
        │   Fetches all outlet versions of the story.
        │   Uses spaCy Named Entity Recognition locally (zero token cost)
        │   to filter irrelevant articles before any LLM call.
        │
        ├── Agent 3: DNA Extractor   → Featherless API (Mistral-7B)
        │   Extracts the "narrative DNA" of each article:
        │   actors, core claims, key facts. Structured JSON output.
        │   Only the first 300 words per article are sent to the LLM.
        │
        ├── Agent 4: Translator      → Google Gemini Flash
        │   Translates non-English articles before DNA extraction.
        │   Handles multi-language coverage of global stories.
        │
        ├── Agent 5: Drift Scorer    → Python math + DNA comparison
        │   Computes a 0–100 drift score by comparing each outlet's
        │   DNA against the root story's DNA. Measures semantic
        │   divergence: facts added, facts dropped, framing shifts.
        │
        ├── Agent 6: Geo-Branch Builder → PostgreSQL
        │   Assembles the full commit tree by outlet and country.
        │   Persists the tree structure and drift history to the DB.
        │
        └── Agent 7: Alert Agent     → Webhook / email
            Fires an alert when any outlet's drift score exceeds 70.
            Enables real-time monitoring without manual polling.
        │
        ▼
PostgreSQL (stories, outlet_versions, drift history)
        │
        ▼
Next.js Dashboard
        ├── D3.js Git Commit Tree  ←  main visualization
        ├── Facts Diff Panel (click any node to see exact changes)
        └── Impact Forecast Panel  ←  Gemini Pro (on-demand)
```

### Token Efficiency

The pipeline is designed to minimize LLM cost:

- spaCy NER runs **locally** — zero tokens, filters articles before any LLM call
- RSS headline matching runs **locally** — zero tokens
- Only the **first 300 words** of each matched article are sent to the LLM
- Featherless does **structured JSON extraction**, not open-ended summarization
- Total cost: ~4,000–6,000 tokens per full pipeline run

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14.3 + FastAPI + Uvicorn |
| Agent pipeline | LangGraph StateGraph (7 agents) |
| NLP (local) | spaCy `en_core_web_sm` + langdetect |
| DNA extraction | Featherless API (Mistral-7B) |
| Translation | Google Gemini Flash |
| Forecasting | Google Gemini Pro |
| Database | PostgreSQL 15 + psycopg2 |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Visualization | D3.js v7 |
| Voice input | Speechmatics real-time WebSocket |
| Data sources | GDELT API, NewsAPI, 15 RSS feeds |
| Deployment | Docker Compose + Nginx + Render / Vultr |

---

## Prerequisites

- Python 3.14.3+
- Node.js 18+
- PostgreSQL 15+

---

## Environment Setup

Copy the example env file and fill in your API keys:

```bash
cp .env.example .env
```

Open `.env` and set the following:

| Variable | Where to get it |
|---|---|
| `DATABASE_URL` | Your local or hosted PostgreSQL connection string |
| `NEWSAPI_KEY` | [newsapi.org](https://newsapi.org) |
| `FEATHERLESS_API_KEY` | [featherless.ai](https://featherless.ai) |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com) |
| `WEBHOOK_URL` | Any endpoint to receive high-drift alerts (optional) |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` for local dev |
| `SPEECHMATICS_KEY` | [Speechmatics](https://speechmatics.com) — **never use `NEXT_PUBLIC_` prefix** |

---

## Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Download the spaCy English model (required by seed_agent and crawler_agent)
python -m spacy download en_core_web_sm
```

### Initialize the Database

Make sure PostgreSQL is running and `DATABASE_URL` is set in `.env`, then:

```bash
psql $DATABASE_URL -f backend/db/migrations.sql
```

This creates the `stories` and `outlet_versions` tables plus three indexes. Safe to re-run on a fresh database; will error if tables already exist — use `DROP TABLE` first to reset.

### Run the Backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify it's running:

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Running Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v

# Single file
python -m pytest tests/test_seed_agent.py -v

# Single test
python -m pytest tests/test_seed_agent.py::test_run_with_topic_uses_gdelt -v
```

All external calls are mocked — no running services or API keys required.

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

App runs at [http://localhost:3000](http://localhost:3000).

---

## Full Stack with Docker

**Local development:**

```bash
docker compose up -d
docker compose logs -f api
docker compose down
```

**Hackathon (fastest):** see [deploy/HACKATHON.md](deploy/HACKATHON.md) — Render Blueprint, ~20 min, free tier.

**Production (VPS):** see [deploy/DEPLOY.md](deploy/DEPLOY.md) for Vultr/Ubuntu + Nginx + `docker-compose.prod.yml`.

The database schema is applied automatically on first startup.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze` | Submit a URL or topic; returns `job_id` and `poll_url` (202) |
| `GET` | `/story/{job_id}` | Poll for results; returns full tree JSON when `status == "complete"` |
| `GET` | `/story/recent` | Returns the 10 most recently completed stories |
| `POST` | `/forecast/{job_id}` | Gemini Pro world-impact forecast (optional, runs after pipeline completes) |
| `GET` | `/health` | Health check |

### Example: submit a topic and poll for results

```bash
# Submit
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"topic": "Iran nuclear talks"}'

# Poll (replace <job_id> with the value returned above)
curl http://localhost:8000/story/<job_id>
```

---

## Origin

StoryTrace was conceived and built during a hackathon. The core concept — applying version control semantics to track narrative mutation across global media — originated from the observation that while software engineers have Git to audit every change to a codebase, journalists and citizens have no equivalent tool to audit every change to a story.

The project targets four hackathon tracks: Agentic Workflows, Collaborative Multi-Agent Systems, Enterprise Utility, and Intelligent Reasoning.

---

## License

MIT
