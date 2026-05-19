from dotenv import load_dotenv
load_dotenv()

import logging
import os
import uuid
import asyncio
import json as json_lib

import redis
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from backend.models import AnalyzeRequest, AnalyzeResponse, StoryResponse
from backend.db.connection import save_story, update_story, get_story, get_recent
from backend.orchestrator import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(name)s — %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S',
)
logger = logging.getLogger(__name__)

app = FastAPI(title="StoryTrace API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))


@app.post("/analyze", status_code=202, response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    user_input = req.url or req.topic  # single string passed to the pipeline

    logger.info('[%s] Job submitted — input: "%s"', job_id, user_input[:120] if user_input else '')
    save_story(job_id, req.topic, req.url)  # store url and topic in their own columns
    background_tasks.add_task(run_and_save, job_id, user_input)

    return {
        "job_id":   job_id,
        "status":   "processing",
        "poll_url": f"/story/{job_id}",
    }


async def run_and_save(job_id: str, user_input: str):
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(None, run_pipeline, job_id, user_input)
        update_story(job_id, result, status='complete')
        logger.info('[%s] Saved to DB — status=complete', job_id)
    except Exception as exc:
        logger.error('[%s] Pipeline raised an unhandled exception: %s', job_id, exc)
        update_story(job_id, {}, status='failed')


@app.get("/story/recent")
async def get_recent_stories():
    return get_recent()


@app.get("/story/{job_id}", response_model=StoryResponse)
async def get_story_result(job_id: str):
    try:
        cached = r.get(f"story:{job_id}")
        if cached:
            logger.debug('[%s] Redis cache hit', job_id)
            return json_lib.loads(cached)
    except Exception as exc:
        logger.warning('[%s] Redis unavailable, falling back to DB: %s', job_id, exc)

    story = get_story(job_id)
    if not story:
        logger.warning('[%s] Story not found in DB', job_id)
        return {"error": "Story not found"}

    if story['status'] == 'complete':
        try:
            r.setex(f"story:{job_id}", 3600, json_lib.dumps(story))
            logger.debug('[%s] Result cached in Redis', job_id)
        except Exception:
            pass  # Redis unavailable — still return the result from DB

    return story


@app.post("/forecast/{job_id}")
async def forecast(job_id: str):
    try:
        from agents.forecast_agent import run as run_forecast
    except ImportError:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=501, content={"error": "Forecast agent not yet implemented"})
    story = get_story(job_id)
    if not story or story['status'] != 'complete':
        return {"error": "Story not complete yet"}
    return run_forecast(story)


@app.get("/health")
async def health():
    return {"status": "ok"}
