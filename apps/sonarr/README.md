<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Sonarr

Manage a standalone television collection. This is a standalone, single-copy Nex catalogue package using the LinuxServer image.

## Status

Listed; native Nex lab install, first-run authentication, permissions, update, backup/restore, host failover and Controller replacement tests are **unrun**. Image publication and package-format checks do not establish runtime acceptance.

## Configuration and authentication

1. Choose persistent storage for the mappings below. Keep one replica.
2. Edit `PUID` and `PGID` (both default to `1000`) to the numeric owner/group permitted to write that storage; `TZ` defaults to `Etc/UTC` and is editable. The container initialization uses LinuxServer's normal privilege model; PUID does not make the entire container run without root.
3. Choose the published HTTP `PORT` (default `8989`); the container still listens on `8989`.
4. Open the selected host address and published port over HTTP on a trusted network. Complete the first-run authentication prompt, select Forms authentication, set a unique username/password, and leave Authentication Required enabled for all addresses. Review Settings → General → Security before exposing access.
5. Configure root folders, quality profiles and indexers in the application. Follow the [upstream quick-start guide](https://wiki.servarr.com/sonarr/quick-start-guide) and [authentication settings](https://wiki.servarr.com/sonarr/settings#security).

No password or API key is supplied by this manifest. Nex login does not authenticate requests to this application's web UI. Treat its API key as a credential and protect configuration backups. HTTP is published directly; provide trusted TLS termination before remote access.

## Storage and permissions

- `CONFIG` → `/config`: settings, database, API keys and credentials; keep persistent and back it up.
- `DATA` → `/data`: the selected library and staged imports. Create `/data/tv` as its root folder and keep incoming files in `/data/downloads`, outside the library root.

Nex allocates a private folder for each storage row by default. To integrate separately installed
apps, select the same NFS/SMB share and the same **Existing folder on the share** for their DATA
rows, with compatible permissions and identical `/data` paths. Selecting the share alone does not
share the default folders. Keep every CONFIG folder separate; never share configuration databases.
Remote path mappings translate names but cannot mount missing files. Use **arr-suite** to share DATA
within one installation. Native share permissions and locking remain untested.

One `/data` mapping keeps library and staged downloads together; hardlinks and atomic moves still require filesystem support and matching permissions. This package makes no tested claim about either.

Both the mapped directories and imported files need ownership or ACLs that permit the chosen PUID/PGID to read and write them. Nex may create folders as root; choosing a UID/GID does not itself change share-side permissions. Have the storage administrator grant only the required access, then confirm the app can save settings and, where applicable, import a file. Do not use world-writable permissions as a shortcut. NAS UID mapping and ACLs must also allow access. See [LinuxServer's UID/GID guidance](https://docs.linuxserver.io/general/understanding-puid-and-pgid/).

## Limits and recovery

- One replica, non-scalable: never start two writers against the same configuration database.
- No download client, VPN, host networking, host paths, Docker socket, extra privileges or device access is requested.
- No resource cap is set by this package; size the host for the workload.
- Stop the app before copying its configuration/database for a consistent manual backup. Back up the library separately as well; a configuration export alone is not a full recovery test.
- Update by replacing the pinned container image through the catalogue workflow; do not use an in-container updater. Preserve data, review upstream changes and test recovery before accepting an update.

## Image provenance and licenses

Exact image reference:

```text
ghcr.io/linuxserver/sonarr:4.0.20.3014-ls4@sha256:673dc4609a5672bc8e46069c86ffcea283a86b48d34a6c93d8da8c24a1b87571
```

The versioned tag is published in the [LinuxServer release](https://github.com/linuxserver/docker-sonarr/releases/tag/4.0.20.3014-ls4). The anonymous [GHCR manifest endpoint](https://ghcr.io/v2/linuxserver/sonarr/manifests/4.0.20.3014-ls4) was fetched using a registry pull token; its `Docker-Content-Digest` matched the SHA-256 of the returned index bytes. The index includes Linux `amd64` and `arm64` manifests (and attestation entries). The manifest pins that index digest, not a floating channel. This verifies registry publication, not a container boot or a supply-chain audit.

- [Sonarr source](https://github.com/Sonarr/Sonarr) and [upstream GPL v3 license](https://github.com/Sonarr/Sonarr/blob/develop/LICENSE.md). `license: GPL-3.0` describes the upstream application; bundled components retain their own licenses.
- [LinuxServer container source](https://github.com/linuxserver/docker-sonarr), [container license](https://github.com/linuxserver/docker-sonarr/blob/master/LICENSE), and [image configuration documentation](https://docs.linuxserver.io/images/docker-sonarr/).
- `nex.yaml`, this README and `icon.svg` are original catalogue work licensed **AGPL-3.0-only**. The colorful icon is an original, unofficial illustration, not upstream artwork or an official logo. No upstream artwork is bundled.

## Nex integration

API impact: **existing contract** — Core parses this Compose package, infers its settings/storage/port questions, and renders the deployment through the existing application install contract; no endpoint or behavior changes.

Guide impact: **updated** — this README documents package setup, authentication, storage, limits and unrun verification. Durable application settings and storage mappings use Core's existing cluster-master application record and inventory/adoption path; this package adds no Controller-owned state.

## Checks performed

Core's actual `apps.Parse`, `ValidateCatalogue` and `Render` accepted this file in a temporary Go harness. Checks passed for host storage, default and edited web ports, default and edited PUID/PGID/TZ, rejection of two replicas, and rejection of missing storage. SVG XML parsing and static checks for disallowed service settings, license markers and whitespace also passed. These are format/render checks; no native container or Nex lab workflow was run.
