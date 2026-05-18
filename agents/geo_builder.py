OUTLET_COUNTRY = {
    'BBC':            'UK',
    'Guardian':       'UK',
    'Reuters':        'US',
    'CNN':            'US',
    'Fox News':       'US',
    'Al Jazeera':     'Qatar',
    'Arab News':      'Saudi Arabia',
    'Dawn':           'Pakistan',
    'RT':             'Russia',
    'Sputnik':        'Russia',
    'TASS':           'Russia',
    'DW':             'Germany',
    'France24':       'France',
    'NDTV':           'India',
    'Times of India': 'India',
    'NHK':            'Japan',
}


def run(state: dict) -> dict:
    root = state.get('root', {})

    # write country back into each scored article so DB has real country names
    for art in state.get('scored_list', []):
        art['country'] = OUTLET_COUNTRY.get(art['outlet'], 'Other')

    tree = {
        'id':          'root',
        'outlet':      root.get('outlet', 'Wire'),
        'country':     'US',
        'headline':    root.get('headline', ''),
        'drift_score': 0,
        'parent_id':   None,
        'type':        'root',
        'children':    [],
    }

    by_country: dict[str, list] = {}
    for art in state.get('scored_list', []):
        country = art['country']
        by_country.setdefault(country, []).append({
            'id':          f"node-{art['outlet'].replace(' ', '-')}",
            'outlet':      art['outlet'],
            'country':     country,
            'headline':    art.get('headline', ''),
            'url':         art.get('url', ''),
            'drift_score': art['drift_score'],
            'parent_id':   art.get('parent_outlet', 'root'),
            'dna':         art.get('dna', {}),
            'type':        'outlet',
            'children':    [],
        })

    for country, nodes in by_country.items():
        avg_drift = round(sum(n['drift_score'] for n in nodes) / len(nodes))
        tree['children'].append({
            'id':          f'branch-{country}',
            'country':     country,
            'type':        'country_branch',
            'drift_score': avg_drift,
            'children':    nodes,
        })

    tree['children'].sort(key=lambda b: b['drift_score'])

    state['tree'] = tree
    return state
