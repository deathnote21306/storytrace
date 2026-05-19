-- Required for gen_random_uuid() used as default primary key generator
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- One row per pipeline run. Created when POST /analyze is received;
-- updated to 'complete' or 'failed' when the pipeline finishes.
CREATE TABLE stories (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- job_id returned to the client
  topic         TEXT,           -- free-text topic or article URL submitted by the user
  input_url     TEXT,           -- populated when the user submits a URL instead of a topic
  root_outlet   TEXT,           -- name of the outlet that published the original wire story
  root_url      TEXT,           -- URL of the root/original article found by seed_agent
  root_headline TEXT,           -- headline of the root article (used in the diff panel)
  root_text     TEXT,           -- first 300 words of the root article sent to the LLM
  root_dna      JSONB,          -- structured DNA of the root story: facts, tone, framing
  status        TEXT DEFAULT 'processing', -- 'processing' | 'complete' | 'failed'
  created_at    TIMESTAMP DEFAULT NOW(),   -- when the job was first submitted
  tree          JSONB           -- full D3-ready nested tree JSON produced by geo_builder; NULL until pipeline completes
);

-- One row per outlet version found by the crawler for a given story.
-- Populated by update_story() after the full pipeline completes.
CREATE TABLE outlet_versions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- internal row id
  story_id      UUID REFERENCES stories(id) ON DELETE CASCADE, -- links back to the parent story
  outlet        TEXT NOT NULL,    -- outlet name, e.g. "BBC", "RT" (matches OUTLET_COUNTRY map)
  country       TEXT NOT NULL,    -- country of the outlet, set by geo_builder before DB write
  url           TEXT,             -- direct URL to the outlet's article
  headline      TEXT,             -- outlet's headline (may differ significantly from root)
  article_text  TEXT,             -- first 300 words used for DNA extraction and drift scoring
  dna           JSONB,            -- extracted DNA: facts_kept, facts_dropped, tone, framing, political_lean
  drift_score   INTEGER CHECK (drift_score BETWEEN 0 AND 100), -- 0 = identical to root, 100 = max drift
  parent_outlet TEXT,             -- outlet with the closest drift score (used to build the mutation chain)
  language      TEXT DEFAULT 'en', -- ISO 639-1 language code detected by langdetect; 'en' if untranslated
  crawled_at    TIMESTAMP DEFAULT NOW() -- when this version was fetched by the crawler
);

-- Speed up lookups when fetching all versions for a story (used by get_story)
CREATE INDEX idx_outlet_story   ON outlet_versions(story_id);
-- Speed up geo_builder grouping and the /explore country filter
CREATE INDEX idx_outlet_country ON outlet_versions(country);
-- Speed up sorting by drift score in get_story and the DriftTree render order
CREATE INDEX idx_outlet_drift   ON outlet_versions(drift_score);
