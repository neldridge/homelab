#!/usr/bin/python3
"""Bounded semantic checks missing from standard exporters. No response bodies logged."""
import base64, concurrent.futures, configparser, datetime, glob, json, os, re, subprocess, time, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path('/opt/data/homelab/monitoring'); CONFIG=Path('/opt/data/homelab/config')
def request(url,headers=None,data=None,xml=False):
 r=urllib.request.urlopen(urllib.request.Request(url,headers=headers or {},data=data),timeout=5)
 body=r.read(4*1024*1024)
 return ET.fromstring(body) if xml else json.loads(body)
def atomic(path,body):
 p=Path(str(path)+'.tmp');p.write_text(body);p.chmod(0o644);p.replace(path)
def check(s):
 k=json.loads((ROOT/'app-keys.json').read_text()); out={}
 if (ROOT/('fault-'+s)).exists(): k[s]='monitoring-invalid-fixture'
 h={'X-Api-Key':k.get(s,'')}
 if s in ('sonarr','radarr','prowlarr'):
  p={'sonarr':8989,'radarr':7878,'prowlarr':9696}[s];v=1 if s=='prowlarr' else 3;b=f'http://127.0.0.1:{p}/api/v{v}/'
  assert request(b+'system/status',h)['appName'].lower()==s
  health=request(b+'health',h);assert isinstance(health,list);out['warnings']=len(health)
  if s!='prowlarr':
   q=request(b+'queue?page=1&pageSize=1000',h);assert 'records' in q
   out['queue_failures']=sum(x.get('trackedDownloadState') in ('importBlocked','importFailed','downloadFailed') or x.get('status')=='failed' for x in q['records'])
   statepath=ROOT/(s+'-queue-state.json')
   old=json.loads(statepath.read_text()) if statepath.exists() else {};current={};stuck=0
   for x in q['records']:
    if x.get('trackedDownloadState') in ('importPending','importing') or (x.get('status')=='completed' and x.get('trackedDownloadState')!='imported'):
     ident=str(x['id']);sig=str((x.get('trackedDownloadState'),x.get('sizeleft'),x.get('status')))
     prior=old.get(ident,{});since=prior.get('since',time.time()) if prior.get('sig')==sig else time.time()
     current[ident]={'sig':sig,'since':since};stuck+=int(time.time()-since>1800)
   atomic(statepath,json.dumps(current));statepath.chmod(0o600)
   out['queue_stuck']=stuck
 elif s=='bazarr':
  assert request('http://127.0.0.1:6767/api/system/status',h)['data']['bazarr_version'];d=request('http://127.0.0.1:6767/api/system/health',h);assert isinstance(d['data'],list);out['warnings']=len(d['data'])
 elif s=='seerr':
  d=request('http://127.0.0.1:5055/api/v1/request?take=1',h);assert 'pageInfo' in d and isinstance(d['results'],list)
 elif s=='tautulli':
  d=request('http://127.0.0.1:8181/api/v2?apikey='+k[s]+'&cmd=get_activity')['response'];assert d['result']=='success' and 'sessions' in d['data']
 elif s=='plex':
  c=configparser.ConfigParser();c.read(CONFIG/'tautulli/config.ini');d=request('http://192.168.11.129:32400/library/sections',{'X-Plex-Token':c['PMS']['pms_token']},xml=True);assert d.tag=='MediaContainer' and len(d.findall('Directory'))>0
 elif s=='nzbget':
  n=dict(l.strip().split('=',1) for l in (CONFIG/'nzbget/nzbget.conf').read_text().splitlines() if '=' in l and not l.startswith('#'))
  h={'Authorization':'Basic '+base64.b64encode((n['ControlUsername']+':'+n['ControlPassword']).encode()).decode(),'Content-Type':'application/json'}
  d=request('http://127.0.0.1:6790/jsonrpc',h,json.dumps({'method':'status','params':[],'id':1}).encode());assert not d.get('error') and d['result']['UpTimeSec']>0
  out['warnings']=int(d['result']['QuotaReached'])+int(d['result']['DownloadPaused'])+int(d['result']['PostPaused'])
  logs=request('http://127.0.0.1:6790/jsonrpc',h,json.dumps({'method':'log','params':[0,100],'id':1}).encode())
  assert not logs.get('error') and isinstance(logs['result'],list)
  out['recent_errors']=sum(x['Kind']=='ERROR' and time.time()-x['Time']<600 for x in logs['result'])
 elif s=='nginx':
  r=urllib.request.urlopen(urllib.request.Request('https://overseerr.a3f.link/api/v1/status'),timeout=5);d=json.load(r);assert 'version' in d and 'restartRequired' in d
 return out
def kometa_summary(text):
 matches=list(re.finditer(r'Finished: (\d\d:\d\d:\d\d \d{4}-\d\d-\d\d)',text))
 if not matches:return None
 m=matches[-1];ts=datetime.datetime.strptime(m[1],'%H:%M:%S %Y-%m-%d').timestamp()
 before=text[:m.start()]
 if 'Report Error:' in before:return ts,-1
 start=before.rfind('Error Summary')
 # Installed Kometa omits severity summaries when that severity has no rows.
 count=sum(int(x) for x in re.findall(r'\|\s+(\d+)\s+\|',before[start:])) if start>=0 else 0
 return ts,count
