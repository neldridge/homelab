import tempfile, unittest, json, time
from pathlib import Path
from unittest.mock import patch
import service_checks as c

class ChecksTest(unittest.TestCase):
 def test_kometa_success_requires_summary_completion(self):
  self.assertIsNone(c.kometa_summary('Started Run'))
  self.assertEqual(c.kometa_summary('Finished Run\nFinished: 10:28:06 2026-10-11')[1],0)
 def test_kometa_finished_with_errors_is_not_success(self):
  self.assertEqual(c.kometa_summary('Error Summary\n| 73 | Overlay Error |\n| 2 | Unauthorized |\nFinished Run\nFinished: 10:28:06 2026-10-11')[1],75)
 def test_kometa_summary_failure_is_unknown(self):
  self.assertEqual(c.kometa_summary('Report Error: failed\nFinished: 10:28:06 2026-10-11')[1],-1)
 def test_http_200_wrong_semantics_fails(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);(r/'app-keys.json').write_text('{}')
   with patch.object(c,'ROOT',r),patch.object(c,'request',return_value={'html':'landing page'}):
    with self.assertRaises(AssertionError):c.check('seerr')
 def test_api_explicit_schema_passes(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);(r/'app-keys.json').write_text('{}')
   with patch.object(c,'ROOT',r),patch.object(c,'request',return_value={'pageInfo':{},'results':[]}):
    self.assertEqual(c.check('seerr'),{})
 def test_container_event_and_oom_fixture(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'discovery').mkdir();(root/'loki').mkdir()
   (root/'docker-events-state.json').write_text(json.dumps({'since':time.time()-10,'counts':{'sonarr:die':0}}))
   container={'Config':{'Labels':{'com.docker.compose.service':'sonarr'}},'State':{'Running':True,'OOMKilled':True},'RestartCount':2,'LogPath':'/var/lib/docker/fixture.log'}
   event={'Action':'die','Actor':{'Attributes':{'com.docker.compose.service':'sonarr'}},'timeNano':int((time.time()-2)*1e9)}
   def output(cmd,**kw):
    if cmd[1]=='ps':return b'fixture'
    if cmd[1]=='events':return json.dumps(event).encode()
    return json.dumps([container]).encode()
   with patch.object(c,'ROOT',root),patch.object(c,'CONFIG',root/'config'),patch.object(c,'check',return_value={}),patch.object(c.subprocess,'check_output',side_effect=output):c.run()
   text=(root/'textfile/services.prom').read_text()
   self.assertIn('homelab_container_oom{host="bb9b",service="sonarr"} 1',text)
   self.assertIn('homelab_container_restarts{host="bb9b",service="sonarr"} 2',text)
   self.assertIn('service="sonarr",event="die"} 1',text)
if __name__=='__main__':unittest.main()
