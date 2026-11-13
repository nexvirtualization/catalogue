<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SABnzbd

Standalone Usenet downloader with repair and unpacking, curated for Nex's existing application package format. Runs one copy; scaling is disabled. A Usenet provider and its credentials are required; none are supplied in this package.

## Configuration and first sign-in

1. Choose settings (`CONFIG`, mounted at `/config`) and download/unpacking (`DATA`, mounted at `/data`) storage. With **This host** storage, choose exactly one host; that storage has no automatic failover.
2. Keep or edit numeric file ownership defaults `PUID=1000`, `PGID=1000`, and IANA time zone `TZ=Etc/UTC`. Both folders must be writable by that UID/GID. On NFS/SMB, arrange share-side ownership and ACLs; root squash may prevent the image from fixing ownership at startup. Correct the selected folders' write permissions rather than granting world write access.
3. From a trusted network, open `http://<host-address>:8081` (or the chosen published port). The default mapping is **external TCP 8081 → container TCP 8080**; leave SABnzbd's internal HTTP port at `8080`.
4. Complete SABnzbd's setup wizard with the provider's address and credentials, enabling provider TLS with certificate verification. In **Config → General**, set a strong username/password and require login for local as well as remote UI access. Nex sign-in is separate. Do not expose the unconfigured wizard publicly; no preset login is shipped here.
5. In **Config → Folders**, place temporary downloads under `/data/incomplete` and completed downloads under `/data/complete`. Keep category output folders beneath `/data` too. The image's optional `/downloads` and `/incomplete-downloads` paths are not mounted by this package; explicitly change the app's folder settings.

If first access by DNS name is refused, use the host's numeric address to reach setup, then add only the intended DNS hostname to **Config → Special → `host_whitelist`** and save/restart as required. Do not use wildcard allowlists or turn off hostname verification. Keep API-key checking enabled, retain the generated API/NZB keys as secrets, and grant external access only as needed. Do not bypass authentication for local ranges. For remote UI access, arrange a separately secured HTTPS endpoint; this package publishes HTTP only.

## Storage and limits

`/config` persists provider credentials, API keys, configuration, queue and history. Protect that folder and its backups. `/data` holds downloaded articles and extracted files; allow additional free space for incomplete jobs, PAR repair and unpacking, potentially several times a job's final size. Configure minimum free space and job/connection limits in SABnzbd. Repair/unpacking can use substantial CPU and RAM; the package declares no per-app CPU, memory or disk quota.

Pause downloads and stop the app for a consistent backup of configuration and payloads. Preserve both folders when moving or recovering the app. An unavailable share or permission error is not repaired by changing download paths to unmounted container directories; correct storage access first.

Nex allocates a private folder for each storage row by default. To integrate separately installed
apps, select the same NFS/SMB share and the same **Existing folder on the share** for their DATA
rows, with compatible permissions and identical `/data` paths. Selecting the share alone does not
share the default folders. Keep every CONFIG folder separate; never share configuration databases.
Remote path mappings translate names but cannot mount missing files. Use **arr-suite** to share DATA
within one installation. Native share permissions and locking remain untested.

Only the HTTP port is published. Outbound access to the configured Usenet provider is needed. No socket, device, privileged mode, host paths, host networking or startup dependencies are requested. Multiple writers or extra replicas are unsupported.

## Provenance and licensing

- [SABnzbd upstream source](https://github.com/sabnzbd/sabnzbd/tree/5.1.3) and [license](https://github.com/sabnzbd/sabnzbd/blob/5.1.3/LICENSE.txt): GPL-2.0-or-later. Bundled utilities retain their own licenses.
- [LinuxServer image documentation](https://docs.linuxserver.io/images/docker-sabnzbd/) and [build source/license](https://github.com/linuxserver/docker-sabnzbd): LinuxServer's separate recipe is GPL-3.0 licensed.
- [Published build tag](https://hub.docker.com/r/linuxserver/sabnzbd/tags?name=5.1.3-ls281) and [GHCR package](https://github.com/linuxserver/docker-sabnzbd/pkgs/container/sabnzbd).
- [Authentication and ports](https://sabnzbd.org/wiki/configuration/5.1/general), [hostname allowlist](https://sabnzbd.org/wiki/extra/hostname-check.html) and [folder configuration](https://sabnzbd.org/wiki/configuration/5.1/folders).
- Exact image: `ghcr.io/linuxserver/sabnzbd:5.1.3-ls281@sha256:b356d0a9b22db584e9005364ec4e752dfc081ce501b7145e9a5c0bb38e4d1ba4`.
- Original manifest, README and `icon.svg`: **AGPL-3.0-only**. The icon is an original geometric illustration, not official upstream artwork or branding; no upstream artwork was copied. Referencing an image does not relicense or redistribute its contents.

## Verification and acceptance

Docker Hub's primary tags API listed the pinned build. An anonymous GHCR registry manifest GET returned HTTP 200; its `Docker-Content-Digest` and SHA-256 of the response bytes both matched the pinned digest. The index contains Linux amd64 and arm64 manifests. This establishes publication and pin identity, not runtime operation or image security.

Core source checks passed using `go test -overlay <temporary-overlay.json> ./internal/apps -v`: the existing package tests plus temporary checks against this manifest exercised Parse, ValidateCatalogue, default answers, storage rendering, published ports and rejection of two replicas. The default external 8081 to internal 8080 mapping was checked. The overlay was temporary and is not a committed test. SVG XML, square dimensions, whitespace and a manual private-identifier scan passed. These are static/source checks, not container tests.

Native Nex lab installation, initial wizard/allowlist/authentication, provider connection, downloading, repair/unpacking, writable-share behavior, restarts, backup/restore and Controller replacement are **unrun**; acceptance remains open. No runtime success is claimed.

API impact: **existing contract** — uses Core's package parsing, `apps-describe`, `app-install` and render/storage flow with no API changes. Guide impact: **updated** — this README supplies package-specific setup and limits. Settings persist in Core's existing cluster application record; app data lives in the chosen volumes/shares, with no Controller-owned state added.
