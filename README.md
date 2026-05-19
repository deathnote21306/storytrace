# StoryTrace

**Git for News** — paste any article URL or speak a topic, and StoryTrace finds the original wire story, tracks how it mutated across 15 outlets and countries, scores narrative drift 0–100, and visualizes the mutation chain as a Git commit tree.

---

## Prerequisites

- Python 3.14.3+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

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
| `REDIS_URL` | Your local or hosted Redis URL |
| `NEWSAPI_KEY` | [newsapi.org](https://newsapi.org) |
| `FEATHERLESS_API_KEY` | [featherless.ai](https://featherless.ai) |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com) |
| `WEBHOOK_URL` | Any endpoint to receive high-drift alerts (optional) |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` for local dev |
| `SPEECHMATICS_KEY` | [Speechmatics](https://speechmatics.com) — **never use `NEXT_PUBLIC_` prefix** |

---

## Backend Setup

```bash
# Create venv
python -m venv venv

# Activate the virtual environment first
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

This creates two tables (`stories`, `outlet_versions`) and three indexes. Safe to re-run on a fresh database; will error if tables already exist (use `DROP TABLE` first to reset).

### Run the Backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify it's running:

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

Swagger UI is available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Running Tests

```bash
# Activate the virtual environment first
source venv/bin/activate

# Run the full test suite
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_seed_agent.py -v

# Run a single test by name
python -m pytest tests/test_seed_agent.py::test_run_with_topic_uses_gdelt -v
```

Tests do not require any running services (database, Redis, or API keys) — all external calls are mocked.

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

```bash
# Start all services (PostgreSQL, Redis, API, frontend)
docker-compose up -d

# Stream backend logs
docker-compose logs -f api

# Stop everything
docker-compose down
```

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

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14.3 + FastAPI + Uvicorn |
| Agent pipeline | LangGraph StateGraph (7 agents) |
| NLP | spaCy (local NER), langdetect |
| DNA extraction | Featherless API (Mistral-7B) |
| Translation | Google Gemini Flash |
| Forecasting | Google Gemini Pro |
| Database | PostgreSQL + psycopg2 |
| Cache | Redis |
| Frontend | Next.js 14 + TypeScript + Tailwind |
| Visualization | D3.js v7 |
| Voice input | Speechmatics real-time WebSocket |
| Data sources | GDELT API, NewsAPI, 15 RSS feeds |
