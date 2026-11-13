# Arr suite curation

Scope: seven independently usable catalogue packages and one integrated Arr Suite for disposable
Nex lab testing. Use maintained Radarr, Sonarr, Prowlarr, Lidarr, Bazarr, qBittorrent and SABnzbd
images with version/digest pins, primary provenance links and original unofficial icons. Readarr
is excluded because its upstream project is retired. Request portals, media servers, VPNs and
application auto-configuration are outside this batch.

API impact: **existing contract**. Packages use Core's current Compose/x-nex parser, application
settings/install flow, inventory and signed format-1 catalogue. No Controller/Core or client API
changes. The combined suite uses one DATA variable to simplify installation; separate apps may
share data by selecting the same existing folder on the same share. Default allocated folders
remain private; configuration stays separate and single-copy for each service.

State owner: **core** for installed settings/storage mappings in the master's existing application
record and inventory/adoption flow. Catalogue source files add no new runtime state or authority.
Guide impact: **updated** via root/package READMEs and the native lab checklist.

Acceptance before publication: inspect all public files, validate packages with real Core and
Compose, run policy/bundle/privacy regressions, independent review and resolve findings. Keep
`tested.txt` empty until native authentication, imports, storage, interrupted operations and
Controller-disconnection/replacement scenarios in the lab checklist have actual evidence.
No signing identity, source hosting, live deployment or native acceptance is created by this work.