def run():
 ROOT.joinpath('textfile').mkdir(exist_ok=True); ROOT.joinpath('logs').mkdir(exist_ok=True)
 lines=[]
 def metric(name,value,s):lines.append(f'homelab_{name}{{host="bb9b",service="{s}"}} {value}')
 services=['sonarr','radarr','prowlarr','bazarr','seerr','tautulli','plex','nzbget','nginx']
 with concurrent.futures.ThreadPoolExecutor(max_workers=9) as pool:
  jobs={pool.submit(check,s):s for s in services}
  for f,s in jobs.items():
   try:
    d=f.result();metric('api_ok',1,s)
    for n,v in d.items():metric(n,v,s)
   except Exception:metric('api_ok',0,s)
 containers=json.loads(subprocess.check_output(['docker','inspect']+subprocess.check_output(['docker','ps','-aq','--filter','label=com.docker.compose.project=homelab']).decode().split(),timeout=8))
 containers=[c for c in containers if c['Config']['Labels'].get('com.docker.compose.service')!='overseerr']
 targets=[]
 for c in containers:
  s=c['Config']['Labels'].get('com.docker.compose.service','unknown');st=c['State']
  metric('container_running',int(st['Running']),s);metric('container_restarts',c['RestartCount'],s);metric('container_oom',int(st['OOMKilled']),s)
  if c['LogPath']:targets.append({'__path__':'/rootfs'+c['LogPath'],'service':s,'host':'bb9b','job':'docker'})
 # Bounded Docker event window catches exits/OOM between state snapshots.
 statepath=ROOT/'docker-events-state.json'
 state=json.loads(statepath.read_text()) if statepath.exists() else {'since':time.time(),'counts':{}}
 now=int(time.time());since=max(state['since'],now-120)
 for c in containers:
  svc=c['Config']['Labels'].get('com.docker.compose.service','unknown')
  for action in ('die','oom','restart'):state['counts'].setdefault(svc+':'+action,0)
 raw=subprocess.check_output(['docker','events','--since',str(int(since)),'--until',str(int(now)),
  '--filter','label=com.docker.compose.project=homelab','--filter','type=container','--format','{{json .}}'],timeout=5).decode()
 for line in raw.splitlines():
  event=json.loads(line);action=event.get('Action');s=event.get('Actor',{}).get('Attributes',{}).get('com.docker.compose.service','unknown')
  if s=='overseerr':continue # Retained stopped rollback container is retired.
  if action in ('die','oom','restart') and event.get('timeNano',0)/1e9>state['since']:
   key=s+':'+action;state['counts'][key]=state['counts'].get(key,0)+1
 state['since']=now
 atomic(statepath,json.dumps(state));statepath.chmod(0o600)
 for key,value in state['counts'].items():
  s,action=key.split(':')
  if s=='overseerr':continue
  lines.append(f'homelab_container_events_total{{host="bb9b",service="{s}",event="{action}"}} {value}')
 monitoring=json.loads(subprocess.check_output(['docker','inspect','homelab-monitoring-loki-1','homelab-monitoring-alloy-1','homelab-monitoring-grafana-1','homelab-monitoring-prometheus-1'],timeout=5))
 for optional in ('blackbox','snmp'):
  try:monitoring+=json.loads(subprocess.check_output(['docker','inspect','homelab-monitoring-'+optional+'-1'],timeout=2,stderr=subprocess.DEVNULL))
  except (subprocess.SubprocessError,ValueError):pass
 for c in monitoring:
  s='monitoring-'+c['Config']['Labels'].get('com.docker.compose.service','unknown')
  if c['LogPath']:targets.append({'__path__':'/rootfs'+c['LogPath'],'service':s,'host':'bb9b','job':'docker'})
 atomic(ROOT/'discovery/docker-targets.json',json.dumps(targets))
 # Read only bounded local Kometa logs. Finished Run plus final summary, not uptime.
 completed=success=errors=0
 for p in (CONFIG/'plexmetamanager/logs').glob('meta*.log*'):
  with p.open('rb') as f:
   f.seek(max(0,p.stat().st_size-1024*1024));text=f.read().decode(errors='replace')
  result=kometa_summary(text)
  if result is None:continue
  ts,count=result
  if ts>completed:completed,errors=ts,count
  if count==0:success=max(success,ts)
 metric('kometa_completed_timestamp',completed,'kometa');metric('kometa_success_timestamp',success,'kometa');metric('kometa_summary_errors',errors,'kometa')
 try:
  lc=json.loads(subprocess.check_output(['docker','inspect','homelab-monitoring-loki-1'],timeout=5))[0]
  ip=next(iter(lc['NetworkSettings']['Networks'].values()))['IPAddress']
  r=urllib.request.urlopen('http://'+ip+':3100/ready',timeout=3);assert r.status==200
  metric('loki_ready',1,'loki')
 except Exception:metric('loki_ready',0,'loki')
 st=os.statvfs(ROOT/'loki');metric('loki_disk_free_ratio',st.f_bavail/st.f_blocks,'loki')
 metric('checks_timestamp',time.time(),'checks')
 atomic(ROOT/'textfile/services.prom','\n'.join(lines)+'\n')
 # Canary traverses the same file source, processing, write, storage and query path.
 if (ROOT/'canary-paused').exists():return
 p=ROOT/'logs/canary.log'
 if p.exists() and p.stat().st_size>1024*1024:p.replace(ROOT/'logs/canary.log.1')
 with p.open('a') as f:f.write(json.dumps({'message':'pipeline_canary','timestamp':time.time()})+'\n')
if __name__=='__main__':run()
