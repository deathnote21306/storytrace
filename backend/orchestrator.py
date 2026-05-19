import logging

from langgraph.graph import StateGraph, END
from agents import (
    seed_agent, crawler_agent, translator,
    dna_extractor, drift_scorer, geo_builder, alert_agent,
)

logger = logging.getLogger(__name__)

# Contract: the Translator mutates state['articles'] in-place (updates art['text'] and
# art['language'] on each dict directly). The DNA Extractor then reads the already-translated
# text from state['articles']. Do NOT have the Translator produce a new list under a
# different key — it must write back into the same list so dna_extractor sees the updates.


def _route_after_seed(state: dict) -> str:
    # seed_agent sets state['error'] on failure (GDELT timeout, no articles found, etc.).
    # Short-circuit to END so downstream agents never run on invalid state.
    return 'end' if state.get('error') else 'crawler'


def build_pipeline():
    g = StateGraph(dict)

    g.add_node('seed',       seed_agent.run)
    g.add_node('crawler',    crawler_agent.run)
    g.add_node('translator', translator.run)
    g.add_node('dna',        dna_extractor.run)
    g.add_node('scorer',     drift_scorer.run)
    g.add_node('geo',        geo_builder.run)
    g.add_node('alert',      alert_agent.run)

    g.set_entry_point('seed')
    g.add_conditional_edges('seed', _route_after_seed, {'crawler': 'crawler', 'end': END})
    g.add_edge('crawler',    'translator')  # translate before DNA extraction
    g.add_edge('translator', 'dna')
    g.add_edge('dna',        'scorer')
    g.add_edge('scorer',     'geo')
    g.add_edge('geo',        'alert')
    g.add_edge('alert',      END)

    return g.compile()


pipeline = build_pipeline()


def run_pipeline(job_id: str, user_input: str) -> dict:
    logger.info('[%s] Pipeline starting — input: "%s"', job_id, user_input[:120])
    initial_state = {
        'job_id': job_id,
        'input':  user_input,
    }
    result = pipeline.invoke(initial_state)
    if result.get('error'):
        logger.error('[%s] Pipeline completed with error: %s', job_id, result['error'])
    else:
        article_count = len(result.get('scored_list', []))
        logger.info('[%s] Pipeline complete — %d article(s) scored', job_id, article_count)
    return result
