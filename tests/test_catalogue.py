# SPDX-License-Identifier: AGPL-3.0-only
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validate', ROOT/'scripts/validate.py')
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class CatalogueTests(unittest.TestCase):
    def test_all_packages(self):
        self.assertEqual(policy.validate(), 8)

    def test_unsafe_changes_are_rejected(self):
        for old, new in [('ghcr.io/linuxserver/radarr:', 'ghcr.io/linuxserver/radarr:latest #'),
                         ('${CONFIG}:/config', '/etc:/config'),
                         ('replicas: 1', 'replicas: 2')]:
            with self.subTest(change=new), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                shutil.copytree(ROOT/'apps/radarr', root/'apps/radarr')
                manifest = root/'apps/radarr/nex.yaml'
                original = manifest.read_text()
                self.assertIn(old, original)
                manifest.write_text(original.replace(old, new))
                with self.assertRaises(AssertionError):
                    policy.validate(root)

    def test_suite_shares_data_but_separates_configuration(self):
        app = policy.yaml.safe_load((ROOT/'apps/arr-suite/nex.yaml').read_text())
        configs = set()
        for name, service in app['services'].items():
            config = [v for v in service['volumes'] if v.endswith(':/config')]
            self.assertEqual(len(config), 1)
            configs.add(config[0])
            self.assertEqual('${DATA}:/data' in service['volumes'], name != 'prowlarr')
            standalone = policy.yaml.safe_load((ROOT/'apps'/name/'nex.yaml').read_text())
            self.assertEqual(service['image'], standalone['services'][name]['image'])
        self.assertEqual(len(configs), 7)

    def test_signed_bundle_roundtrip_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tool = ROOT/'scripts/catalogue-bundle.py'
            def run(*args):
                return subprocess.run(['python3', str(tool), *map(str,args)], capture_output=True, text=True)
            built = run('build', ROOT, root/'bundle', '--commit', 'a'*40)
            self.assertEqual(built.returncode, 0, built.stderr)
            document = json.loads((root/'bundle/index.json').read_text())
            self.assertEqual(len(document['apps']), 8)
            self.assertFalse(any(app['tested'] for app in document['apps']))
            for args in [('keygen', root/'key.pem', root/'key.pub'),
                         ('sign',root/'bundle','--key',root/'key.pem'),
                         ('verify',root/'bundle','--pub',root/'key.pub')]:
                result = run(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
            index = root/'bundle/index.json'
            index.write_bytes(index.read_bytes()+b' ')
            self.assertNotEqual(run('verify',root/'bundle','--pub',root/'key.pub').returncode, 0)


if __name__ == '__main__':
    unittest.main()
