<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Nex Application Catalogue

Curated Compose packages for Nex Core Applications, executed on Nex-managed Docker Swarm hosts.
Nex Core owns deployment and durable settings; Nex Controller submits requests and displays results.

**Development catalogue: packages have not completed native lab acceptance.** Published image
digests and package/render validation do not establish working downloads, safe NAS database locking,
host failover or recovery. `tested.txt` intentionally contains no app IDs.

## Packages

| Package | Purpose | Setup |
| --- | --- | --- |
| Arr Suite | Integrated seven-service media/download workflow | [Guide](apps/arr-suite/README.md) |
| Radarr | Movie library management | [Guide](apps/radarr/README.md) |
| Sonarr | Television library management | [Guide](apps/sonarr/README.md) |
| Prowlarr | Indexer management | [Guide](apps/prowlarr/README.md) |
| Lidarr | Music library management | [Guide](apps/lidarr/README.md) |
| Bazarr | Subtitles for Sonarr/Radarr libraries | [Guide](apps/bazarr/README.md) |
| qBittorrent | BitTorrent download client | [Guide](apps/qbittorrent/README.md) |
| SABnzbd | Usenet download client | [Guide](apps/sabnzbd/README.md) |

Choose **Arr Suite** for an integrated installation. Independent Nex apps receive private folders by default;
to share data, explicitly select the same **Existing folder on the share** for their DATA rows.
Keep their configuration folders separate. The combined package shares one data mapping within
one installation. [Readarr is excluded because its upstream project is retired](https://github.com/Readarr/Readarr#announcement-retirement-of-readarr).
No media server, VPN, credentials, paid service or automatic application configuration is included.

## Use in a disposable lab

Follow the [Arr Suite guide](apps/arr-suite/README.md). Start with one host and local settings
storage. Import its `nex.yaml` through **Applications → Add your own**, or publish a signed bundle
and add it as a catalogue source. A GitHub source repository URL is **not** a catalogue source URL:
Core expects HTTPS `index.json` and `index.json.sig`, with a separately trusted public key.
This repository does not configure the official catalogue URL, publish keys or deploy to hosts.

## Validation

Use Python 3.11 or newer and OpenSSL 3. Run from this checkout:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate.py
python3 -m unittest discover -s tests
# Optional: exercise the actual Core parser and renderer using a Nex source checkout.
python3 scripts/validate.py --core ../nex
```

The Core check creates and removes a temporary Go harness inside that checkout for Go's internal
import rules; it does not edit Core source. It uses that checkout's Go toolchain and dependencies.
CI runs policy/regression checks and Compose configuration validation, without Nex secrets or host
access. Core checks require its separate source checkout and are not claimed as hosted enforcement.
Use the [native checklist](docs/lab-acceptance.md) before marking any package tested.

## Build and sign a catalogue bundle

The bundle tool uses Nex's format-1 index and length-prefixed SHA-256 package digest. It is copied
from Nex's AGPL-3.0-only bundle builder, with its original license preserved.

```sh
python3 scripts/catalogue-bundle.py build . dist/v1 --commit "$(git rev-parse HEAD)"
# Use an authorized existing signing key held outside this repository.
python3 scripts/catalogue-bundle.py sign dist/v1 --key /secure/catalogue-signing.pem
python3 scripts/catalogue-bundle.py verify dist/v1 --pub /secure/catalogue-signing.pub
```

Publish the resulting `dist/v1` directory unchanged to your chosen HTTPS lab catalogue endpoint.
Supply its address and the trusted public key in **Applications → Settings → Catalogue sources**.
Do not commit signing keys, generate an official trust identity casually, or mark packages tested
just because a bundle verifies. No signing key or hosting infrastructure is supplied here.

## Contributing and licensing

Keep one app under `apps/<id>/` with `nex.yaml`, `icon.svg` and `README.md`. Pin a version **and**
registry digest, record primary upstream documentation and license links, retain authentication,
and use operator-selected storage variables. Do not request host paths, Docker sockets, devices,
privileged mode or host networking. Preserve a single writer for stateful services.

Original catalogue manifests, scripts, docs and unofficial icons are **AGPL-3.0-only**;
see [LICENSE](LICENSE). Application and image components retain their upstream licenses.
The repository references images and does not redistribute their binaries. Icons are original
illustrations, not official upstream logos. Never add third-party artwork without its actual license.
Do not include private addresses, account details, credentials or personal information in contributions.
