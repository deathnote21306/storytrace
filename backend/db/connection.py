import json
import logging
import os
from pathlib import Path

import psycopg2
from psycopg2 import errors as pg_errors

logger = logging.getLogger(__name__)

_schema_ready = False


def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URL'])


def ensure_schema():
    """Run migrations.sql once at startup (idempotent for Render/Railway deploys)."""
    global _schema_ready
    if _schema_ready:
        return
    if not os.environ.get('DATABASE_URL'):
        logger.warning('DATABASE_URL not set — skipping schema migration')
        return

    migrations = Path(__file__).parent / 'migrations.sql'
    statements: list[str] = []
    buf: list[str] = []
    for line in migrations.read_text().splitlines():
        if line.strip().startswith('--') or not line.strip():
            continue
        buf.append(line)
        if line.rstrip().endswith(';'):
            statements.append('\n'.join(buf))
            buf = []

    with get_conn() as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            for stmt in statements:
                try:
                    cur.execute(stmt)
                except (pg_errors.DuplicateTable, pg_errors.DuplicateObject, pg_errors.DuplicateSchema):
                    conn.rollback()
                except Exception as exc:
                    conn.rollback()
                    logger.warning('Migration statement skipped: %s', exc)

    _schema_ready = True
    logger.info('Database schema ready')


def save_story(job_id: str, topic: str | None, url: str | None):
    logger.debug('[%s] Inserting story into DB (topic=%s)', job_id, topic)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO stories (id, topic, input_url, status) VALUES (%s, %s, %s, 'processing')",
                (job_id, topic, url)
            )


def update_story(job_id: str, result: dict, status: str):
    logger.info('[%s] Updating story: status=%s, outlets=%d',
                job_id, status, len(result.get('scored_list', [])))
    with get_conn() as conn:
        with conn.cursor() as cur:
            root = result.get('root', {})
            cur.execute(
                """UPDATE stories
                   SET status=%s, root_outlet=%s, root_url=%s,
                       root_headline=%s, root_text=%s, root_dna=%s, tree=%s
                   WHERE id=%s""",
                (
                    status,
                    root.get('outlet'),
                    root.get('url'),
                    root.get('headline'),
                    root.get('text'),
                    json.dumps(root.get('dna', {})),
                    json.dumps(result.get('tree')) if result.get('tree') is not None else None,
                    job_id,
                )
            )
            for art in result.get('scored_list', []):
                cur.execute(
                    """INSERT INTO outlet_versions
                         (story_id, outlet, country, url, headline, article_text,
                          dna, drift_score, parent_outlet, language)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        job_id,
                        art['outlet'],
                        art.get('country', 'Unknown'),
                        art.get('url'),
                        art.get('headline'),
                        art.get('text'),
                        json.dumps(art.get('dna', {})),
                        art.get('drift_score', 0),
                        art.get('parent_outlet', 'root'),
                        art.get('language', 'en'),
                    )
                )


def get_story(job_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM stories WHERE id=%s", (job_id,))
            story_row = cur.fetchone()
            if not story_row:
                return None
            cur.execute(
                "SELECT * FROM outlet_versions WHERE story_id=%s ORDER BY drift_score",
                (job_id,)
            )
            version_rows = cur.fetchall()
            return build_story_response(story_row, version_rows)


def build_story_response(story_row, version_rows) -> dict:
    # story_row columns: id(0), topic(1), input_url(2), root_outlet(3), root_url(4),
    #                    root_headline(5), root_text(6), root_dna(7), status(8),
    #                    created_at(9), tree(10)
    scored_list = [
        {
            'outlet':        row[2],
            'country':       row[3],
            'url':           row[4],
            'headline':      row[5],
            'text':          row[6],
            'dna':           row[7] or {},
            'drift_score':   row[8],
            'parent_outlet': row[9] or 'root',
            'language':      row[10] or 'en',
        }
        for row in version_rows
        # outlet_versions columns: id, story_id, outlet, country, url, headline,
        #                          article_text, dna, drift_score, parent_outlet, language, crawled_at
    ]
    return {
        'job_id': str(story_row[0]),
        'status': story_row[8],
        'root': {
            'outlet':   story_row[3],
            'url':      story_row[4],
            'headline': story_row[5],
            'dna':      story_row[7] or {},
        },
        'scored_list': scored_list,
        'tree': story_row[10],  # JSONB column; psycopg2 returns it as a dict automatically
    }


def get_recent() -> list:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, topic, root_headline, root_outlet, status, created_at, input_url
                   FROM stories
                   WHERE status='complete'
                   ORDER BY created_at DESC
                   LIMIT 10"""
            )
            rows = cur.fetchall()
            return [
                {
                    'job_id':    str(r[0]),
                    'topic':     r[1],
                    'headline':  r[2] or r[1] or r[6] or 'Untitled story',
                    'outlet':    r[3],
                    'created_at': str(r[5]),
                }
                for r in rows
            ]
