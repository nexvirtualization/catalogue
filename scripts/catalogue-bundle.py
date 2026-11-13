#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Build, sign and verify the application catalogue's signed bundle.

The bundle format and the package digest are defined in internal/appcatalogue/catalogue.go; this
script implements the same definition for the catalogue repository's CI.

    catalogue-bundle.py build <repo dir> <out dir> --commit <sha>
    catalogue-bundle.py sign <out dir> --key <Ed25519 private key PEM>
    catalogue-bundle.py keygen <private.pem> <public.pub>
    catalogue-bundle.py verify <out dir> --pub <public.pub>

A repository holds apps/<id>/nex.yaml, apps/<id>/icon.svg or icon.png, and optionally
apps/<id>/screenshots/*. A top-level tested.txt lists the IDs of tested apps, one per line
(blank lines and # comments are ignored); every other app is listed as untested. build writes
<out>/index.json and copies screenshots to <out>/apps/<id>/screenshots/; its build time is now,
or SOURCE_DATE_EPOCH when set. A .pub file holds the base64 raw 32-byte public key Core reads
from /usr/share/nex/catalogue. Ed25519 signing uses openssl 3; private keys never live in the
repository.
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

INDEX_LIMIT = 16 << 20
MANIFEST_LIMIT = 32 << 10  # protocol.AppComposeLimit
LOGO_LIMIT = 32 << 10  # protocol.AppLogoLimit
SCREENSHOT_LIMIT = 2 << 20  # protocol.AppAssetLimit
MAX_APPS = 1000
MAX_SCREENSHOTS = 5
PACKAGE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SCREENSHOT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
IMAGE_TYPES = {".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".webp": "webp"}
LOGO_TYPES = {"icon.svg": "image/svg+xml", "icon.png": "image/png"}
ED25519_PUBLIC_DER = bytes.fromhex("302a300506032b6570032100")


class BundleError(Exception):
    pass


def digest(manifest, logo, logo_type, screenshots):
    """The package digest: SHA-256 over length-prefixed (8-byte big-endian) fields."""
    fields = [manifest, logo, logo_type.encode()]
    for shot in screenshots:
        fields += [shot["path"].encode(), shot["sha256"].encode()]
    h = hashlib.sha256()
    for field in fields:
        h.update(len(field).to_bytes(8, "big"))
        h.update(field)
    return h.hexdigest()


def image_matches(data, kind):
    if kind == "png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    if kind == "jpeg":
        return data.startswith(b"\xff\xd8\xff")
    return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"


def check_screenshot(app_id, name, data):
    kind = IMAGE_TYPES.get(os.path.splitext(name)[1].lower())
    if not SCREENSHOT_NAME.match(name) or kind is None:
        raise BundleError(f"{app_id}: screenshot {name!r} must be a plain .png, .jpg, .jpeg or .webp file name")
    if not 1 <= len(data) <= SCREENSHOT_LIMIT:
        raise BundleError(f"{app_id}: screenshot {name} is empty or over {SCREENSHOT_LIMIT >> 20} MiB")
    if not image_matches(data, kind):
        raise BundleError(f"{app_id}: screenshot {name} is not the image type its name says")


def read_app(app_dir):
    app_id = app_dir.name
    if not PACKAGE_ID.match(app_id):
        raise BundleError(f"{app_id!r} is not a valid package ID")
    manifest_path = app_dir / "nex.yaml"
    if not manifest_path.is_file():
        raise BundleError(f"{app_id}: nex.yaml is missing")
    manifest = manifest_path.read_bytes()
    if not 1 <= len(manifest) <= MANIFEST_LIMIT:
        raise BundleError(f"{app_id}: nex.yaml is empty or over {MANIFEST_LIMIT >> 10} KiB")
    try:
        manifest.decode("utf-8")
    except UnicodeDecodeError:
        raise BundleError(f"{app_id}: nex.yaml is not UTF-8") from None
    icons = [name for name in LOGO_TYPES if (app_dir / name).is_file()]
    if len(icons) != 1:
        raise BundleError(f"{app_id}: needs exactly one of icon.svg or icon.png")
    logo = (app_dir / icons[0]).read_bytes()
    if not 1 <= len(logo) <= LOGO_LIMIT:
        raise BundleError(f"{app_id}: {icons[0]} is empty or over {LOGO_LIMIT >> 10} KiB")
    shots, files = [], []
    shot_dir = app_dir / "screenshots"
    if shot_dir.is_dir():
        files = sorted(shot_dir.iterdir())
    if len(files) > MAX_SCREENSHOTS:
        raise BundleError(f"{app_id}: more than {MAX_SCREENSHOTS} screenshots")
    for path in files:
        if not path.is_file() or path.is_symlink():
            raise BundleError(f"{app_id}: screenshots/{path.name} is not a regular file")
        data = path.read_bytes()
        check_screenshot(app_id, path.name, data)
        shots.append({"path": f"screenshots/{path.name}", "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
    entry = {"id": app_id, "digest": digest(manifest, logo, LOGO_TYPES[icons[0]], shots),
             "manifest": manifest.decode("utf-8"), "logo": base64.b64encode(logo).decode(),
             "logo_type": LOGO_TYPES[icons[0]], "screenshots": shots, "tested": False}
    return entry, files


def read_tested(repo, ids):
    path = repo / "tested.txt"
    if not path.is_file():
        return set()
    tested = {line.split("#", 1)[0].strip() for line in path.read_text().splitlines()} - {""}
    unknown = sorted(tested - set(ids))
    if unknown:
        raise BundleError(f"tested.txt names apps that do not exist: {', '.join(unknown)}")
    return tested


def build(args):
    repo, out = Path(args.repo), Path(args.out)
    if not COMMIT.match(args.commit):
        raise BundleError("--commit takes the full 40-character lowercase Git commit hash")
    if out.exists() and any(out.iterdir()):
        raise BundleError(f"refusing to build into a directory that is not empty: {out}")
    app_dirs = sorted(path for path in (repo / "apps").iterdir() if path.is_dir()) if (repo / "apps").is_dir() else []
    if len(app_dirs) > MAX_APPS:
        raise BundleError(f"more than {MAX_APPS} apps")
    apps = [read_app(app_dir) for app_dir in app_dirs]
    tested = read_tested(repo, [entry["id"] for entry, _ in apps])
    for entry, _ in apps:
        entry["tested"] = entry["id"] in tested
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    when = datetime.datetime.fromtimestamp(int(epoch), datetime.timezone.utc) if epoch else \
        datetime.datetime.now(datetime.timezone.utc)
    document = {"format": 1, "commit": args.commit, "created": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "apps": [entry for entry, _ in apps]}
    body = (json.dumps(document, indent=1, sort_keys=True) + "\n").encode()
    if len(body) > INDEX_LIMIT:
        raise BundleError(f"index.json would be over {INDEX_LIMIT >> 20} MiB")
    out.mkdir(parents=True, exist_ok=True)
    for entry, files in apps:
        if files:
            target = out / "apps" / entry["id"] / "screenshots"
            target.mkdir(parents=True)
            for path in files:
                shutil.copyfile(path, target / path.name)
    (out / "index.json").write_bytes(body)
    print(f"built {out / 'index.json'}: {len(apps)} apps, commit {args.commit}")


def public_raw(key):
    der = subprocess.run(["openssl", "pkey", "-in", str(key), "-pubout", "-outform", "DER"],
                         check=True, capture_output=True).stdout
    if not der.startswith(ED25519_PUBLIC_DER) or len(der) != 44:
        raise BundleError(f"an Ed25519 key is required: {key}")
    return der[-32:]


def sign(args):
    index = Path(args.out) / "index.json"
    if not Path(args.key).is_file():
        raise BundleError(f"the signing key does not exist: {args.key}")
    public_raw(args.key)
    signature = subprocess.run(["openssl", "pkeyutl", "-sign", "-inkey", args.key, "-rawin", "-in", str(index)],
                               check=True, capture_output=True).stdout
    if len(signature) != 64:
        raise BundleError("signing produced a malformed signature")
    (Path(args.out) / "index.json.sig").write_text(base64.b64encode(signature).decode() + "\n")
    print(f"signed {index}")


def keygen(args):
    private, public = Path(args.private), Path(args.public)
    for path in (private, public):
        if path.exists():
            raise BundleError(f"refusing to overwrite {path}")
    subprocess.run(["openssl", "genpkey", "-algorithm", "ed25519", "-out", str(private)], check=True)
    private.chmod(0o600)
    encoded = base64.b64encode(public_raw(private)).decode()
    public.write_text(encoded + "\n")
    print(encoded)


def read_public(path):
    try:
        raw = base64.b64decode(Path(path).read_text().strip(), validate=True)
    except ValueError:
        raw = b""
    if len(raw) != 32:
        raise BundleError(f"{path} does not hold a base64 raw 32-byte Ed25519 public key")
    return raw


def check_index(body):
    """Validate index.json as Core does, and return it parsed."""
    if len(body) > INDEX_LIMIT:
        raise BundleError(f"index.json is over {INDEX_LIMIT >> 20} MiB")
    document = json.loads(body)
    if document.get("format") != 1:
        raise BundleError("unsupported index format")
    if not COMMIT.match(str(document.get("commit", ""))):
        raise BundleError("the commit is not a 40-character Git hash")
    datetime.datetime.fromisoformat(str(document.get("created", "")).replace("Z", "+00:00"))
    apps = document.get("apps") or []
    if len(apps) > MAX_APPS:
        raise BundleError(f"more than {MAX_APPS} apps")
    seen = set()
    for app in apps:
        app_id = app.get("id", "")
        if not PACKAGE_ID.match(app_id) or app_id in seen:
            raise BundleError(f"invalid or repeated app ID {app_id!r}")
        seen.add(app_id)
        manifest = app["manifest"].encode()
        logo = base64.b64decode(app["logo"], validate=True)
        if not 1 <= len(manifest) <= MANIFEST_LIMIT or not 1 <= len(logo) <= LOGO_LIMIT:
            raise BundleError(f"{app_id}: nex.yaml or the logo is empty or too large")
        if app["logo_type"] not in LOGO_TYPES.values():
            raise BundleError(f"{app_id}: the logo must be SVG or PNG")
        shots = app.get("screenshots") or []
        if len(shots) > MAX_SCREENSHOTS or len({shot["path"] for shot in shots}) != len(shots):
            raise BundleError(f"{app_id}: more than {MAX_SCREENSHOTS} or repeated screenshots")
        for shot in shots:
            name = shot["path"].removeprefix("screenshots/")
            if not shot["path"].startswith("screenshots/") or not SCREENSHOT_NAME.match(name) or \
                    os.path.splitext(name)[1].lower() not in IMAGE_TYPES or not SHA256.match(shot["sha256"]) or \
                    not 1 <= shot["size"] <= SCREENSHOT_LIMIT:
                raise BundleError(f"{app_id}: invalid screenshot entry {shot['path']!r}")
        if app["digest"] != digest(manifest, logo, app["logo_type"], shots):
            raise BundleError(f"{app_id}: its contents do not match its digest")
    return document


def verify(args):
    out = Path(args.out)
    body = (out / "index.json").read_bytes()
    signature = base64.b64decode((out / "index.json.sig").read_text().strip(), validate=True)
    with tempfile.TemporaryDirectory() as scratch:
        der = Path(scratch) / "key.der"
        der.write_bytes(ED25519_PUBLIC_DER + read_public(args.pub))
        sig = Path(scratch) / "index.sig"
        sig.write_bytes(signature)
        result = subprocess.run(["openssl", "pkeyutl", "-verify", "-pubin", "-keyform", "DER", "-inkey", str(der),
                                 "-rawin", "-in", str(out / "index.json"), "-sigfile", str(sig)], capture_output=True)
    if result.returncode != 0:
        raise BundleError("the signature does not match index.json")
    document = check_index(body)
    for app in document["apps"]:
        for shot in app["screenshots"]:
            path = out / "apps" / app["id"] / shot["path"]
            data = path.read_bytes() if path.is_file() else b""
            if len(data) != shot["size"] or hashlib.sha256(data).hexdigest() != shot["sha256"]:
                raise BundleError(f"{app['id']}: {shot['path']} is missing or does not match the index")
            check_screenshot(app["id"], path.name, data)
    print(f"verified {out / 'index.json'}: {len(document['apps'])} apps, commit {document['commit']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("build")
    p.add_argument("repo")
    p.add_argument("out")
    p.add_argument("--commit", required=True)
    p.set_defaults(run=build)
    p = commands.add_parser("sign")
    p.add_argument("out")
    p.add_argument("--key", required=True)
    p.set_defaults(run=sign)
    p = commands.add_parser("keygen")
    p.add_argument("private")
    p.add_argument("public")
    p.set_defaults(run=keygen)
    p = commands.add_parser("verify")
    p.add_argument("out")
    p.add_argument("--pub", required=True)
    p.set_defaults(run=verify)
    args = parser.parse_args(argv)
    try:
        args.run(args)
    except (BundleError, OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"catalogue-bundle: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
