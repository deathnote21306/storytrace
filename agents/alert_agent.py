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
    scored_list = state.get('scored_list', [])
    job_id = state.get('job_id', '?')

    logging.info('[%s] alert_agent started — checking %d article(s) (threshold=%d)',
                 job_id, len(scored_list), THRESHOLD)

    drift_detected = []
    alerts_fired = []
    for art in scored_list:
        if art['drift_score'] >= THRESHOLD:
            drift_detected.append(art['outlet'])
            logging.info('[%s] HIGH DRIFT: %s scored %d/100 — "%s"',
                         job_id, art['outlet'], art['drift_score'], art.get('headline', '')[:70])
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
                logging.info('[%s] Webhook alert sent for %s', job_id, art['outlet'])
            else:
                logging.debug('[%s] No webhook configured, alert skipped for %s', job_id, art['outlet'])

    logging.info('[%s] alert_agent done — %d high-drift outlet(s), %d webhook(s) fired',
                 job_id, len(drift_detected), len(alerts_fired))

    state['drift_detected'] = drift_detected
    state['alerts_fired'] = alerts_fired
    return state
