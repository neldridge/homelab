# Overseerr to Seerr migration — bb9b, October 11, 2026

Installed official `ghcr.io/seerr-team/seerr:v3.5.0`, pinned to its **linux/amd64
manifest** `sha256:c33702abebcec295b69a1371417b3a350e31dfeacbae3158e790c86908dc3659`.
The release's multiarchitecture index is
`sha256:27602401178d54f1964442287b9f23f67a3fa2252645ee8065839ea1c3f69e45`;
the running platform config ID is
`sha256:c1673c6c7835e21540cacbf517abb7c4a80d2893b3484bec1b1a11212ac247fb`.
These three digests identify different registry objects.

Sources checked before changing deployment:

- https://docs.seerr.dev/migration-guide/
- https://docs.seerr.dev/getting-started/docker/
- https://docs.seerr.dev/using-seerr/backups/
- https://github.com/seerr-team/seerr/releases/tag/v3.5.0
- https://raw.githubusercontent.com/seerr-team/seerr/v3.5.0/server/lib/overseerrMerge.ts
- https://info.linuxserver.io/issues/2026-02-16-overseerr/

LinuxServer recommends the official image. Seerr documents automatic Overseerr
migration; v3.5.0 includes the schema adapter for the deployed Overseerr schema
(latest source migration `UpdateWebPush1740717744278`). Its release also fixes
leftover Overseerr deleted-media statuses. Compatibility was verified by the
successful migration of this exact `v1.35.0-ls159` deployment, rather than an
assumption about third-party image environment variables.

## Data and cutover

Only Overseerr was stopped before the consistent filesystem copy and archive.
The final copy passed SQLite integrity and foreign-key checks before Seerr
started. The new directory `/opt/data/homelab/config/seerr` is owned by
1000:1000, directories 0700/files 0600, mounted at `/app/config`. Official image
user `node` and `init: true` replace LinuxServer PUID/PGID and `/config`.
Seerr's automatic migration reported completion. Overseerr remains stopped;
its original directory `/opt/data/homelab/config/overseerr` is preserved.
Do not use `--remove-orphans` or start the old container alongside Seerr.

Private, root-only rollback bundle:
`/opt/data/homelab/rollback/overseerr-to-seerr-20261011T230937Z/`.
It contains `overseerr-config.tar.gz`, `archive.sha256`, original deployment and
monitoring files, private API-key mapping, baseline counts/container inventory,
cutover timestamps, and `rollback.sh`. Nothing in this bundle belongs in Git.
The original configuration matched the archive byte-for-byte after migration.

The final stop-to-verified-HTTPS upper bound was **82.2 seconds**. Nginx alone
was recreated to bind its updated configuration inode; both virtual hosts now
use `seerr:5055`. TCP 5055, existing HTTPS certificates, public URL
`https://requests.neldridge.net:3579` and internal URL
`https://overseerr.a3f.link` are preserved. No router changes were made.

## Verification

- SQLite integrity and foreign keys pass before and after migration.
- 28 users, 387 requests, 1,281 media records and 215 requested seasons preserved.
- Authenticated status, requests, users and integration settings APIs pass.
- Existing Plex administrator login, session authentication and request-history
  access pass through both HTTPS URLs with certificate validation and CSRF enabled.
- Seerr reads Sonarr/Radarr profiles and root folders through its configured
  connections. Configured Plex authenticated library access passes.
- Saved Plex/Sonarr/Radarr/Tautulli settings, client ID and web-push keys preserved.
  Official migration relocates trustProxy/CSRF fields to network settings.
- Seerr metrics and Docker logs reach Prometheus/Loki. Stable release inventory
  reports v3.5.0 current; the existing overview selector includes Seerr.
- Nine semantic APIs and all 31 dependency/DNS/TLS probes pass. Both independent
  heartbeat rules remain firing with health=ok. PagerDuty routing/grouping and
  resolve-message settings are unchanged, as is Kometa's review-only handling.
- Grafana dispatched OverseerrDeprecated resolve events at 23:13:11–12 UTC.
  After recovery, the obsolete rule was removed through provisioning deleteRules.
  No manual PagerDuty resolution or suppression was used.
- Twelve Python regression tests pass locally and on bb9b.
- Unrelated container images, start times and restart counts are unchanged.

Only Nginx and the affected monitoring Blackbox/Prometheus collectors were
recreated. Grafana provisioning was reloaded without restarting Grafana, Alloy,
Loki or Exportarr. No real requests/downloads were created, no unrelated backup
problems repaired, and no commits made. The application saved URL value was
preserved exactly; public port 3579 remains in the existing proxy redirect.

## Exact rollback

Run from an administrator terminal:

```sh
ssh neldridge@192.168.11.10
sudo bash /opt/data/homelab/rollback/overseerr-to-seerr-20261011T230937Z/rollback.sh
```

The syntax-checked script stops Seerr first, restores original Compose/proxy and
monitoring files plus the private key mapping, starts the retained original
Overseerr container, recreates only Nginx/Blackbox/Prometheus, refreshes observers,
reloads Grafana provisioning, and verifies Overseerr 1.35.0 at both URLs.
It has not been executed because that would undo the successful migration.

The old container uses the original image:
`docker.io/linuxserver/overseerr:v1.35.0-ls159@sha256:6108ed066d4a919c05251d9dab041c1e55e67ff7247e7b31be97b65ffcbaeeb1`
and original `/opt/data/homelab/config/overseerr:/config` bind. Neither the
script nor Overseerr touches the migrated Seerr database. Rollback returns to
the cutover state; subsequent Seerr activity remains only in its separate
configuration. Keep both directories and the archive intact.

If the retained container has been removed, after stopping Seerr and restoring
the files, recreate only Overseerr from the restored definition:

```sh
cd /opt/data/homelab/repo/compose
sudo docker compose -f compose.yaml -f compose.proxy.yaml up -d --no-deps overseerr
```

Never mount `config/seerr` into Overseerr. If the original directory is lost,
stop both applications and restore the private pre-migration archive into a
separate directory, validate it, and deliberately restore that Overseerr copy.
Do not overwrite or downgrade the migrated Seerr database.

Final follow-up: both external Healthchecks checks reported **up**, with fresh
pings at 23:16:42 UTC. The expected Nginx cutover log/event alerts returned
inactive/health=ok; Grafana sent their PagerDuty resolve events at 23:15:42 and
23:16:42 UTC. The complete original request fields and user identities/password
hashes/permissions/Plex credentials compare equal with Overseerr. All unrelated
container start times, image IDs and restart counts match the baseline.

Remaining verification limits: rollback was syntax-checked but not rehearsed;
PagerDuty resolve dispatch was observed in Grafana rather than independently
confirmed in PagerDuty's incident UI. The public URL and Plex login were tested
from bb9b through HTTPS, without a separate off-LAN vantage or browser visual QA.
Existing unrelated backup and update conditions remain actionable and untouched.
