import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
import wanted_checks as w
import version_checks as v

class SearchRetries(unittest.TestCase):
    def test_two_stages_persist_and_do_not_repeat(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'state.json'
            state = {'1': {'since': 0, 'seen': 7200, 'searches': {}}}
            def accepted(url, headers, data):
                persisted = json.loads(path.read_text())['1']['searches']
                self.assertEqual(persisted[str(2 if len(persisted) == 1 else 5)]['status'], 'submitted')
                self.assertEqual(json.loads(data), {'name':'MoviesSearch','movieIds':[1]})
                return {'id': 42}
            with patch.object(w, 'request', side_effect=accepted) as api:
                w.search_missing('radarr', '', {}, state, path, 7199)
                self.assertEqual(api.call_count, 0)
                for now in (7200, 7500, 18000, 18300):
                    w.search_missing('radarr', '', {}, state, path, now)
                self.assertEqual(api.call_count, 2)
            refreshed, _, _ = w.observe('radarr', [dict(id=1,monitored=True,hasFile=False,isAvailable=True,digitalRelease='1970-01-01')], [], state, 7500)
            self.assertEqual(refreshed['1']['searches'], state['1']['searches'])

    def test_timeout_is_not_duplicated_and_five_hour_attempt_still_runs(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.json'
            state={'2':{'since':0,'searches':{}}}
            with patch.object(w,'request',side_effect=TimeoutError) as api:
                self.assertEqual(w.search_missing('sonarr','',{},state,path,7200),1)
                w.search_missing('sonarr','',{},state,path,7500)
                self.assertEqual(api.call_count,1)
            with patch.object(w,'request',return_value={'id':7}) as api:
                w.search_missing('sonarr','',{},state,path,18000)
                self.assertEqual(json.loads(api.call_args.args[2]),{'name':'EpisodeSearch','episodeIds':[2]})

    def test_no_search_for_existing_overdue_and_no_double_catchup(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.json'
            with patch.object(w,'request',return_value={'id':1}) as api:
                state={'1':{'since':0,'searches':{}}}
                w.search_missing('radarr','',{},state,path,36000)
                api.assert_not_called()
                state={'1':{'since':0,'searches':{}}}
                w.search_missing('radarr','',{},state,path,19000)
                self.assertEqual(api.call_count,1)
                self.assertEqual(state['1']['searches']['2']['status'],'skipped')

    def test_queue_and_long_observer_outage_clear_search_cycle(self):
        movie=dict(id=1,monitored=True,hasFile=False,isAvailable=True,digitalRelease='1970-01-01')
        old={'1':{'since':0,'seen':7200,'searches':{'2':{'status':'accepted'}}}}
        self.assertEqual(w.observe('radarr',[movie],[{'movieId':1}],old,7500)[0],{})
        state, _, _=w.observe('radarr',[movie],[],old,9000)
        self.assertEqual(state['1']['searches'],{})

class VersionRetries(unittest.TestCase):
    def test_transient_http_retries_then_succeeds(self):
        class Response:
            headers={}
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read(self,*args): return b'{"ok":true}'
        error=urllib.error.HTTPError('https://example.test',503,'unavailable',{},None)
        with patch.object(v.urllib.request,'urlopen',side_effect=[error,error,Response()]) as api, patch.object(v.time,'sleep') as delay:
            self.assertEqual(v.fetch('https://example.test')[0],{'ok':True})
            self.assertEqual(api.call_count,3)
            self.assertEqual([c.args[0] for c in delay.call_args_list],[1,3])

    def test_auth_challenge_is_not_retried(self):
        error=urllib.error.HTTPError('https://example.test',401,'auth',{},None)
        with patch.object(v.urllib.request,'urlopen',side_effect=error) as api:
            with self.assertRaises(urllib.error.HTTPError): v.fetch('https://example.test')
            self.assertEqual(api.call_count,1)

    def test_three_failures_and_recovery(self):
        row={'service':'radarr','lookup_error':'HTTPError'}
        previous={}
        for expected in (1,2,3):
            count=v.failure_streak(row,previous)
            self.assertEqual(count,expected)
            previous={'radarr':{'lookup_failures':count}}
        self.assertEqual(v.failure_streak({'service':'radarr'},previous),0)
        self.assertEqual(v.error_details(urllib.error.HTTPError('secret',429,'secret',{},None)),{'lookup_error':'HTTPError','lookup_http_status':429})

    def test_retry_timer_skips_healthy_and_recent_snapshots(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with patch.object(v,'ROOT',root),patch.object(v.sys,'argv',['version_checks.py','--retry-failed']),patch.object(v,'run') as run:
                for state in ({'checked':0,'rows':[{'service':'radarr'}]}, {'checked':v.time.time(),'rows':[{'service':'radarr','lookup_error':'HTTPError'}]}):
                    (root/'versions.json').write_text(json.dumps(state))
                    v.main()
                run.assert_not_called()
                (root/'versions.json').write_text(json.dumps({'checked':0,'rows':[{'service':'radarr','lookup_error':'HTTPError'}]}))
                v.main()
                run.assert_called_once()
