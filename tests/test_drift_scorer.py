from agents.drift_scorer import compute_drift, find_parent_outlet, run


def _dna(facts_kept=None, tone='neutral'):
    return {'facts_kept': facts_kept or [], 'tone': tone}


def _article(outlet, dna):
    return {'outlet': outlet, 'url': f'https://{outlet}.com', 'headline': 'h',
            'text': 't', 'language': 'en', 'dna': dna}


# --- compute_drift ---

def test_identical_facts_neutral_tone_scores_zero():
    dna = _dna(['Iran deal', 'IAEA inspection'], 'neutral')
    assert compute_drift(dna, dna) == 0


def test_all_facts_dropped_alarming_tone_scores_100():
    root   = _dna(['fact A', 'fact B'], 'neutral')
    outlet = _dna([], 'alarming')
    assert compute_drift(root, outlet) == 100


def test_no_root_facts_scores_only_tone():
    root   = _dna([], 'neutral')
    outlet = _dna([], 'alarming')
    assert compute_drift(root, outlet) == 40  # tone capped at 40


def test_half_facts_dropped_neutral_tone():
    root   = _dna(['fact A', 'fact B'], 'neutral')
    outlet = _dna(['fact A'], 'neutral')
    assert compute_drift(root, outlet) == 30  # 0.5 * 60 = 30


def test_drift_capped_at_100():
    root   = _dna(['a', 'b', 'c', 'd'], 'neutral')
    outlet = _dna([], 'alarming')
    assert compute_drift(root, outlet) == 100


def test_fact_comparison_is_case_insensitive():
    root   = _dna(['Iran Deal'], 'neutral')
    outlet = _dna(['iran deal'], 'neutral')
    assert compute_drift(root, outlet) == 0


def test_empty_dicts_score_zero():
    assert compute_drift({}, {}) == 0


# --- find_parent_outlet ---

def test_first_article_parent_is_root():
    assert find_parent_outlet(0, []) == 'root'


def test_parent_is_lowest_drift_outlet():
    scored = [
        {'outlet': 'BBC', 'drift_score': 10},
        {'outlet': 'RT',  'drift_score': 80},
    ]
    assert find_parent_outlet(2, scored) == 'BBC'


# --- run ---

def test_run_sets_scored_list():
    state = {
        'root': {'dna': _dna(['fact A'], 'neutral')},
        'dna_list': [
            _article('BBC', _dna(['fact A'], 'neutral')),
            _article('RT',  _dna([], 'alarming')),
        ],
    }
    result = run(state)
    assert 'scored_list' in result
    assert len(result['scored_list']) == 2


def test_run_sorted_ascending_by_drift():
    state = {
        'root': {'dna': _dna(['fact A', 'fact B'], 'neutral')},
        'dna_list': [
            _article('RT',  _dna([], 'alarming')),
            _article('BBC', _dna(['fact A', 'fact B'], 'neutral')),
        ],
    }
    result = run(state)
    scores = [a['drift_score'] for a in result['scored_list']]
    assert scores == sorted(scores)


def test_run_each_article_has_drift_score_and_parent():
    state = {
        'root': {'dna': _dna(['fact A'], 'neutral')},
        'dna_list': [_article('BBC', _dna(['fact A'], 'neutral'))],
    }
    result = run(state)
    art = result['scored_list'][0]
    assert 'drift_score' in art
    assert 'parent_outlet' in art
    assert isinstance(art['drift_score'], int)


def test_run_with_empty_dna_list():
    state = {'root': {'dna': _dna(['fact A'], 'neutral')}, 'dna_list': []}
    result = run(state)
    assert result['scored_list'] == []


def test_run_preserves_article_fields():
    state = {
        'root': {'dna': _dna(['fact A'], 'neutral')},
        'dna_list': [_article('Guardian', _dna(['fact A'], 'neutral'))],
    }
    result = run(state)
    art = result['scored_list'][0]
    assert art['outlet'] == 'Guardian'
    assert art['url'] == 'https://Guardian.com'
