<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# qBittorrent

Standalone BitTorrent client, curated for Nex's existing application package format. Runs one copy; scaling is disabled. This package is not a VPN or an integrated media automation stack.

## Configuration and first sign-in

1. Choose settings (`CONFIG`, mounted at `/config`) and downloads (`DATA`, mounted at `/data`) storage in Nex. With **This host** storage, select exactly one host; it has no automatic storage failover.
2. Set the numeric file owner/group (`PUID=1000`, `PGID=1000`) and IANA time zone (`TZ=Etc/UTC`), or keep those editable defaults. Both folders must allow writes by that UID/GID. For NFS/SMB, arrange ownership and ACLs on the share; root squash can prevent startup ownership changes. Fix the selected folders' permissions rather than using world-writable permissions.
3. Keep web port `8080` or select a free port. Open `http://<host-address>:<web-port>` from a trusted network. The same setting controls the published port, target port and `WEBUI_PORT`; changing it keeps all three equal as LinuxServer requires.
4. Read the application's startup logs for the temporary password for user `admin`. Sign in and immediately set a strong persistent password under the Web UI settings. Treat the startup logs as sensitive. If no permanent password is saved, a restart may generate another temporary one.
5. In qBittorrent's download settings, set the default save path to `/data/downloads` and, if enabled, incomplete downloads to `/data/incomplete`. These paths are application settings, not environment defaults supplied by this package. Avoid `/downloads`, which is not mounted here.

Keep CSRF protection, host-header validation and authentication enabled, including for local clients. If using a DNS name, configure only the intended server domain in the Web UI settings. Nex sign-in does not authenticate qBittorrent. Keep HTTP on a trusted network; use a separately secured HTTPS endpoint for remote administration.

## Storage and limits

`/config` holds configuration, authentication and torrent resume state; `/data` holds payloads. Back up both for recovery, and stop the app for a consistent configuration copy. Downloads may fill the chosen storage; set download/queue limits in qBittorrent and monitor free space. No per-app CPU, memory or disk quota is declared by this package.

Nex allocates a private folder for each storage row by default. To integrate separately installed
apps, select the same NFS/SMB share and the same **Existing folder on the share** for their DATA
rows, with compatible permissions and identical `/data` paths. Selecting the share alone does not
share the default folders. Keep every CONFIG folder separate; never share configuration databases.
Remote path mappings translate names but cannot mount missing files. Use **arr-suite** to share DATA
within one installation. Native share permissions and locking remain untested.

Only the TCP peer port is published (`6881` by default). The peer setting controls the published port, target port and `TORRENTING_PORT` together; keep random-on-start peer ports disabled. Any router forwarding must match the selected peer port. TCP peers work without published UDP, but inbound UDP/uTP and DHT reachability are limited; no full UDP capability is claimed.

Core currently rejects duplicate published port numbers even across TCP and UDP. Adding UDP `6881` under Advanced alongside TCP `6881` therefore fails validation. Publishing UDP on a different external number is not equivalent to a correctly advertised shared peer port and is not a supported workaround. Full same-number TCP/UDP support needs a Core contract/validation change first. No host networking, device, socket or privileged access is requested.

## Provenance and licensing

- [qBittorrent upstream source](https://github.com/qbittorrent/qBittorrent/tree/release-5.3.0) and [license declaration](https://github.com/qbittorrent/qBittorrent/blob/release-5.3.0/COPYING): source GPL-2.0-or-later, binary GPL-3.0-or-later with the upstream OpenSSL exception. The manifest identifies the binary license; bundled components keep their licenses.
- [LinuxServer image documentation](https://docs.linuxserver.io/images/docker-qbittorrent/) and [build source/license](https://github.com/linuxserver/docker-qbittorrent): LinuxServer's separate image recipe is GPL-3.0 licensed.
- [Published build tag](https://hub.docker.com/r/linuxserver/qbittorrent/tags?name=5.3.0_v2.1.2-ls487) and [GHCR package](https://github.com/linuxserver/docker-qbittorrent/pkgs/container/qbittorrent).
- Exact image: `ghcr.io/linuxserver/qbittorrent:5.3.0_v2.1.2-ls487@sha256:3d4c4545d51a690a0df15a2ff99038823a88a9822df8e794526447b9afbd7384`.
- Original manifest, README and `icon.svg`: **AGPL-3.0-only**. The icon is an original geometric illustration, not official upstream artwork or branding. No upstream artwork was copied. Referencing an image does not relicense or redistribute its contents.

## Verification and acceptance

The published tag was observed in Docker Hub's primary tags API. An anonymous GHCR registry manifest GET returned HTTP 200; its `Docker-Content-Digest` and SHA-256 of the returned bytes both matched the pinned digest. The index contains Linux amd64 and arm64 manifests. This verifies publication and pin identity, not runtime operation or image security.

Core source checks passed using `go test -overlay <temporary-overlay.json> ./internal/apps -v`: the existing package tests plus temporary checks against this manifest exercised Parse, ValidateCatalogue, default answers, storage rendering, published ports and rejection of two replicas. Custom web/peer port matching and Core's rejection of same-number TCP/UDP publishing were also checked. The overlay was temporary and is not a committed test. SVG XML, square dimensions, whitespace and a manual private-identifier scan passed. These are static/source checks, not container tests.

Native Nex lab installation, browser sign-in, download/seeding, writable-share behavior, restarts, backup/restore and Controller replacement are **unrun**; acceptance remains open. No runtime success is claimed.

API impact: **existing contract** — uses Core's package parsing, `apps-describe`, `app-install` and render/storage flow without API changes. Guide impact: **updated** — this README supplies package-specific setup and limits. Durable application settings belong to Core's existing cluster application record and application data to the chosen volumes/shares; no Controller-owned state is added.
