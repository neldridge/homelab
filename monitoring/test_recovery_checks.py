import json,tempfile,unittest
from pathlib import Path
from recovery_checks import metrics
class RecoveryTests(unittest.TestCase):
    def test_local_never_implies_offhost(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'local-status.json').write_text(json.dumps(dict(source='bundle-validator',success=True,completed=100,observed=100)))
            output=metrics(root,200)
            self.assertIn('homelab_recovery_known{host="bb9b",stage="local"} 1',output)
            for stage in ('nas','cloud'):
                self.assertIn(f'homelab_recovery_known{{host="bb9b",stage="{stage}"}} 0',output)
    def test_cloud_local_age_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'cloud-status.json').write_text(json.dumps(dict(source='bundle-validator',success=True,completed=100,observed=100)))
            self.assertIn('homelab_recovery_known{host="bb9b",stage="cloud"} 0',metrics(root,200))
if __name__=='__main__':unittest.main()
