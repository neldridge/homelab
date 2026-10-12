import json, sqlite3, tempfile, unittest
from pathlib import Path
from create_bundle import copy_file, digest
from verify_bundle import verify
class BundleTests(unittest.TestCase):
    def test_live_wal_and_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'live.db';out=root/'bundle';out.mkdir();records=[]
            with sqlite3.connect(src) as live:
                live.execute('pragma journal_mode=wal');live.execute('create table t(value)');live.execute('insert into t values (42)');live.commit()
                copy_file(src,out/'db.sqlite3',records,out)
                self.assertEqual(sqlite3.connect(out/'db.sqlite3').execute('select value from t').fetchone(),(42,))
                (out/'manifest.json').write_text(json.dumps(dict(schema=1,id='fixture',files=records)))
                (out/'COMPLETE').write_text(digest(out/'manifest.json'))
                self.assertEqual(verify(out)['databases'],1)
                (out/'db.sqlite3').write_bytes(b'corrupt')
                with self.assertRaises(AssertionError):verify(out)
    def test_unknown_database_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'bad.db';src.write_bytes(b'not sqlite')
            with self.assertRaises(RuntimeError):copy_file(src,root/'out.db',[],root)
if __name__=='__main__':unittest.main()
