import json, os, sqlite3, tempfile, time, unittest, zipfile
from pathlib import Path
from unittest.mock import patch
import nfs_probe as n
import storage_checks as s
import backup_checks as b

class StorageFixtures(unittest.TestCase):
    def test_tautulli_manual_and_independent_config_freshness(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for name,stamp in [('tautulli.backup-1.sched.db.zip',100),('tautulli.backup-2.db.zip',300),('config.backup-3.sched.ini.zip',200)]:
                p=root/name;p.touch();os.utime(p,(stamp,stamp))
            db,config,stamp=b.tautulli_artifacts(root)
            self.assertEqual(db.name,'tautulli.backup-2.db.zip')
            self.assertEqual(config.name,'config.backup-3.sched.ini.zip')
            self.assertEqual(stamp,200) # Fresh DB cannot hide a stale config.
            config.unlink()
            with self.assertRaises(ValueError):b.tautulli_artifacts(root)
    def test_tautulli_config_validation(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'config.backup-1.ini.zip'
            for contents,valid in [('[General]\nfixture=1\n',True),('[Other]\nfixture=1\n',False)]:
                with zipfile.ZipFile(p,'w') as z:z.writestr('config.ini',contents)
                if valid:b.validate_tautulli_config(p)
                else:
                    with self.assertRaises(AssertionError):b.validate_tautulli_config(p)
    def mount(self,source='192.168.11.131:/volume2/media-library',fs='nfs'):
        return f'1 0 0:1 / /mnt/media-library rw - {fs} {source} rw\n'
    def test_missing_wrong_source_and_filesystem(self):
        self.assertFalse(n.mount_ok('library',''))
        self.assertFalse(n.mount_ok('library',self.mount('192.168.11.2:/wrong')))
        self.assertFalse(n.mount_ok('library',self.mount(fs='ext4')))
        self.assertTrue(n.mount_ok('library',self.mount()))
    def test_read_failure_and_recovery(self):
        for age,expected in [(46,0),(1,1)]:
            rows=s.storage_metrics(self.mount(),{'library':{'timestamp':100-age,'ok':1}},100)
            self.assertIn(f'homelab_nfs_read_ok{{host="bb9b",service="nfs-library"}} {expected}',rows)
        self.assertIn('homelab_nfs_read_ok{host="bb9b",service="nfs-library"} 0',s.storage_metrics('',{'library':{'timestamp':99,'ok':1}},100))
    def test_backup_corrupt_missing_and_recovery(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);db=sqlite3.connect(root/'test.db');db.execute('create table fixture(id integer)');db.commit();db.close()
            p=root/'backup.zip'
            def write(data):
                with zipfile.ZipFile(p,'w') as z:
                    z.writestr('sonarr.db',data);z.writestr('config.xml','<Config/>');z.writestr('INFO','fixture')
            write(b'broken')
            with self.assertRaises(AssertionError): b.validate_archive(p,'sonarr',root)
            write((root/'test.db').read_bytes());b.validate_archive(p,'sonarr',root)
            p.write_bytes(b'not a ZIP')
            with self.assertRaises(zipfile.BadZipFile): b.validate_archive(p,'sonarr',root)
            write((root/'test.db').read_bytes());b.validate_archive(p,'sonarr',root)
if __name__=='__main__':unittest.main()
