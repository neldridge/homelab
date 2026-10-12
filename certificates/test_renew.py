import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('renew', Path(__file__).with_name('renew.py'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class DeploymentTests(unittest.TestCase):
    def test_failed_health_restores_both_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); dest = root/'dest'; src = root/'src'
            dest.mkdir(); src.mkdir()
            for f in ('fullchain.pem', 'privkey.pem'):
                (dest/f).write_text('old'); (src/f).write_text('new')
            def replacement(source, target, *_): target.write_bytes(source.read_bytes())
            with patch.object(m, 'ROOT', root), patch.dict(m.SETS, {'fixture':(str(dest), ['fixture'], [], 0, 0o600)}), patch.object(m, 'validate'), patch.object(m, 'compose'), patch.object(m, 'activate') as activate, patch.object(m, 'replace', side_effect=replacement), patch.object(m.time, 'sleep'), patch.object(m, 'health', side_effect=[RuntimeError()]*20+[None]):
                with self.assertRaises(RuntimeError): m.deploy('fixture', src)
                self.assertEqual(activate.call_count, 2)
                for f in ('fullchain.pem', 'privkey.pem'): self.assertEqual((dest/f).read_text(), 'old')

    def test_invalid_candidate_never_changes_files(self):
        with patch.object(m, 'validate', side_effect=ValueError()), patch.object(m, 'replace') as replace:
            with self.assertRaises(ValueError): m.deploy('a3f', Path('/invalid'))
            replace.assert_not_called()

if __name__ == '__main__': unittest.main()
