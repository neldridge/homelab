#!/usr/bin/python3
"""Read-only daily inventory/release observer. No pulls, execs, or app mutations."""
import base64
import configparser
import json
import sys
import fcntl
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from service_checks import ROOT, CONFIG, atomic, request

LIMIT = 2 * 1024 * 1024
REQUESTS = 0
MAX_REQUESTS = 480
ACCEPT = ', '.join(['application/vnd.oci.image.index.v1+json','application/vnd.docker.distribution.manifest.list.v2+json','application/vnd.oci.image.manifest.v1+json','application/vnd.docker.distribution.manifest.v2+json'])
RELEASES = {'seerr':'seerr-team/seerr','grafana':'grafana/grafana','alloy':'grafana/alloy','loki':'grafana/loki','prometheus':'prometheus/prometheus','blackbox':'prometheus/blackbox_exporter','snmp':'prometheus/snmp_exporter','exportarr':'onedr0p/exportarr'}

def fetch(url, headers=None):
    global REQUESTS
    for attempt in range(3):
        REQUESTS += 1
        if REQUESTS > MAX_REQUESTS: raise ValueError("request budget exhausted")
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'homelab-maintenance/1', **(headers or {})}), timeout=8) as r:
                raw = r.read(LIMIT + 1)
                if len(raw) > LIMIT: raise ValueError('response bound')
                return json.loads(raw), r.headers
        except urllib.error.HTTPError as exc:
            # Authentication challenges are handled by registry(), not retried here.
            if exc.code not in (408, 429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2: raise
        time.sleep((1, 3)[attempt])

def failure_streak(row, previous):
    if not row.get('lookup_error'):
        return 0
    return previous.get(row['service'], {}).get('lookup_failures', 0) + 1

def error_details(exc):
    result = {'lookup_error': type(exc).__name__}
    if isinstance(exc, urllib.error.HTTPError): result['lookup_http_status'] = exc.code
    # Do not record response bodies, credentials, or URLs.
    return result

def version(value):
    """Only stable numeric versions; LSIO rebuild number is compared separately."""
    m = re.fullmatch(r'v?(\d+(?:\.\d+)+)(?:-ls(\d+)|-alpine)?', value)
    if not m: return None
    return tuple(map(int,m[1].split('.'))), int(m[2] or 0)

def update_level(row):
    """Classify stable releases; unknown identity alone cannot justify an alert."""
    if row.get('lookup_error') or row['status'] in ('current', 'installed-ahead', 'unknown', 'channel-review'):
        return 'none'
    # Numeric image pins describe the installed release even if its API is down.
    installed = version(row['installed_tag']) or version(row['installed_version'])
    available = version(row['available_tag'])
    # Plex appends a build hash to its four-component application version.
    if row['service'] == 'plex':
        installed = version(row['installed_version'].split('-')[0])
        available = version(row['available_tag'].split('-')[0])
    if not installed or not available:
        return 'unknown'
    old, new = installed[0], available[0]
    if new[0] != old[0]:
        return 'major' if new[0] > old[0] else 'none'
    if new[1] != old[1]:
        return 'minor' if new[1] > old[1] else 'none'
    if new > old:
        return 'patch'
    return 'rebuild' if new == old else 'none'

def candidate(tags, lsio=False, nginx=False):
    allowed = []
    for tag in tags:
        v = version(tag)
        if not v: continue
        if lsio and not re.fullmatch(r'v?\d+(?:\.\d+)+-ls\d+',tag): continue
        if nginx and (not tag.endswith('-alpine') or v[0][1] % 2): continue
        allowed.append(tag)
    if not allowed: raise ValueError('stable tag not in bounded window')
    return max(allowed,key=version)

def discover(repo, lsio=False, nginx=False):
    tags = []
    for page in (1,2):
        d,_ = fetch(f'https://hub.docker.com/v2/repositories/{repo}/tags?page_size=100&ordering=last_updated&page={page}')
        tags.extend(x['name'] for x in d['results'])
        if not d.get('next'): break
    try:
        return candidate(tags,lsio,nginx)
    except ValueError:
        if repo != 'linuxserver/kometa' or not lsio:
            raise
        # Frequent nightly builds can displace stable tags from both pages.
        release,_ = fetch('https://api.github.com/repos/Kometa-Team/Kometa/releases/latest')
        stable = release['tag_name']
        if release.get('prerelease') or release.get('draft') or not version(stable):
            raise ValueError('nonstable Kometa release')
        tags = []
        for page in (1,2):
            d,_ = fetch(f'https://hub.docker.com/v2/repositories/{repo}/tags?page_size=100&ordering=last_updated&page={page}&name={urllib.parse.quote(stable.lstrip("v"))}')
            tags.extend(x['name'] for x in d['results'] if version(x['name']) and version(x['name'])[0] == version(stable)[0])
            if not d.get('next'): break
        return candidate(tags,lsio=True)

def registry(repo, tag, arch, osname='linux'):
    """Compare config digests, not multiarch-index digests with image IDs."""
    parts=repo.split('/')
    host=parts.pop(0) if '.' in parts[0] else 'registry-1.docker.io'
    if host=='docker.io': host='registry-1.docker.io'
    path='/'.join(parts)
    if '/' not in path: path='library/'+path
    base=f'https://{host}/v2/{path}'
    headers={'Accept':ACCEPT}
    def get(kind, ref):
        url=f'{base}/{kind}/{ref}'
        try: return fetch(url,headers)
        except urllib.error.HTTPError as e:
            if e.code != 401 or 'Authorization' in headers: raise
            challenge=dict(re.findall(r'(\w+)="([^"]+)"',e.headers['WWW-Authenticate']))
            realm=challenge.pop('realm')
            if not realm.startswith('https://'): raise ValueError('insecure token endpoint')
            token,_=fetch(realm+'?'+urllib.parse.urlencode(challenge))
            headers['Authorization']='Bearer '+(token.get('token') or token['access_token'])
            return fetch(url,headers)
    manifest,h=get('manifests',tag)
    index=h.get('Docker-Content-Digest','')
    if 'manifests' in manifest:
        matches=[m for m in manifest['manifests'] if m.get('platform',{}).get('architecture')==arch and m['platform'].get('os')==osname]
        if len(matches)!=1: raise ValueError('architecture unavailable/ambiguous')
        manifest,h=get('manifests',matches[0]['digest'])
    config_digest=manifest['config']['digest']
    config,_=get('blobs',config_digest)
    if config.get('architecture')!=arch or config.get('os')!=osname: raise ValueError('architecture mismatch')
    return {'available_tag':tag,'available_digest':index,'available_config':config_digest}

def app_version(s):
    keys=json.loads((ROOT/'app-keys.json').read_text())
    h={'X-Api-Key':keys.get(s,'')}
    if s in ('sonarr','radarr','prowlarr'):
        port={'sonarr':8989,'radarr':7878,'prowlarr':9696}[s]
        return request(f'http://127.0.0.1:{port}/api/v{1 if s=="prowlarr" else 3}/system/status',h)['version'],'api'
    if s=='bazarr': return request('http://127.0.0.1:6767/api/system/status',h)['data']['bazarr_version'],'api'
    if s=='seerr': return request('http://127.0.0.1:5055/api/v1/status',h)['version'],'api'
    if s=='tautulli': return request('http://127.0.0.1:8181/api/v2?'+urllib.parse.urlencode({'apikey':keys[s],'cmd':'get_tautulli_info'}))['response']['data']['tautulli_version'],'api'
    if s=='nzbget':
        n=dict(l.strip().split('=',1) for l in (CONFIG/'nzbget/nzbget.conf').read_text().splitlines() if '=' in l and not l.startswith('#'))
        h={'Authorization':'Basic '+base64.b64encode((n['ControlUsername']+':'+n['ControlPassword']).encode()).decode(),'Content-Type':'application/json'}
        return request('http://127.0.0.1:6790/jsonrpc',h,b'{"method":"version","params":[],"id":1}')['result'],'api'
    if s=='kometa':
        p=CONFIG/'plexmetamanager/logs/meta.log'
        with p.open('rb') as f: text=f.read(65536).decode(errors='replace')
        m=re.search(r'Version:\s*(\d+\.\d+\.\d+)',text)
        if not m: raise ValueError('no logged version')
        return m[1],'run-log'
    if s=='nginx':
        with urllib.request.urlopen('https://overseerr.a3f.link/api/v1/status',timeout=5) as r:
            m=re.fullmatch(r'nginx/(\d+(?:\.\d+)+)',r.headers.get('Server',''))
            if not m: raise ValueError('server version unavailable')
            return m[1], 'http-server-header'
    raise ValueError('no app endpoint')

def run():
    global REQUESTS
    REQUESTS = 0
    now=time.time(); lines=[]; rows=[]; cache={}
    saved = ROOT/'versions.json'
    previous = {r['service']: r for r in json.loads(saved.read_text())['rows']} if saved.exists() else {}
    def metric(name,value,**labels):
        labels={'host':'bb9b',**labels}
        labels={k:str(v)[:512] for k,v in labels.items()}
        lines.append('homelab_version_'+name+'{'+','.join(k+'='+json.dumps(str(v)) for k,v in labels.items())+'} '+str(value))
    ids=subprocess.check_output(['docker','ps','-q'],timeout=5).decode().split()[:32]
    containers=json.loads(subprocess.check_output(['docker','inspect',*ids],timeout=8)) if ids else []
    for c in containers[:32]:
        labels=c['Config'].get('Labels') or {}; project=labels.get('com.docker.compose.project')
        if project not in ('homelab','homelab-monitoring'): continue
        svc=labels['com.docker.compose.service']; service=('monitoring-' if project=='homelab-monitoring' else '')+svc
        image=c['Config']['Image']; ref=image.split('@')[0]; repo,tag=ref.rsplit(':',1) if ':' in ref.split('/')[-1] else (ref,'latest')
        local=json.loads(subprocess.check_output(['docker','image','inspect',c['Image']],timeout=5))[0]
        row={'service':service,'image':repo,'installed_tag':tag,'image_id':c['Image'],'running_digest':';'.join(local.get('RepoDigests',[])[:2]),'architecture':local['Architecture'],'channel':'stable','installed_channel':'stable' if version(tag) else ('mutable stable' if tag in ('latest','stable') else 'unverified'),'installed_version':'unknown','version_source':'unavailable','available_tag':'unknown','available_digest':'','status':'unknown'}
        try:
            if project=='homelab':
                row['installed_version'],row['version_source']=app_version(svc)
            else:
                if svc.startswith('exportarr-'):
                    row['installed_version']=local['Config']['Labels']['org.opencontainers.image.version']
                    row['version_source']='image-label'
                elif svc=='grafana':
                    row['installed_version']=request('https://grafana.a3f.link:3000/api/health')['version']
                    row['version_source']='api'
                else:
                    port,build={'alloy':(12345,'alloy_build_info'),'loki':(3100,'loki_build_info'),'prometheus':(9090,'prometheus_build_info'),'blackbox':(9115,'blackbox_exporter_build_info'),'snmp':(9116,'snmp_exporter_build_info')}[svc]
                    ip=next(iter(c['NetworkSettings']['Networks'].values()))['IPAddress']
                    with urllib.request.urlopen(f'http://{ip}:{port}/metrics',timeout=5) as r:
                        text=r.read(LIMIT).decode()
                    m=re.search(r'^'+build+r'\{[^\n]*\bversion="([^"]+)"',text,re.M)
                    if not m: raise ValueError('no build metric')
                    row['installed_version']=m[1];row['version_source']='build-metric'

        except Exception: pass
        metric('application_known',int(row['installed_version'] not in ('unknown','')),service=service)
        try:
            lsio='linuxserver/' in repo
            if lsio:
                hub='linuxserver/'+svc; channel='stable (LSIO numeric tags)'
                chosen=discover(hub,lsio=True)
            elif svc=='nginx':
                channel='stable even minor / alpine'; chosen=discover('library/nginx',nginx=True)
            else:
                key='exportarr' if svc.startswith('exportarr-') else svc
                channel='stable GitHub release'
                release,_=fetch('https://api.github.com/repos/'+RELEASES[key]+'/releases/latest') if key not in cache else (cache[key],{})
                cache[key]=release
                if release.get('prerelease') or release.get('draft') or not version(release['tag_name']): raise ValueError('nonstable release')
                chosen=release['tag_name']
                if key in ('grafana','loki'): chosen=chosen.lstrip('v')
            row['channel']=channel
            ck=(repo,chosen,row['architecture'])
            if ck not in cache: cache[ck]=registry(repo,chosen,row['architecture'])
            row.update(cache[ck])
            installed=version(tag); available=version(chosen)
            # Mutable tags are resolved by config identity; numeric downgrade is never an update.
            if c['Image']==row['available_config']: row['status']='current'
            elif installed and available and available < installed: row['status']='installed-ahead'
            elif installed and available and available > installed: row['status']='image-rebuild' if available[0]==installed[0] else 'update'
            elif installed and available and available == installed: row['status']='image-rebuild'
            elif tag in ('latest','stable'): row['status']='mutable-tag-changed'
            else: row['status']='channel-review'
            metric('lookup_ok',1,service=service)
        except Exception as e:
            row.update(error_details(e));metric('lookup_ok',0,service=service)
        rows.append(row)
    # Plex is a separate server, not an R710 container. Public stable channel only.
    row={'service':'plex','image':'external PMS','installed_tag':'n/a','image_id':'n/a','running_digest':'n/a','architecture':'unknown','channel':'public stable','installed_channel':'unverified (public/beta)','installed_version':'unknown','version_source':'api','available_tag':'unknown','available_digest':'n/a','status':'unknown'}
    try:
        c=configparser.ConfigParser();c.read(CONFIG/'tautulli/config.ini')
        p=request('http://192.168.11.129:32400/',{'X-Plex-Token':c['PMS']['pms_token']},xml=True)
        row['installed_version']=p.attrib['version'];row['platform']=p.attrib.get('platform','unknown')
        d,_=fetch('https://plex.tv/api/downloads/5.json');public=d['computer'][row['platform']]
        row['available_tag']=public['version']
        def pv(v): return tuple(map(int,v.split('-')[0].split('.')))
        row['status']='update' if pv(public['version'])>pv(row['installed_version']) else ('current' if public['version']==row['installed_version'] else 'installed-ahead')
        metric('lookup_ok',1,service='plex')
    except Exception as e: row.update(error_details(e));metric('lookup_ok',0,service='plex')
    metric('application_known',int(row['installed_version']!='unknown'),service='plex');rows.append(row)
    for row in rows:
        row['update_level'] = update_level(row)
        row['lookup_failures'] = failure_streak(row, previous)
        metric('lookup_failures', row['lookup_failures'], service=row['service'])
        metric('info',1,**{k:row[k] for k in ('service','image','installed_tag','running_digest','image_id','architecture','channel','installed_channel','installed_version','version_source','available_tag','available_digest','status')})
        metric('major_minor_update_available',int(row['update_level'] in ('major','minor')),service=row['service'])
        metric('update_available',int(row['status'] in ('update','image-rebuild','mutable-tag-changed')),service=row['service'])
    metric('checked_timestamp',now)
    atomic(ROOT/'versions.json',json.dumps({'checked':now,'rows':rows},indent=2));(ROOT/'versions.json').chmod(0o600)
    atomic(ROOT/'textfile/versions.prom','\n'.join(lines)+'\n')
    print(json.dumps({'services':len(rows),'statuses':{s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},'requests':REQUESTS,'unknown_applications':[r['service'] for r in rows if r['installed_version']=='unknown']}))

def main():
    # Daily and recovery timers can overlap; serialize without queuing duplicate runs.
    with (ROOT/'versions.lock').open('w') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return
        if '--retry-failed' in sys.argv:
            saved = ROOT/'versions.json'
            if not saved.exists(): return
            state = json.loads(saved.read_text())
            if not any(r.get('lookup_error') for r in state['rows']): return
            if time.time() - state['checked'] < 14 * 60: return
        run()

if __name__=='__main__': main()
