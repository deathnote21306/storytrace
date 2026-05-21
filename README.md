# StoryTrace

**StoryTrace** is a web application for tracking how a news story changes as it moves across outlets, countries, and media ecosystems.

Live demo: [https://storytrace-web.onrender.com/](https://storytrace-web.onrender.com/)

## What It Does

StoryTrace works like **Git for news**. A user can enter a news topic or article URL, and the app traces how that story evolves across different sources.

The platform is designed to help users understand:

- where a story may have started;
- which outlets are reporting on the same narrative;
- how facts, framing, or emphasis shift between versions;
- how much each version appears to drift from the original story;
- how the narrative spreads visually across a tree or map-style interface.

## What It Is For

StoryTrace is useful for journalists, researchers, analysts, students, and readers who want to compare coverage instead of reading one article in isolation.

The goal is not just to summarize the news. The goal is to make narrative change visible: what was added, what was removed, what was reframed, and how different outlets shape the same event over time.

## Core Features

- Submit a news URL or topic to start a trace.
- Run an AI-assisted backend pipeline that searches, compares, translates, and scores related stories.
- Visualize story drift through an interactive dashboard.
- Compare versions through narrative difference panels.
- Explore country and outlet-level views of a story.
- Use voice input for topic submission.
- Store analyzed stories and retrieve recent traces.

## Technology Stack

### Frontend

- **Next.js**
- **React**
- **TypeScript**
- **Tailwind CSS**
- **D3.js**
- **react-globe.gl**

### Backend

- **Python**
- **FastAPI**
- **Uvicorn**
- **LangGraph**
- **Pydantic**
- **PostgreSQL**
- **psycopg2**

### AI, NLP, And Data

- **spaCy** for local NLP and named entity recognition
- **langdetect** for language detection
- **Google Gemini** for translation and forecasting flows
- **OpenAI-compatible APIs** for agent workflows
- **RSS feeds, GDELT, and NewsAPI-style sources** for news discovery

### Deployment

- **Docker**
- **Docker Compose**
- **Render**
- **Nginx deployment configuration**

## Project Structure

```text
storytrace/
├── agents/              # Specialized AI/NLP pipeline agents
├── backend/             # FastAPI API, orchestration, database access
├── deploy/              # Deployment notes and server config
├── frontend/            # Next.js web application
├── tests/               # Backend and agent tests
├── docker-compose.yml   # Local multi-service setup
├── render.yaml          # Render backend deployment config
└── render.frontend.yaml # Render frontend deployment config
```

## How It Works

1. The user submits a topic or article URL from the web interface.
2. The frontend sends the request to the FastAPI backend.
3. The backend starts a background analysis job.
4. A LangGraph-based pipeline coordinates multiple agents.
5. The agents gather related articles, extract narrative details, translate where needed, and calculate drift scores.
6. Results are saved to PostgreSQL.
7. The frontend displays the story trace, visualizations, and comparison panels.

## Local Development

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend health check is available at:

[http://localhost:8000/health](http://localhost:8000/health)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs locally at:

[http://localhost:3000](http://localhost:3000)

## Environment Variables

The project expects environment variables for the API, database, and external AI/news services.

Common variables include:

- `DATABASE_URL`
- `NEXT_PUBLIC_API_URL`
- `CORS_ORIGINS`
- `NEWSAPI_KEY`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY` or compatible provider keys
- `SPEECHMATICS_KEY`
- `WEBHOOK_URL`

Do not expose private API keys in frontend `NEXT_PUBLIC_` variables unless they are explicitly safe for browser use.

## Testing

Backend tests are located in `tests/`.

```bash
pytest
```

Frontend build verification:

```bash
cd frontend
npm run build
```

## Demo

Try the live version here:

[https://storytrace-web.onrender.com/](https://storytrace-web.onrender.com/)
