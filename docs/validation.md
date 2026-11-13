# Catalogue validation evidence

Checks executed against the initial eight-package working tree, using a development Nex source
checkout with the Applications parser/renderer, Python 3.12-compatible scripts, OpenSSL 3 and
Docker Compose. These are local source/configuration checks, not a native Nex installation.

- `python3 scripts/validate.py --core ../nex`: passed for all eight packages, including Core
  Parse, ValidateCatalogue, Check and Render; rejected multiple replicas and missing storage.
- `python3 -m unittest discover -s tests`: seven tests passed, covering all packages, rejection
  of unsafe edits, suite data/configuration separation and image parity, signed-bundle roundtrip,
  tamper rejection and repository privacy checks.
- `docker compose -f <each package>/nex.yaml config --quiet`, with generated validation-only
  storage answers and default ports/environment: all eight configurations passed. This did not
  start containers or exercise Swarm scheduling.
- Versioned image manifest indexes were fetched from their registries by the package curators;
  digest bytes matched recorded references, with amd64 and arm64 entries. Per-package READMEs
  retain primary provenance URLs. Registry availability does not prove container startup.
- Nex's own repository privacy unittest suite passed. Its documentation worktree checker found
  no Nex source changes; it does not validate this separate catalogue repository.

The public catalogue's own privacy tests are copied from Nex and run in catalogue CI. They
supplement manual inspection, and do not certify absence of every possible private identifier.

Native setup, authentication, real downloads/imports, NAS permissions/locking, host failures,
Controller outage/replacement, updates and restore integrity remain **unrun**. Use the
[lab checklist](lab-acceptance.md); `tested.txt` contains no accepted packages.

API impact: **existing contract** — existing package/settings/install/report and signed catalogue
contracts only. Guide impact: **updated** through root and package READMEs. Runtime durable state
remains Core-owned in the master's application record and inventory/adoption flow.

Independent read-only source review verified image digests and actual Core bundle verification,
including tamper refusal and last-verified-copy retention. Its one P2 finding about shared-folder
guidance was corrected against Core appsSharePath and the wizard: separate apps can explicitly
choose the same existing folder on the same share. Configuration databases stay separate.
The correction was checked locally; no second independent review is claimed.
