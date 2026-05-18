TONE_MAP = {
    'neutral':    0,
    'supportive': 20,
    'dismissive': 35,
    'alarming':   50,
    'unknown':    0,
}

_STOP = {
    'the', 'a', 'an', 'is', 'in', 'on', 'at', 'to', 'of', 'and', 'or',
    'for', 'that', 'this', 'was', 'were', 'are', 'be', 'been', 'has',
    'have', 'had', 'by', 'with', 'as', 'it', 'its', 'he', 'she', 'they',
    'we', 'who', 'which', 'but', 'if', 'from', 'about', 'after', 'also',
    'said', 'says', 'say', 'new', 'one', 'two', 'not', 'no', 'their',
}


def _keywords(text: str) -> set:
    return set(text.lower().split()) - _STOP


def _fact_covered(root_fact: str, outlet_facts: list[str]) -> bool:
    """True if any outlet fact shares >=40% of root fact's keywords."""
    rw = _keywords(root_fact)
    if not rw:
        return False
    return any(len(rw & _keywords(of)) / len(rw) >= 0.4 for of in outlet_facts)


def compute_drift(root_dna: dict, outlet_dna: dict) -> int:
    root_facts   = root_dna.get('facts_kept', [])
    outlet_facts = outlet_dna.get('facts_kept', [])

    if root_facts:
        covered      = sum(1 for rf in root_facts if _fact_covered(rf, outlet_facts))
        dropped_ratio = (len(root_facts) - covered) / len(root_facts)
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
