#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Validate catalogue policy; optionally exercise the actual Nex Core parser/renderer."""
import argparse
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PIN = re.compile(r"^[a-z0-9./_-]+:[A-Za-z0-9._-]+@sha256:[0-9a-f]{64}$")
REF = re.compile(r"\$\{([A-Z][A-Z0-9_]*)(?::-([^}]*))?\}")


def validate(root=ROOT):
    manifests = sorted(root.glob('apps/*/nex.yaml'))
    assert manifests, 'No packages found'
    for path in manifests:
        text = path.read_text()
        app = yaml.safe_load(text)
        meta = app['x-nex']
        assert all(meta.get(k) for k in ('name', 'summary', 'category')), path
        assert meta.get('scalable', False) is False, path
        icon = path.parent/'icon.svg'
        assert 0 < icon.stat().st_size <= 32768, icon
        svg = ET.parse(icon).getroot()
        assert svg.tag == '{http://www.w3.org/2000/svg}svg', icon
        assert not any(e.tag.endswith(('script', 'foreignObject', 'image')) for e in svg.iter()), icon
        defaults = {}
        for var, default in REF.findall(text):
            if default:
                assert var not in defaults or defaults[var] == default, (path, var)
                defaults[var] = default
        ports = []
        for name, svc in app['services'].items():
            assert PIN.fullmatch(svc['image']), (path, name, 'image must pin tag and digest')
            assert not any(k in svc for k in ('build','privileged','devices','network_mode','env_file','extends','container_name','depends_on')), (path,name)
            assert svc.get('deploy', {}).get('replicas', 1) == 1, (path,name)
            for volume in svc.get('volumes', []):
                assert re.fullmatch(r'\$\{[A-Z][A-Z0-9_]*\}:/[a-z]+(?::ro)?', volume), (path,volume)
            for port in svc.get('ports', []):
                expanded = REF.sub(lambda m: defaults[m[1]], port)
                published = int(expanded.split(':')[0])
                assert 1 <= published <= 65535 and published not in ports, (path,port)
                ports.append(published)
        print(f'{path.parent.name}: package policy passed')
    return len(manifests)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, help='Nex source checkout with internal/apps')
    args = parser.parse_args()
    count = validate()
    if args.core:
        core = args.core.resolve()
        with tempfile.TemporaryDirectory(prefix='catalogue-check-', dir=core) as folder:
            shutil.copyfile(ROOT/'scripts/check-core.go', Path(folder)/'main.go')
            subprocess.run(['go','run','.',str(ROOT)], cwd=folder, check=True)
    print(f'{count} packages validated; native runtime acceptance is separate')


if __name__ == '__main__':
    main()
