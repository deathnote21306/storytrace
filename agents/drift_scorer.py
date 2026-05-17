TONE_MAP = {
    'neutral':    0,
    'supportive': 20,
    'dismissive': 35,
    'alarming':   50,
    'unknown':    0,
}


def compute_drift(root_dna: dict, outlet_dna: dict) -> int:
    root_facts   = set(f.lower() for f in root_dna.get('facts_kept', []))
    outlet_facts = set(f.lower() for f in outlet_dna.get('facts_kept', []))

    if root_facts:
        dropped_ratio = len(root_facts - outlet_facts) / len(root_facts)
    else:
        dropped_ratio = 0
    fact_score = dropped_ratio * 60

    root_tone   = TONE_MAP.get(root_dna.get('tone', 'neutral'), 0)
    outlet_tone = TONE_MAP.get(outlet_dna.get('tone', 'neutral'), 0)
    tone_score  = min(abs(outlet_tone - root_tone), 40)

    return min(round(fact_score + tone_score), 100)


def find_parent_outlet(index: int, scored_so_far: list) -> str:
    if not scored_so_far:
        return 'root'
    return min(scored_so_far, key=lambda x: x['drift_score'])['outlet']


def run(state: dict) -> dict:
    root_dna = state.get('root', {}).get('dna', {})
    scored = []

    for i, art in enumerate(state.get('dna_list', [])):
        score  = compute_drift(root_dna, art.get('dna', {}))
        parent = find_parent_outlet(i, scored)
        scored.append({**art, 'drift_score': score, 'parent_outlet': parent})

    state['scored_list'] = sorted(scored, key=lambda x: x['drift_score'])
    return state
