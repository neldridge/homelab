import json
import os
import tarfile
import shutil
import fcntl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import retention as r
from verify_bundle import digest

class RetentionTests(unittest.TestCase):
    def bundle(self, root, ident):
        p=root/ident;p.mkdir()
        (p/'manifest.json').write_text(json.dumps({'schema':1,'id':ident,'files':[]}))
        (p/'COMPLETE').write_text(digest(p/'manifest.json'))
        return p
    def test_preserves_seven_status_pins_named_and_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            for n in range(1,11): self.bundle(root,f'202610{n:02}T030000Z')
            (root/'nas-status.json').write_text(json.dumps({'success':True,'bundle_id':'20261001T030000Z'}))
            for name in ['migration-20261001','pre-upgrade-20261001','.partial-20261011T030000Z','20261011T030000Z']:(root/name).mkdir()
            self.assertEqual([p.name for p in r.local_plan(root)],['20261003T030000Z','20261002T030000Z'])
    def test_scratch_success_old_failure_and_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); self.bundle(root,'20261022T030000Z')
            (root/'nas-status.json').write_text(json.dumps({'success':True,'bundle_id':'20261019T030000Z'}))
            t=root/'transfers';t.mkdir()
            for name in ['20261019T030000Z','20261020T030000Z','20261022T030000Z','manual']:(t/name).mkdir()
            now=r.generation_time('20261022T120000Z')
            os.utime(t/'20261020T030000Z', (now-r.SCRATCH_AGE, now-r.SCRATCH_AGE))
            self.assertEqual({p.name for p in r.local_plan(root,now)}, {'20261019T030000Z','20261020T030000Z'})
            (t/'20261019T030000Z'/'unexpected').touch()
            with self.assertRaises(RuntimeError):r.local_plan(root,now)
    def test_failed_verification_and_symlinks_block_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();self.bundle(root,'20261022T030000Z')
            with patch.object(r,'verify',side_effect=RuntimeError('corrupt')):
                with self.assertRaises(RuntimeError):r.prune_local(root,apply=True)
            (root/'local-status.json').symlink_to(root/'missing-status')
            with self.assertRaises(RuntimeError):r.local_plan(root)
            (root/'local-status.json').unlink()
            (root/'transfers').symlink_to(root,target_is_directory=True)
            with self.assertRaises(RuntimeError):r.local_plan(root)
    def test_lock_and_dry_run_prevent_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            for n in range(1,9):self.bundle(root,f'202610{n:02}T030000Z')
            victims=r.prune_local(root,apply=False)
            self.assertEqual(len(victims),1)
            self.assertTrue(victims[0].exists())
            with (root/'transfer.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):r.prune_local(root,apply=True)
            self.assertTrue(victims[0].exists())
            r.prune_local(root,apply=True)
            self.assertFalse(victims[0].exists())

    def test_nas_only_exact_eligible_names_keep_seven(self):
        lines='\n'.join(f'  before-202610{n:02}T030000Z.tar A 100 Thu Oct  1 03:00:00 2026' for n in range(1,10))
        staging='  20261001T030000Z.tar A 100 Thu Oct  1 03:00:00 2026\n  unrelated.tar A 100 Thu Oct  1 03:00:00 2026'
        calls=[]
        def smb(cmd,timeout):
            calls.append(cmd)
            return lines if cmd=='cd prior; ls' else staging if cmd=='cd staging; ls' else ''
        with patch.object(r.time,'time',return_value=r.generation_time('20261022T030000Z')):r.prune_nas(smb,'20261022T030000Z',apply=True)
        self.assertEqual([c for c in calls if c.startswith('del')],['del "prior/before-20261002T030000Z.tar"','del "prior/before-20261001T030000Z.tar"','del "staging/20261001T030000Z.tar"'])

    def test_both_locks_and_lock_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            for name in ('bundle.lock','transfer.lock'):
                with (root/name).open('a') as lock:
                    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    with self.assertRaises(BlockingIOError): r.prune_local(root,True)
            (root/'bundle.lock').unlink()
            (root/'bundle.lock').symlink_to(root/'transfer.lock')
            with self.assertRaises(OSError): r.prune_local(root,True)

    def test_scratch_age_boundary_and_exact_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();self.bundle(root,'20261022T030000Z')
            t=root/'transfers';t.mkdir()
            old=t/'20261001T030000Z';old.mkdir()
            now=r.generation_time('20261022T120000Z')
            (root/'nas-status.json').write_text(json.dumps({'success':True,'bundle_id':'20261022T030000Z'}))
            os.utime(old,(now-r.SCRATCH_AGE+1,now-r.SCRATCH_AGE+1))
            self.assertEqual(r.local_plan(root,now),[])
            os.utime(old,(now-r.SCRATCH_AGE,now-r.SCRATCH_AGE))
            self.assertEqual(r.local_plan(root,now),[old])
            (old/'readback').mkdir();(old/'readback'/'link').symlink_to(root)
            with self.assertRaises(RuntimeError): r.local_plan(root,now)

    def test_local_status_pin_and_unsafe_expired_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            for n in range(1,10):self.bundle(root,f'202610{n:02}T030000Z')
            (root/'local-status.json').write_text(json.dumps({'id':'20261001T030000Z'}))
            self.assertEqual([p.name for p in r.local_plan(root)],['20261002T030000Z'])
            (root/'20261002T030000Z'/'link').symlink_to(root)
            with self.assertRaises(RuntimeError):r.prune_local(root,True)

    def test_nas_dry_run_and_recent_retry(self):
        calls=[]
        def smb(cmd,timeout):
            calls.append(cmd)
            if cmd=='cd prior; ls':
                return '\n'.join(f' before-202610{n:02}T030000Z.tar A 100 Thu Oct 1 03:00:00 2026' for n in range(1,10))
            return ' 20261001T030000Z.tar A 100 Thu Oct 22 03:00:00 2026\n 20261001T030000Z.tar.link A 100 Thu Oct 1 03:00:00 2026'
        with patch.object(r.time,'time',return_value=r.generation_time('20261022T030000Z')):
            r.prune_nas(smb,'20261022T030000Z')
            self.assertFalse(any(c.startswith('del') for c in calls))
            r.prune_nas(smb,'20261022T030000Z',apply=True)
        self.assertFalse(any('staging/' in c for c in calls))

    def test_nas_verification_failure_prevents_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve()
            bundle=self.bundle(root,'20261022T030000Z')
            archive=root/'fixture.tar'
            with tarfile.open(archive,'w') as tar:tar.add(bundle,arcname=bundle.name)
            state={'success':True,'bundle_id':bundle.name,'sha256':r.digest(archive),'validation':r.verify(bundle)}
            (root/'nas-status.json').write_text(json.dumps(state))
            calls=[]
            def smb(cmd,timeout=1800):
                calls.append(cmd)
                if cmd.startswith('get '):shutil.copyfile(archive,cmd.split('"')[1])
                return ''
            with patch.object(r,'ROOT',root), patch('publish_nas.smb',side_effect=smb), patch.object(r,'verify',side_effect=RuntimeError('bad database')):
                with self.assertRaises(RuntimeError):r.nas_retention(apply=True)
            self.assertEqual(len(calls),1)
            self.assertFalse(any(c.startswith('del') for c in calls))

if __name__=='__main__':unittest.main()
