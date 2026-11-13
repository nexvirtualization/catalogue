<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Arr Suite

Radarr, Sonarr, Prowlarr, Lidarr, Bazarr, qBittorrent and SABnzbd in one Nex application.
The suite shares one data mapping across its services, with seven separate configuration mappings.
Each service runs one copy. All images reuse the exact version and registry digest documented
in the corresponding standalone package; those READMEs retain upstream license and provenance links.

## Status

Development package for disposable lab testing. Native installation, downloads/imports, database
locking, upgrades, host failover and Controller replacement are **unrun**. No tested badge is claimed.
[Readarr is excluded because the upstream project is retired](https://github.com/Readarr/Readarr#announcement-retirement-of-readarr). This package supplies media management,
subtitles, indexers and two alternative download clients; it does not include a media player/server,
VPN, request portal, credentials, indexer subscriptions or Usenet service.

## Prerequisites

Use a Nex Core development build with Applications, administrator access, and a disposable host
with room for seven services and their images. Begin with **This host** for all eight storage
choices and exactly one selected host. This keeps SQLite configuration databases on local storage.
NFS/SMB database locking and permissions require separate native testing; this package does not
claim share-based failover is safe. Prepare folders writable by the chosen numeric PUID/PGID
(default `1000:1000`); Nex creating a folder does not grant that UID access. Do not solve permissions
by granting everyone write access. Publish these HTTP pages only on a trusted network while setting up.

## Steps

1. In **Applications**, select the cluster → **Catalogue** → **Arr Suite** → **Install** once a
   signed bundle is available. Alternatively use **Add your own** and paste `nex.yaml`; the custom
   workflow does not verify this repository's catalogue signature.
2. Select exactly one host. Place each service's settings in its own storage row, and select the
   shared media/downloads row once. Keep PUID/PGID consistent across services. Set `TZ` as needed.
3. Keep the ports below or choose unused published ports. qBittorrent's web/peer target ports
   change with their published ports. Other services retain their fixed internal ports.
4. Install, open each service's page using the host's address, complete its first-run setup and
   enable authentication for all addresses. Radarr/Sonarr/Lidarr/Prowlarr require authentication;
   Bazarr authentication must also be enabled. qBittorrent's initial `admin` password is generated
   in its startup logs: retrieve it through the service logs and change it immediately. SABnzbd
   requires provider setup and a username/password. Keep API keys private. Nex login does not
   protect these pages. Retain CSRF and host-header protection; add only the actual names used to
   connect if SABnzbd rejects a hostname. Use trusted TLS termination for remote access.
5. In the download clients, set incomplete/completed folders under `/data/torrents` and
   `/data/usenet`, respectively; create the folders through the clients' folder settings as needed.
   In Radarr use `/data/movies`, Sonarr `/data/tv`, Lidarr `/data/music`. Keep library roots separate
   from download roots. Configure categories such as `radarr`, `sonarr`, `lidarr` on each client.
6. Connect Radarr, Sonarr and Lidarr to either or both download clients using service DNS names
   `qbittorrent` and `sabnzbd`, their **internal** ports and credentials/API keys. For SABnzbd,
   add `sabnzbd` to its allowed hostnames if needed without disabling validation. Enable completed
   download handling. Paths are identical under `/data` so remote path mappings are unnecessary.
7. Configure indexers in Prowlarr and add Radarr, Sonarr and Lidarr as applications with their
   service DNS names, internal ports and API keys. Set Prowlarr's application-facing address to
   `http://prowlarr:9696`. Use Test in each application before saving.
8. Connect Bazarr to `radarr:7878` and `sonarr:8989` with API keys; configure subtitle providers and
   language profiles. Paths remain `/data/movies` and `/data/tv` in all three services.
9. Test a small authorized download, import and subtitle write; check file ownership, paths and
   hardlink behavior on the actual filesystem before using existing libraries.

| Service | Default published port | Internal port |
| --- | --- | --- |
| Radarr | 7878 | 7878 |
| Sonarr | 8989 | 8989 |
| Prowlarr | 9696 | 9696 |
| Lidarr | 8686 | 8686 |
| Bazarr | 6767 | 6767 |
| qBittorrent web | 8080 | `WEBUI_PORT` (8080 by default) |
| qBittorrent incoming peers | 6881 TCP | `TORRENTING_PORT` (6881 by default) |
| SABnzbd | 8081 | 8080 |

Use internal ports for service-to-service traffic. If editing qBittorrent's web port, use the
new internal port in download-client settings too. Core currently rejects publishing the same
number twice, including TCP and UDP; incoming UDP peers are therefore not published. Outbound
traffic is still available. No VPN or public-network privacy is supplied by this package.

## Expected result

Seven services run, each retains its own settings, and every media service/downloader sees the
same `/data`. Prowlarr has configuration only. Imports use the client's reported path directly.
Hardlinks and atomic moves additionally require filesystem support and permissions; sharing a
mapping alone does not prove they work.

## Troubleshooting and recovery

- Authentication failure: verify the service's own credentials/API key, hostname allowlist and
  internal port. Never disable authentication, CSRF or hostname checks as a shortcut.
- Empty library or failed import: verify the download path and library root are under the single
  `/data` mapping, and the selected PUID/PGID can write. For a separate Nex app, explicitly select the same existing folder on the same share;
  a remote path mapping alone does not mount files.
- Port conflict: stop the conflicting standalone app or select a free published port in Nex.
- Database errors on a share: stop the application and return configuration to known-good local
  storage; do not assume a NAS supports the required SQLite locking semantics.
- Back up all seven configuration folders and the shared data with the services stopped for a
  consistent copy. Application backup/restore in Nex Recovery points is not implemented yet.
  Test manual restore on disposable storage before relying on it.
- Update through catalogue image changes, keeping one writer per service. Stop-first update and
  rollback are explicit; never scale these databases. Do not use in-container self-updaters.

## Verification and attribution

See the root [validation instructions](../../README.md#validation) and
[lab checklist](../../docs/lab-acceptance.md). Static and Core render checks are distinct from
native acceptance. Exact image references and upstream sources are in
[Radarr](../radarr/README.md), [Sonarr](../sonarr/README.md), [Prowlarr](../prowlarr/README.md),
[Lidarr](../lidarr/README.md), [Bazarr](../bazarr/README.md),
[qBittorrent](../qbittorrent/README.md) and [SABnzbd](../sabnzbd/README.md).

The manifest, documentation and colorful unofficial suite icon are original **AGPL-3.0-only**
work. Upstream applications and container components retain their own licenses; no binaries or
upstream artwork are redistributed here.

API impact: **existing contract**, using Core's existing package parser, settings validation and
application install/report flows. Guide impact: **updated**, through these instructions. Core
owns the installed application's durable settings and storage mappings in its cluster-master
application record, recovered through inventory/adoption; no Controller-owned state is added.
