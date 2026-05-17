import logging
import os
import requests

THRESHOLD = int(os.environ.get('ALERT_THRESHOLD', '70'))


def send_alert(payload: dict) -> bool:
    """POST payload to webhook. Returns True if webhook is configured (attempt was made)."""
    webhook = os.environ.get('WEBHOOK_URL', '')
    if not webhook:
        return False
    try:
        r = requests.post(webhook, json=payload, timeout=5)
        r.raise_for_status()
    except Exception as exc:
        logging.warning('Alert webhook failed for %s: %s', payload.get('outlet'), exc)
    return True


def run(state: dict) -> dict:
    drift_detected = []
    alerts_fired = []
    for art in state.get('scored_list', []):
        if art['drift_score'] >= THRESHOLD:
            drift_detected.append(art['outlet'])
            payload = {
                'job_id':      state.get('job_id'),
                'outlet':      art['outlet'],
                'country':     art.get('country', 'Unknown'),
                'drift_score': art['drift_score'],
                'headline':    art.get('headline', ''),
                'url':         art.get('url', ''),
                'alert':       f"DRIFT ALERT: {art['outlet']} scored {art['drift_score']}/100",
            }
            if send_alert(payload):
                alerts_fired.append(art['outlet'])

    state['drift_detected'] = drift_detected
    state['alerts_fired'] = alerts_fired
    return state
