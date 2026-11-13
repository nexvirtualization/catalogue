# Native lab acceptance

All native checks below are **unrun**. Use explicitly selected disposable resources; this repository
performs no deployment, disk operations or host reboots. Record package commit/digest, Nex build,
anonymous environment description, method and observed results before adding IDs to `tested.txt`.

1. Install Arr Suite through the documented custom-app or signed-source workflow. Confirm seven
   single-copy services, expected images/ports, and no VM networking interruption.
2. Complete first-run authentication for all web pages. Confirm anonymous access is refused after
   setup; verify valid/invalid API keys and hostname/CSRF protection.
3. Confirm each settings mapping is private and persists through service restart. Confirm all six
   data consumers see one `/data` tree. Check UID/GID writes and permission-denied behavior.
4. With authorized sample content, test torrent and Usenet downloads, completed-download imports,
   Prowlarr indexer synchronization, Bazarr subtitle writes, and actual hardlinks/atomic moves.
5. Retry an interrupted install/update and confirm no duplicate writable service instances. Test a
   stop-first update and rollback without concurrent configuration-database writers.
6. Disconnect/replace Controller and verify workloads continue and installed settings are adopted
   from Core without re-entry. Confirm client timeouts do not trigger duplicate deployments.
7. Separately test supported NFS/SMB permissions, database locking, storage interruption and host
   failure before considering share-based failover accepted. Local storage stays host-bound.
8. Stop services, copy configuration and data, and restore onto disposable storage. Verify settings,
   credentials, queue state and media integrity. Snapshot or successful copy alone is insufficient.
9. For signed sources, reject a tampered index and retain the last verified catalogue. Confirm an
   unsigned bundle and wrong public key fail without replacing the verified copy.

Format/render checks are simulated validation, not evidence these native workflows ran.
