#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Build and check the application catalogue bundle's integrity.

The bundle format and the package digest are defined in internal/appcatalogue/catalogue.go; this
script implements the same definition for the catalogue repository's CI.

    catalogue-bundle.py build <repo dir> <out dir> --commit <sha>
    catalogue-bundle.py verify <out dir>

A repository holds apps/<id>/nex.yaml, apps/<id>/icon.svg or icon.png, and optionally
apps/<id>/screenshots/*. A top-level tested.txt lists the IDs of tested apps, one per line
(blank lines and # comments are ignored); every other app is listed as untested. build writes
<out>/index.json and copies screenshots to <out>/apps/<id>/screenshots/; its build time is now,
or SOURCE_DATE_EPOCH when set. Checksums detect inconsistent contents; they do not
authenticate the publisher.
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
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
    p = commands.add_parser("verify")
    p.add_argument("out")
    p.set_defaults(run=verify)
    args = parser.parse_args(argv)
    try:
        args.run(args)
    except (BundleError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"catalogue-bundle: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
