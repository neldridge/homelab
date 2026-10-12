#!/usr/bin/python3
"""Read-only wanted observer; bounded requests, private persistent item state."""
import datetime
import json
import time
import urllib.request
from pathlib import Path
from service_checks import ROOT, atomic

LIMIT = 10000
THRESHOLD = 10 * 3600

def request(url, headers):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=5) as response:
        body = response.read(32 * 1024 * 1024 + 1)
    if len(body) > 32 * 1024 * 1024:
        raise ValueError('API snapshot exceeds 32 MiB')
    return json.loads(body)

def timestamp(value):
    if not value:
        return None
    return datetime.datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=datetime.timezone.utc).timestamp()

def eligible(service, item, now):
    if not item.get('monitored') or item.get('hasFile'):
        return False
    if service == 'radarr':
        # isAvailable alone may mean announced/in cinemas. Require home release evidence.
        dates = [timestamp(item.get(k)) for k in ('digitalRelease', 'physicalRelease')]
        return item.get('isAvailable') is True and any(d is not None and d <= now for d in dates)
    aired = timestamp(item.get('airDateUtc'))
    return item.get('series', {}).get('monitored') is True and aired is not None and aired <= now

def paged(base, endpoint, headers):
    records = []
    for page in range(1, 11):
        data = request(base + endpoint + f'?page={page}&pageSize=1000&includeSeries=true', headers)
        assert isinstance(data['records'], list) and data['totalRecords'] <= LIMIT
        records.extend(data['records'])
        if len(records) >= data['totalRecords']:
            return records
    raise ValueError('Incomplete wanted/queue snapshot')

def observe(service, items, queue, old, now):
    key = 'movieId' if service == 'radarr' else 'episodeId'
    queued = {x[key] for x in queue if key in x}
    current = {}
    for item in items:
        if item['id'] in queued or not eligible(service, item, now):
            continue
        ident = str(item['id'])
        # A long observer outage cannot prove continuous eligibility.
        prior = old.get(ident, {})
        since = prior.get('since', now) if now - prior.get('seen', 0) <= 900 else now
        current[ident] = {'since': since, 'seen': now}
    ages = [max(0, now - x['since']) for x in current.values()]
    return current, sum(age >= THRESHOLD for age in ages), max(ages, default=0)

def run():
    keys = json.loads((ROOT / 'app-keys.json').read_text())
    lines = []
    for service, port in [('sonarr', 8989), ('radarr', 7878)]:
        labels = f'host="bb9b",service="{service}"'
        def metric(name, value):
            lines.append(f'homelab_wanted_{name}{{{labels}}} {value}')
        try:
            base = f'http://127.0.0.1:{port}/api/v3/'
            headers = {'X-Api-Key': keys[service]}
            if service == 'radarr':
                items = request(base + 'movie', headers)
                assert isinstance(items, list) and len(items) <= LIMIT
            else:
                items = paged(base, 'wanted/missing', headers)
            queue = paged(base, 'queue', headers)
            statepath = ROOT / (service + '-wanted-state.json')
            old = json.loads(statepath.read_text()) if statepath.exists() else {}
            current, overdue, age = observe(service, items, queue, old, time.time())
            atomic(statepath, json.dumps(current))
            statepath.chmod(0o600)
            metric('overdue', overdue)
            metric('eligible', len(current))
            metric('oldest_seconds', age)
            metric('ok', 1)
        except Exception:
            # Never turn partial/failed collection into a healthy zero backlog.
            metric('ok', 0)
        metric('timestamp', time.time())
    atomic(ROOT / 'textfile/wanted.prom', '\n'.join(lines) + '\n')

if __name__ == '__main__':
    run()
