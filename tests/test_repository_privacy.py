# SPDX-License-Identifier: AGPL-3.0-only
"""Keep personal paths, observed lab IDs, and credentials out of public files."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME_PATH = re.compile(r"/(?:home|Users)/[A-Za-z0-9_.-]+/")
OBSERVED_ID = re.compile(
    r'"(?:id|[^"\n]*_(?:id|uuid)|uuid|certificate_sha256)"\s*:\s*"'
    r'(?:[0-9a-f]{64}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})"', re.I)
CREDENTIAL = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----\s+[A-Za-z0-9+/=]{64,}|"
    r"\bgh[pousr]_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{30,}|"
    r"\bAKIA[0-9A-Z]{16}\b|\bxox[baprs]-[0-9A-Za-z-]{20,}"
)
CI_FILE = re.compile(r"^(?:\.gitlab-ci\.yml$|ci/|\.github/workflows/|\.gitea/workflows/)")
GITLAB_URL = re.compile(r"https?://(gitlab\.[A-Za-z0-9.-]*[A-Za-z0-9])")
ENCODED_PROJECT = re.compile(r"projects/[^<\s]+%2F")


def ci_findings(name, line, number):
    findings = []
    for match in GITLAB_URL.finditer(line):
        if match.group(1).lower() != 'example.com' and not match.group(1).lower().endswith('.example.com'):
            findings.append(f'{name}:{number}: private GitLab host')
    if ENCODED_PROJECT.search(line):
        findings.append(f'{name}:{number}: private GitLab project path')
    return findings


def privacy_findings(name, data):
    # Executables and other binary artifacts can embed paths and credentials too.
    text = data.decode('utf-8', errors='replace')
    findings = []
    for number, line in enumerate([name, *text.splitlines()]):
        if name.startswith('docs/qa/') and OBSERVED_ID.search(line):
            findings.append(f'{name}:{number}: observed environment identifier')
        if HOME_PATH.search(line):
            findings.append(f'{name}:{number}: personal home path')
        if CI_FILE.match(name):
            findings.extend(ci_findings(name, line, number))
    if CREDENTIAL.search(text):
        findings.append(f'{name}: possible credential')
    return findings


class RepositoryPrivacyTests(unittest.TestCase):
    def test_public_repository_has_no_private_paths_ids_or_credentials(self):
        files = subprocess.check_output(
            ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
            cwd=ROOT).decode().split('\0')
        findings = []
        for name in sorted(set(files) - {''}):
            path = ROOT / name
            if path.is_symlink():
                data = str(path.readlink()).encode()
            elif path.is_file():
                data = path.read_bytes()
            else:
                continue
            findings.extend(privacy_findings(name, data))
        self.assertFalse(findings, '\n' + '\n'.join(findings))

    def test_binary_artifacts_are_scanned_for_embedded_home_paths(self):
        fictional_path = '/'.join(('', 'home', 'example-user', 'project', 'main.go')).encode()
        artifact = b'\x7fELF\0\xff' + fictional_path + b'\0'
        self.assertTrue(privacy_findings('fixture.bin', artifact))
        self.assertFalse(privacy_findings('fixture.bin', b'\x7fELF\0\xffpublic-source/main.go\0'))

    def test_ci_files_name_no_private_gitlab_host_or_project(self):
        host = 'gitlab.' + 'corp.invalid'
        self.assertTrue(privacy_findings('ci/gitlab/x.yml', f'url: https://{host}/group/x'.encode()))
        self.assertTrue(privacy_findings('.github/workflows/x.yml', b'glab api projects/team%2Fproject/jobs'))
        self.assertFalse(privacy_findings('ci/gitlab/x.yml', b'url: https://gitlab.example.com/group/x'))
        self.assertFalse(privacy_findings('ci/gitlab/x.yml', b'# (https://gitlab.example.com, project x)'))
        self.assertTrue(privacy_findings('ci/gitlab/x.yml', f'# (https://{host}, project x)'.encode()))
        self.assertFalse(privacy_findings('ci/gitlab/x.yml', b'glab api projects/<group>%2F<project>/jobs'))
        self.assertFalse(privacy_findings('docs/x.md', f'https://{host}/x'.encode()))


if __name__ == '__main__':
    unittest.main()
