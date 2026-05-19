from unittest.mock import patch
from backend.orchestrator import pipeline, run_pipeline


def _make_seed_ok(state: dict) -> dict:
    """Stub seed that succeeds — sets root and entities."""
    return {**state, 'root': {'outlet': 'Reuters', 'headline': 'Test'}, 'entities': ['Iran']}


def _make_seed_fail(state: dict) -> dict:
    """Stub seed that fails — sets error, leaves root absent."""
    return {**state, 'error': 'GDELT timeout: no articles found'}


# ---------------------------------------------------------------------------
# Test 1: happy-path node order
# ---------------------------------------------------------------------------

def test_pipeline_runs_all_nodes_in_order():
    """All 7 agents run in the correct sequence on a successful seed."""
    call_order = []

    def make_tracker(name):
        def agent(state):
            call_order.append(name)
            return state
        return agent

    with (
        patch('agents.seed_agent.run',    make_tracker('seed')),
        patch('agents.crawler_agent.run', make_tracker('crawler')),
        patch('agents.translator.run',    make_tracker('translator')),
        patch('agents.dna_extractor.run', make_tracker('dna')),
        patch('agents.drift_scorer.run',  make_tracker('scorer')),
        patch('agents.geo_builder.run',   make_tracker('geo')),
        patch('agents.alert_agent.run',   make_tracker('alert')),
    ):
        # Rebuild pipeline so it picks up the patched functions.
        from backend import orchestrator
        original = orchestrator.pipeline
        orchestrator.pipeline = orchestrator.build_pipeline()
        try:
            run_pipeline('job-001', 'Iran nuclear talks')
        finally:
            orchestrator.pipeline = original

    assert call_order == ['seed', 'crawler', 'translator', 'dna', 'scorer', 'geo', 'alert'], (
        f"Unexpected node order: {call_order}"
    )


# ---------------------------------------------------------------------------
# Test 2: seed failure short-circuits to END
# ---------------------------------------------------------------------------

def test_seed_error_short_circuits_pipeline():
    """When seed_agent sets state['error'], no downstream agent should run."""
    downstream_called = []

    def track(name):
        def agent(state):
            downstream_called.append(name)
            return state
        return agent

    with (
        patch('agents.seed_agent.run',    _make_seed_fail),
        patch('agents.crawler_agent.run', track('crawler')),
        patch('agents.translator.run',    track('translator')),
        patch('agents.dna_extractor.run', track('dna')),
        patch('agents.drift_scorer.run',  track('scorer')),
        patch('agents.geo_builder.run',   track('geo')),
        patch('agents.alert_agent.run',   track('alert')),
    ):
        from backend import orchestrator
        original = orchestrator.pipeline
        orchestrator.pipeline = orchestrator.build_pipeline()
        try:
            result = run_pipeline('job-002', 'Iran nuclear talks')
        finally:
            orchestrator.pipeline = original

    assert result.get('error') == 'GDELT timeout: no articles found', (
        "Expected error key in state after seed failure"
    )
    assert downstream_called == [], (
        f"Downstream agents ran despite seed failure: {downstream_called}"
    )
