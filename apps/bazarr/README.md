<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Bazarr

Find and download subtitles on web port **6767** (editable during installation).
Bazarr requires Sonarr or Radarr to supply its library inventory. This standalone
package includes neither; without a compatible external instance and matching
local media files, it is a configuration shell, not a working subtitle workflow.
Use matching existing share folders for separately installed Nex apps, or the combined `arr-suite` package.

## Setup and authentication

1. Select settings and media storage and review permissions below. Place the matching
   media library under `/data/tv` and/or `/data/movies` in the selected data folder.
2. Open the selected host's HTTP address and published port on a trusted network.
   In Bazarr's General settings, enable authentication and set your own username and
   strong password before widening access. Nex Controller login does not protect
   Bazarr. Keep Bazarr's API key and provider credentials private.
3. Enable an external Sonarr and/or Radarr in Bazarr settings. Enter its reachable
   address, port and API key, then use its Test control. `localhost` refers to the
   Bazarr container, not the other service. No cross-package service DNS is assumed.
4. If the external instance reports different paths, map its library root to
   `/data/tv` or `/data/movies` as appropriate. The actual corresponding files must
   already exist there. For separately installed Nex Sonarr/Radarr, select the same
   existing DATA folder on the same share; a path mapping alone does not mount files.
5. Select subtitle providers and supply any required accounts, configure languages
   and language profiles, assign profiles to media, then save. Provider account
   requirements, quotas and fees are outside this package.

Bazarr must read video files and write subtitles into their directories (or a
configured subtitle destination under `/data`). A read-only media folder prevents
normal subtitle saving. This package does not download films or television,
synchronize media from other apps, or provision provider credentials. Use catalogue
image updates rather than an in-app updater to preserve the pinned installation.

## Storage and permissions

Choose separate persistent storage for `CONFIG` (`/config`) and `DATA` (`/data`).
Prefer **This host** for `/config`: it holds the database, settings and credentials.
Back up both folders; a replacement container alone does not restore them. Stop the
application before a file-level database backup. A restore has not been lab-tested.
Host-local storage pins the app to one host; it does not provide automatic failover.

`PUID` and `PGID` default to `1000`; `TZ` defaults to `Etc/UTC`. All are editable.
Make both selected folders writable by that numeric user or group. On a share,
set the ownership/ACL on the storage server and check effective write access;
matching names alone do not establish permissions. Do not solve access failures
with world-writable permissions. LinuxServer initialization may need to set ownership;
share export restrictions can prevent this. Inspect the application logs if startup
or imports fail. Nex does not promise to repair storage-server permissions.

Nex allocates a private folder for each storage row by default. To integrate separately installed
apps, select the same NFS/SMB share and the same **Existing folder on the share** for their DATA
rows, with compatible permissions and identical `/data` paths. Selecting the share alone does not
share the default folders. Keep every CONFIG folder separate; never share configuration databases.
Remote path mappings translate names but cannot mount missing files. Use **arr-suite** to share DATA
within one installation. Native share permissions and locking remain untested.

## Limits and verification

One replica only; not scalable. No host paths, Docker socket, devices, privileged
mode, host networking or service dependencies are requested. The manifest does
not install companion applications. Published HTTP traffic is not encrypted by
this package; use a trusted network or an authenticated HTTPS gateway.

Checked against Nex Core's actual Compose parser, catalogue validation and renderer.
Registry manifest retrieval verifies publication, digest and architecture metadata;
it does not establish that the application starts. Native Nex lab installation,
login, permissions, media processing, restart, update and backup/restore tests
are **unrun**. This package must remain listed as untested until those checks run.

API impact: **existing contract** — uses Core's existing package inference,
`app-install`/`app-update`, storage choices and inventory; no API change.
Guide impact: **updated** — this README documents setup and limitations.
State owner: **Core** — Core retains the installed package and settings in the
cluster master's application record and reports them through inventory for a new
Controller; application data remains in the selected persistent folders.

## Package artwork and licensing

`nex.yaml`, this README and `icon.svg` are original Nex catalogue work licensed
**AGPL-3.0-only**. The colorful icon was drawn from simple geometric shapes for
this package; it is original, unofficial artwork, not an upstream logo or endorsement.
No upstream artwork or screenshots are included. The application and LinuxServer
build sources retain their own licenses; the image includes separately licensed
components and is not relicensed by this manifest.

## Upstream and image provenance

Maintenance checked **2026-11-13**: upstream and LinuxServer repositories were not
archived and both had source activity on that date. Upstream stable release
`v1.6.2` was published 2026-09-26; LinuxServer release `v1.6.2-ls372` was published
2026-11-11.

Pinned image:

```text
lscr.io/linuxserver/bazarr:v1.6.2-ls372@sha256:832820dec70bce9e912c6eee7a95baf6551e03dbc63325a7208daaa455423752
```

The authenticated public registry manifest GET returned that digest, independently
matched by hashing the response body. Its index includes `linux/amd64` and
`linux/arm64` image manifests plus attestation entries; the index digest preserves
multi-architecture selection. No image was pulled or executed.

- [Bazarr project and source](https://github.com/morpheus65535/bazarr)
- [Pinned upstream release](https://github.com/morpheus65535/bazarr/releases/tag/v1.6.2)
- [Upstream GPL v3 license](https://github.com/morpheus65535/bazarr/blob/v1.6.2/LICENSE)
- [Official setup guide: connections, paths, providers and languages](https://wiki.bazarr.media/Getting-Started/Setup-Guide/)
- [LinuxServer image documentation: ports, configuration and permissions](https://docs.linuxserver.io/images/docker-bazarr/)
- [Pinned LinuxServer release and build source](https://github.com/linuxserver/docker-bazarr/releases/tag/v1.6.2-ls372)
- [LinuxServer build license](https://github.com/linuxserver/docker-bazarr/blob/v1.6.2-ls372/LICENSE)
- [Published registry manifest](https://lscr.io/v2/linuxserver/bazarr/manifests/v1.6.2-ls372) (registry pull-token authentication required)
