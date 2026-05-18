from agents.geo_builder import OUTLET_COUNTRY, run


def _article(outlet, drift_score, parent_outlet='root'):
    return {
        'outlet': outlet, 'drift_score': drift_score,
        'parent_outlet': parent_outlet,
        'headline': f'{outlet} headline', 'url': f'https://{outlet}.com',
        'text': 'text', 'language': 'en', 'dna': {},
    }


def _base_state(articles):
    return {
        'root': {'outlet': 'Reuters', 'headline': 'Root story', 'dna': {}},
        'scored_list': articles,
    }


# --- country mapping ---

def test_known_outlets_map_to_correct_country():
    assert OUTLET_COUNTRY['BBC'] == 'UK'
    assert OUTLET_COUNTRY['RT'] == 'Russia'
    assert OUTLET_COUNTRY['CNN'] == 'US'
    assert OUTLET_COUNTRY['NHK'] == 'Japan'


def test_unknown_outlet_maps_to_other():
    state = _base_state([_article('UnknownOutlet', 20)])
    run(state)
    assert state['scored_list'][0]['country'] == 'Other'


# --- country written back into scored_list ---

def test_run_sets_country_on_each_article():
    state = _base_state([
        _article('BBC', 10),
        _article('RT', 70),
    ])
    run(state)
    countries = {a['outlet']: a['country'] for a in state['scored_list']}
    assert countries['BBC'] == 'UK'
    assert countries['RT'] == 'Russia'


# --- tree structure ---

def test_run_produces_tree_with_root_node():
    state = _base_state([_article('BBC', 10)])
    result = run(state)
    assert result['tree']['id'] == 'root'
    assert result['tree']['type'] == 'root'
    assert result['tree']['drift_score'] == 0


def test_run_groups_by_country():
    state = _base_state([
        _article('BBC', 10),
        _article('Guardian', 20),
        _article('RT', 70),
    ])
    result = run(state)
    countries = {b['country'] for b in result['tree']['children']}
    assert 'UK' in countries
    assert 'Russia' in countries


def test_run_country_branch_avg_drift():
    state = _base_state([
        _article('BBC', 10),
        _article('Guardian', 30),
    ])
    result = run(state)
    uk_branch = next(b for b in result['tree']['children'] if b['country'] == 'UK')
    assert uk_branch['drift_score'] == 20  # (10+30)/2


def test_run_branches_sorted_ascending_by_drift():
    state = _base_state([
        _article('RT', 80),
        _article('BBC', 10),
        _article('DW', 40),
    ])
    result = run(state)
    scores = [b['drift_score'] for b in result['tree']['children']]
    assert scores == sorted(scores)


def test_run_outlet_node_shape():
    state = _base_state([_article('BBC', 15)])
    result = run(state)
    uk = next(b for b in result['tree']['children'] if b['country'] == 'UK')
    node = uk['children'][0]
    assert node['id'] == 'node-BBC'
    assert node['outlet'] == 'BBC'
    assert node['type'] == 'outlet'
    assert node['drift_score'] == 15
    assert 'dna' in node
    assert node['children'] == []


def test_run_with_empty_scored_list():
    state = _base_state([])
    result = run(state)
    assert result['tree']['children'] == []


def test_run_outlet_with_space_in_name():
    state = _base_state([_article('Fox News', 50)])
    result = run(state)
    us = next(b for b in result['tree']['children'] if b['country'] == 'US')
    assert us['children'][0]['id'] == 'node-Fox-News'
