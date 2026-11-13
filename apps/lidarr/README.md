<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Lidarr

Manage a music library with a standalone Lidarr instance on web port **8686**
(editable during installation). This package supplies Lidarr only, with no download
client, indexer or media server.

## Setup and authentication

1. Select settings and data storage and review the numeric user/group permissions below.
2. Open the selected host's HTTP address and published port on a trusted network.
3. Complete Lidarr's authentication setup; choose a password-protected method and
   require authentication for all addresses. Set your own username and strong password.
   Nex Controller login does not authenticate the Lidarr web interface. Keep its API key private.
4. Create `music` and `downloads` inside the selected data folder through your storage
   management tools. Add `/data/music` as the music root in Lidarr. Stage existing music
   or completed downloads in this app's own data folder and import them in Lidarr.
5. Configure metadata, quality profiles and any external indexer/download-client
   connections in Lidarr itself. A downloader's completed-file path must resolve to
   files actually present under this app's `/data/downloads`; a remote path mapping
   cannot provide missing file access. For a separate Nex downloader, explicitly select
   the same existing DATA folder on the same share in both applications.

Keep library and staged downloads under the single `/data` mount. Hardlinks and
atomic moves require the same underlying filesystem and suitable permissions;
this package does not guarantee them across mounts. Use catalogue image updates
rather than an application's built-in updater to preserve the pinned installation.

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
archived. Upstream stable release `v3.1.6.5079` was published 2026-10-26; LinuxServer
release `3.1.6.5079-ls48` was published 2026-11-11.

Pinned image:

```text
lscr.io/linuxserver/lidarr:3.1.6.5079-ls48@sha256:a91ef0642c15c9bd7c4260fee98fa99972c61601e37c8a96411d6a9cf0e9ad40
```

The authenticated public registry manifest GET returned that digest, independently
matched by hashing the response body. Its index includes `linux/amd64` and
`linux/arm64` image manifests plus attestation entries; the index digest preserves
multi-architecture selection. No image was pulled or executed.

- [Lidarr project and source](https://github.com/Lidarr/Lidarr)
- [Pinned upstream release](https://github.com/Lidarr/Lidarr/releases/tag/v3.1.6.5079)
- [Upstream GPL v3 license](https://github.com/Lidarr/Lidarr/blob/v3.1.6.5079/LICENSE.md)
- [Lidarr setup and settings](https://wiki.servarr.com/lidarr)
- [LinuxServer image documentation: configuration, permissions and media paths](https://docs.linuxserver.io/images/docker-lidarr/)
- [Pinned LinuxServer release and build source](https://github.com/linuxserver/docker-lidarr/releases/tag/3.1.6.5079-ls48)
- [LinuxServer build license](https://github.com/linuxserver/docker-lidarr/blob/3.1.6.5079-ls48/LICENSE)
- [Published registry manifest](https://lscr.io/v2/linuxserver/lidarr/manifests/3.1.6.5079-ls48) (registry pull-token authentication required)
