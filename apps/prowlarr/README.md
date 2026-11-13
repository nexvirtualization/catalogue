<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Prowlarr

Manage and synchronize search indexers. This is a standalone, single-copy Nex catalogue package using the LinuxServer image.

## Status

Listed; native Nex lab install, first-run authentication, permissions, update, backup/restore, host failover and Controller replacement tests are **unrun**. Image publication and package-format checks do not establish runtime acceptance.

## Configuration and authentication

1. Choose persistent storage for the mappings below. Keep one replica.
2. Edit `PUID` and `PGID` (both default to `1000`) to the numeric owner/group permitted to write that storage; `TZ` defaults to `Etc/UTC` and is editable. The container initialization uses LinuxServer's normal privilege model; PUID does not make the entire container run without root.
3. Choose the published HTTP `PORT` (default `9696`); the container still listens on `9696`.
4. Open the selected host address and published port over HTTP on a trusted network. Complete the first-run authentication prompt, select Forms authentication, set a unique username/password, and leave Authentication Required enabled for all addresses. Review Settings → General → Security before exposing access.
5. Configure indexers and optional application synchronization in the application. Follow the [upstream quick-start guide](https://wiki.servarr.com/prowlarr/quick-start-guide) and [authentication settings](https://wiki.servarr.com/prowlarr/settings#security).

No password or API key is supplied by this manifest. Nex login does not authenticate requests to this application's web UI. Treat its API key as a credential and protect configuration backups. HTTP is published directly; provide trusted TLS termination before remote access.

## Storage and permissions

- `CONFIG` → `/config`: settings, database, API keys and credentials; keep persistent and back it up.

Prowlarr stores indexer definitions, application API keys and settings in `/config`. It needs no media or download mapping: synchronization is over HTTP APIs. Configure a reachable application URL and its API key under Settings → Apps, and test the connection; separate Nex applications do not share a private service-name network. Download clients are optional for searches submitted directly from Prowlarr; they are not included here.

Both the mapped directories and imported files need ownership or ACLs that permit the chosen PUID/PGID to read and write them. Nex may create folders as root; choosing a UID/GID does not itself change share-side permissions. Have the storage administrator grant only the required access, then confirm the app can save settings and, where applicable, import a file. Do not use world-writable permissions as a shortcut. NAS UID mapping and ACLs must also allow access. See [LinuxServer's UID/GID guidance](https://docs.linuxserver.io/general/understanding-puid-and-pgid/).

## Limits and recovery

- One replica, non-scalable: never start two writers against the same configuration database.
- No download client, VPN, host networking, host paths, Docker socket, extra privileges or device access is requested.
- No resource cap is set by this package; size the host for the workload.
- Stop the app before copying its configuration/database for a consistent manual backup. Back up configuration including credentials; a configuration export alone is not a full recovery test.
- Update by replacing the pinned container image through the catalogue workflow; do not use an in-container updater. Preserve data, review upstream changes and test recovery before accepting an update.

## Image provenance and licenses

Exact image reference:

```text
ghcr.io/linuxserver/prowlarr:2.7.0.5723-ls168@sha256:6660787a99b2e58203539583663c973b48979fc00ff2cb78dc0ea17429e1f6ef
```

The versioned tag is published in the [LinuxServer release](https://github.com/linuxserver/docker-prowlarr/releases/tag/2.7.0.5723-ls168). The anonymous [GHCR manifest endpoint](https://ghcr.io/v2/linuxserver/prowlarr/manifests/2.7.0.5723-ls168) was fetched using a registry pull token; its `Docker-Content-Digest` matched the SHA-256 of the returned index bytes. The index includes Linux `amd64` and `arm64` manifests (and attestation entries). The manifest pins that index digest, not a floating channel. This verifies registry publication, not a container boot or a supply-chain audit.

- [Prowlarr source](https://github.com/Prowlarr/Prowlarr) and [upstream GPL v3 license](https://github.com/Prowlarr/Prowlarr/blob/develop/LICENSE). `license: GPL-3.0` describes the upstream application; bundled components retain their own licenses.
- [LinuxServer container source](https://github.com/linuxserver/docker-prowlarr), [container license](https://github.com/linuxserver/docker-prowlarr/blob/master/LICENSE), and [image configuration documentation](https://docs.linuxserver.io/images/docker-prowlarr/).
- `nex.yaml`, this README and `icon.svg` are original catalogue work licensed **AGPL-3.0-only**. The colorful icon is an original, unofficial illustration, not upstream artwork or an official logo. No upstream artwork is bundled.

## Nex integration

API impact: **existing contract** — Core parses this Compose package, infers its settings/storage/port questions, and renders the deployment through the existing application install contract; no endpoint or behavior changes.

Guide impact: **updated** — this README documents package setup, authentication, storage, limits and unrun verification. Durable application settings and storage mappings use Core's existing cluster-master application record and inventory/adoption path; this package adds no Controller-owned state.

## Checks performed

Core's actual `apps.Parse`, `ValidateCatalogue` and `Render` accepted this file in a temporary Go harness. Checks passed for host storage, default and edited web ports, default and edited PUID/PGID/TZ, rejection of two replicas, and rejection of missing storage. SVG XML parsing and static checks for disallowed service settings, license markers and whitespace also passed. These are format/render checks; no native container or Nex lab workflow was run.
