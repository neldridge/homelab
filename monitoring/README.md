# R710 monitoring operations

Independent Compose project: `homelab-monitoring`. Run on bb9b from
`/opt/data/homelab/repo/monitoring` using the explicit private runtime file:

```sh
sudo docker compose --env-file /opt/data/homelab/monitoring/runtime.env -p homelab-monitoring config --quiet
sudo docker compose --env-file /opt/data/homelab/monitoring/runtime.env -p homelab-monitoring up -d
sudo docker compose --env-file /opt/data/homelab/monitoring/runtime.env -p homelab-monitoring ps
```

Grafana: https://grafana.a3f.link:3000/ on the LAN and
https://grafana.neldridge.net:3000/ externally. TLS terminates in Grafana;
port 3000 accepts HTTPS. Anonymous access and account signup are disabled.
Prometheus and Alloy have no published ports. Their HTTP traffic is confined
to the monitoring bridge. The media proxy and containers are independent.

Runtime state, certificates and secrets are under `/opt/data/homelab/monitoring/`,
outside this checkout. `runtime.env` is root-only (0600). It contains
`PAGERDUTY_ROUTING_KEY`, `HEALTHCHECKS_PING_URL`, generated
`GRAFANA_ADMIN_PASSWORD`, and `GRAFANA_SECRET_KEY`. `HEALTHCHECKS_API_KEY` is
optional for acceptance verification and is not passed to containers.
The initial Grafana account is `admin`; inspect the password privately on the
server with `sudo vim /opt/data/homelab/monitoring/runtime.env`. Do not print or
commit this file. Changing its admin password value does not reset an existing
Grafana database password; use Grafana account settings for subsequent changes.

Install `systemd/homelab-monitoring.service` in `/etc/systemd/system/` and enable
it. It requires Docker and the local `/opt/data` mount, with no NFS dependency.
Containers use `on-failure` so the unit controls boot startup. Use
`sudo systemctl stop homelab-monitoring` to stop the managed project.

Prometheus retains up to 14 days or 10 GiB of TSDB blocks, whichever comes first;
WAL/head data add overhead. Alloy's remote-write WAL retains at most one hour
of samples and truncates every 15 minutes. Docker logs are bounded to three
10 MiB files per container. Disk and inode alerts cover local ext4 filesystems.

Alloy reads host `/proc`, `/sys`, udev metadata and a read-only root filesystem
bind. This grants broad host file visibility inside the collector. It has no Docker socket or Docker API access. Phase 2 reads selected local
Docker JSON logs, application files and the host journal through read-only
mounts. Only selected host metric collectors run. NFS filesystem types and media mount paths are excluded to avoid
probing unavailable library storage. Local file paths are used explicitly; log collection never traverses the media mount.

The heartbeat evaluates every 30 seconds using successful, fresh Prometheus
self-scrapes and recent TSDB data. Grafana sends success POST notifications at
a 60-second repeat interval and 30-second group interval. Resolved notifications are disabled, and
DatasourceError/DatasourceNoData notifications route to PagerDuty before the
heartbeat route. Healthchecks must use a 60-second period and 60-second grace,
with its PagerDuty integration enabled for failure and recovery. The repeat interval
is a minimum rather than a precise scheduler; steady heartbeat gaps measured
about 90 seconds during acceptance testing. Recheck actual timing after upgrades.

Grafana routes workload notifications to PagerDuty Events API v2, grouped by
alert name and host so unrelated rules have separate incidents. Recovery events
are enabled to resolve the corresponding incident automatically. The unused
Pushover contact point remains available for rollback; no notification policy
routes to it. Its existing private credentials are retained.

For maintenance, create a time-bounded Grafana silence matching `scope=workload`
and `host=bb9b` at `/alerting/silences`. Do not create broad silences that match
`scope=heartbeat` or `scope=log-heartbeat`; those would suppress the external heartbeat. Grafana outages
still intentionally trigger Healthchecks even when workload alerts are silenced.

Certificates must cover both DNS names. Replace `tls/fullchain.pem` and
`tls/privkey.pem` privately (owner 472:0, mode 0640), then restart only Grafana.
The initial certificate expires January 9, 2027. Certificate renewal automation
is not installed; renew and deploy before expiration. Back up the runtime
folder separately, including Grafana's database and secret key.

After replacing a single-file bind source, recreate the affected container
with `up -d --no-deps --force-recreate SERVICE` to bind the new inode. Provisioned
alert and dashboard directories are mounted as directories and reload normally.


## Phase 2: service health and logs

The existing overview now includes authenticated API status, application warnings,
blocked/stuck imports, container state, Kometa completion/success/error summaries,
and a service-selectable Loki log panel. Status fields link directly to that
service's logs. PagerDuty messages include host/service labels, persistence
threshold, overview/log links, the Grafana rule, and a prefilled silence link.
The original HTTPS and PagerDuty routes remain in use; Pushover remains unused.

### Collection and privileges

Alloy reads Docker's existing bounded `json-file` logs using a generated list of
explicit paths. A host systemd timer refreshes that list every 30 seconds, so
container replacement is discovered without a Docker socket in Alloy. It also collects monitoring Loki/Grafana/Alloy/Prometheus container logs and
reads current Sonarr/Radarr/Prowlarr, Bazarr, Tautulli and Kometa application log
files and the system journal (including available kernel messages). New
application/Docker targets start at the end; this deployment does not backfill
historical logs. File positions persist in Alloy's local runtime directory.
Quiet services are valid and do not generate collector-failure alerts.

This is the smallest deployment addition: file readers plus a bounded host
check, without an extra privileged proxy daemon. It is **not** a security
boundary against host administrators or a compromised root collector: Alloy's
pre-existing read-only host root mount grants broad host file visibility. A
read-only Docker socket would still grant broad API access and is deliberately
not mounted. The root host check uses Docker inspect/events and reads existing
local application credentials. Root/Docker access is broad; it is kept on the
host rather than delegated to a new network-accessible container. Its unit has
NoNewPrivileges, a read-only system filesystem and a single writable runtime
root. Runtime secrets remain root-only outside Git. The Grafana and Exportarr
processes receive only the runtime values they use. Never print Compose's fully
interpolated configuration or inspect environment variables in shared output.

Standard Exportarr v2.3.0 instances cover Sonarr, Radarr, Prowlarr and Bazarr;
Loki 3.7.8 is pinned by registry digest. The custom `service_checks.py` is needed
for response semantics, per-item stuck-import age, installed Kometa summaries,
and Docker event snapshots that the standard exporters do not provide. It
makes bounded read-only HTTP requests with five-second timeouts and parallel
service checks; the unit has a 25-second overall timeout. Failure to finish
leaves the timestamp stale and alerts. It never changes application settings,
queues, playback or files. API credentials are copied to private
`app-keys.json` and `runtime.env`; refresh them privately after credential
rotation. Tautulli/Plex and NZBGet credentials are read from their local configs.

### Verified endpoint semantics

| Service/version | Check and healthy response |
|---|---|
| Sonarr 4.0.20.3014 | Authenticated `/api/v3/system/status` appName, `/health` array, `/queue` records |
| Radarr 6.4.4.10685 | Same v3 API semantics |
| Prowlarr 2.6.5.5623 | Authenticated v1 status/appName and health array |
| Bazarr 1.6.2 | Authenticated `/api/system/status` version and `/api/system/health` data array |
| Overseerr 1.35.0 | Authenticated `/api/v1/request?take=1` validates database-backed pageInfo/results |
| NZBGet 26.3 | Authenticated HTTP JSON-RPC on 6790: status has positive uptime and no RPC error; log(0,100) returns ID/Kind/Time/Text |
| Tautulli 2.18.2 | Authenticated get_activity returns response.result=success and sessions array |
| Nginx 1.30.5 | HTTPS `overseerr.a3f.link/api/v1/status` validates proxy/backend JSON, including version and restartRequired |
| Plex 1.43.4.10903-e5521bd8c | Authenticated `192.168.11.129:32400/library/sections` returns MediaContainer and at least one Directory |

Successful landing pages and running containers do not set API health. Plex's
check proves authentication and library metadata access, not playback/transcoding.
Nginx's check proves the selected TLS virtual host and Overseerr upstream, not
all virtual hosts. NZBGet's installed endpoint is HTTP on the LAN; monitoring
adds no public port or application configuration change.

### Alerts and bounds

- API unavailability persists 60 seconds before alerting. Host check freshness,
  Exportarr scrape health, Loki readiness/scrape health and query errors are
  monitored separately. Bazarr scrapes every 60 seconds with a 50-second timeout;
  the separate API check still runs every 30 seconds. Expensive optional Bazarr
  metrics are disabled for this pinned release.
- Servarr/Bazarr health warnings persist five minutes. These include reported
  download-client/indexer failures. Sonarr/Radarr importBlocked/importFailed/
  downloadFailed queue states persist two minutes. Pending/completed imports
  must remain individually unchanged for 30 minutes, then persist one minute.
  Tracking uses bounded queue records (first 1,000) and runtime state by item ID.
- NZBGet alerts on more than two ERROR records in ten minutes, from its bounded
  latest-100-message API window. Pauses/quota states are health warnings.
- Docker inspect reports running/restart count/OOM state. A two-minute bounded
  Docker event window captures die/restart/OOM events between snapshots; counters
  persist outside Git. Gaps longer than two minutes may miss events and the
  collector freshness alert is the indication to investigate that gap.
- More than five error/fatal/exception/OOM lines in five minutes, sustained one
  minute, alerts per service. Only media application/Docker streams participate; monitoring services are
  excluded so Loki query text cannot trigger its own error search.
  Ordinary Nginx access logs and empty streams do not imply collector failure.
  This is an initial conservative pattern, not a complete application-specific
  error taxonomy. Some applications log the same error to stdout and files;
  counts can include both. Filter known benign messages only after investigation.
- Kometa parses the actual final Finished timestamp and Error Summary counts.
  Installed 2.5.2 omits empty severity summaries; a completed run with no Error
  Summary is error-free unless report generation itself failed. Latest completion
  and last error-free completion are distinct. No retained successful run is
  shown explicitly; there is no invented success time. Kometa errors and missing error-free runs are review-only: they remain on
  the overview and in Loki, with no PagerDuty alerts. The recurring application
  error rule excludes Kometa. Review logs using the overview service selector
  (`kometa`, Logs panel). Only the final
  1 MiB of each bounded retained log is inspected.
- A roughly 70-byte canary is appended every 30 seconds and rotates at 1 MiB
  with one backup. Its original generation timestamp is used in Loki. A fresh
  canary proves the file source, processing, write, Loki storage and query path.
  No fresh canary within 90 seconds raises LogIngestionMissing after 30 seconds.
  Retry bursts and exhausted write retries also alert.
- A separate Grafana LogPipelineHeartbeat uses the canary query and its own
  Healthchecks check (60-second period, 60-second grace), with the existing
  PagerDuty integration. Error/no-data states stop successful pings and route
  to PagerDuty. Resolved notifications are disabled on both heartbeat contacts.
- Labels are limited to host, service and job (plus Loki's derived service_name).
  No filename/container ID/request ID/media title is indexed. Generic credential
  fields are redacted before shipping; arbitrary free-text secrets cannot be
  guaranteed absent. Lines over 8 KiB are dropped; rate is capped at five lines
  per second per service with a burst of ten. The canary has its own service
  budget. Source Docker logs retain three 10 MiB files per container.
- Loki compactor retention is seven days with a one-hour deletion delay. Its
  local ext4 loop filesystem has a **hard 16 GiB limit**, separate from the rest
  of /opt/data. Below 20% free alerts. Ingestion is additionally limited to
  0.1 MiB/s with a 1 MiB burst and 100 streams; rejected data raises pipeline
  failure alerts. Retention is an age target, not a promise of seven complete
  days under floods or collector outages. Loki memory is capped at 1 GiB.

The mount unit `opt-data-homelab-monitoring-loki.mount` uses the private runtime
`loki.ext4` file. The monitoring startup unit requires this local mount, Docker
and /opt/data; it has no Synology/NFS dependency. The separate checks timer must
also be enabled. Never format an existing Loki filesystem during routine setup.
The initial config backup and initial Loki files are private runtime rollback
artifacts, not tracked deployment files.

### Acceptance on 2026-10-11 (UTC)

Actual PagerDuty incidents were inspected in the signed-in UI, including
service labels, investigation links and integration-driven resolution. The
PagerDuty session expired before the final recovery inspection; the user then
confirmed in PagerDuty on their phone that all test incidents were resolved and
only the two real Kometa incidents remained open. Times below are Grafana
notification event timestamps, cross-checked against real PagerDuty incidents;
Healthchecks transitions come from its API, not inferred timer settings.

| Test | Fault | PagerDuty trigger | Recovery |
|---|---|---|---|
| Exportarr collector | 18:37:22, stop only Sonarr exporter | 18:39:13 (~111 s), incident #4 | Restore 18:39:50; resolve 18:40:43 (~53 s) |
| Authenticated API | 18:37:22, monitoring-only invalid Sonarr credential fixture | 18:39:19 (~117 s), incident #5 | Restore 18:39:50; resolve 18:40:49 (~59 s) |
| Synthetic log error | 18:43:20, one canary error line | 18:43:40 (~20 s), incident #8 | Window expires; resolve 18:44:40 |
| Loki outage | 18:44:21, stop only Loki | Query error 18:44:47 (~27 s), #9; readiness 18:45:46 (~85 s) | Restore 18:46:16; query resolve 18:46:47, readiness resolve 18:47:46 |
| Ingestion only, Loki healthy | 18:49:07, pause only canary generation | 18:51:15 (~129 s), LogIngestionMissing; Healthchecks down 18:51:09 (~122 s) | Restore 18:52:38; Healthchecks up 18:53:09 (~31 s); all test incidents resolved |
| Independent log heartbeat | Same Loki outage | Healthchecks down 18:45:39 (120 s after last successful ping, ~78 s after fault), #10 | Healthchecks up 18:48:05 (~109 s after restart); PagerDuty resolution checked |

The original metrics heartbeat stayed healthy throughout the Loki outage.
During initial deployment, transferred macOS metadata briefly blocked Grafana
provisioning; removing those generated files restored it and the existing
heartbeat incident resolved automatically. Subsequent transfers exclude
metadata, and rule/dashboard changes use Grafana's reload API.

Six isolated tests validate response schemas (a 200 landing response fails),
Kometa success/error/unknown summaries, and Docker OOM/restart/exit fixtures.
No media application was stopped or restarted for acceptance. OOM and import
failures are covered with fixtures and live schemas, not destructive media tests.
Seven-day deletion and boot persistence are configured/validated, not tested by
waiting seven days or rebooting the active server. Certificate renewal, NAS/NFS
reliability, release tracking and later phases remain outside this scope.


Final verification: all nine semantic API checks and four Exportarr scrapes
healthy; canaries present; Loki ready; both Grafana HTTPS names returned 200 with
database=ok and valid certificates. Compose, Alloy, promtool, Loki config
verification, systemd verification and six isolated tests passed on the R710.
The local Loki filesystem is mounted at 16 GiB. Startup service, local mount
unit and checks timer are enabled. Runtime credential files are 0600. No test
fault markers remain. Media containers retained their original running uptime
and images. Nothing was committed.

To repeat the bounded tests, use monitoring-side faults only: stop/start one
Exportarr container; briefly create/remove `fault-sonarr` in the private runtime
root (the checker substitutes an invalid credential only for its own requests);
append a single JSON canary message `synthetic_monitoring_error` with a current
Unix `timestamp`; stop/start only Loki; or create/remove `canary-paused` to pause
only synthetic generation. Always remove fixtures, verify both Healthchecks
checks return to up and verify PagerDuty resolution. These tests intentionally
notify PagerDuty; do not run them during unrelated incidents. Never stop media
applications, unmount media storage or change queues to validate monitoring.

## Phase 3: storage and dependencies (partial; NAS access pending)

NAS endpoint is `192.168.11.131`, discovered from live mountinfo and fstab.
DSM's API discovery and SSH respond, but the existing SSH key is rejected.
Authenticated DSM/model discovery, SNMPv3 settings/credentials, NAS hardware
values and NAS backup jobs remain unverified. No SNMP metrics or healthy NAS
hardware state are invented. Disk/RAID/volume health, capacity, temperatures,
fans, UPS and other hardware signals are **unavailable pending authenticated
NAS access**, not classified as unsupported by the model. Synology update
notifications were not changed. The requested SNMPv3 deployment is not complete.

### NFS isolation and local filesystem coverage

Five fixed mount/source pairs are checked against `/proc/self/mountinfo`:

| Probe | Mount | Expected source |
|---|---|---|
| library | /mnt/media-library | 192.168.11.131:/volume2/media-library |
| library-alias | /media-library | 192.168.11.131:/volume2/media-library |
| downloads | /mnt/media-downloads | 192.168.11.131:/volume2/media-downloads |
| storage | /mnt/storage | 192.168.11.131:/volume2/storage |
| k8s | /mnt/k8s-services | 192.168.11.131:/volume2/k8s-services |

Actual kernel filesystem type is `nfs` (NFSv3), despite fstab's `nfs4` field
with `vers=3`. Both nfs/nfs4 kernel types are accepted only for the exact
expected source and mount. Mountinfo parsing does not stat or traverse NFS.
Each share has a new 31-byte `.homelab-monitoring-probe` file, created exclusively
and flushed once; the alias shares the library's probe file. No media file is
written or used as a probe. Subsequent collection is read-only and uses
`O_DIRECT`, an aligned 4 KiB buffer and an exact content comparison, avoiding
successful checks solely from the client page cache.

Each named `homelab-monitoring-nfs@NAME.service` runs every 30 seconds under
its own timer, with a four-second start timeout and one-second stop timeout,
32 MiB memory and two-task limits. No automatic service restart is configured.
A kernel-uninterruptible process may resist SIGKILL; systemd keeps that unit
stopping and cannot launch another instance. Thus there can be at most one
worker per fixed mount (five total), rather than a new stuck worker each cycle.
The separate storage observer reads only local result files every 30 seconds;
it has a five-second timeout and no dependency on NFS probe completion.
A read result older than 45 seconds fails. The last successful result is
retained for investigation; it cannot keep the current health metric green.

NFS failure persists 30 seconds before paging; observer age over 75 seconds
also alerts after 30 seconds. All probe timers and the observer timer are
enabled independently of media/NFS startup. The existing main monitoring
service still requires only Docker and local filesystems. Do not add NFS to
its dependencies. A killed sleeping fixture proves timeout handling, not
recovery from an actual kernel D-state; no live mount or NAS connection was
interrupted. Missing mount, wrong source/filesystem, expired read and recovery
are covered by isolated fixtures.

Actual config and temporary downloads are `/opt/data/homelab/config` and
`/opt/data/homelab/downloads`, both on local ext4 `/dev/sdb` mounted at `/opt/data`.
The existing 15% free-space and 10% free-inode rules cover this filesystem and
root. No duplicate local capacity alert was added. Local Loki retains its
existing separate 16 GiB filesystem, 20% warning and seven-day retention target.

### DNS and verified TLS

Prometheus blackbox exporter v0.28.0 is pinned to the verified linux/amd64
registry digest. It has no published port, socket or host mount, drops all
capabilities, has a read-only root, 128 MiB memory and 64-process limits.
Probes are fixed in configuration; no discovery-generated URL labels or
unbounded endpoints are accepted. Prometheus scrapes fixed targets every
30 seconds (TLS-only every 60), with 3–5 second probe and 5–7 second scrape
timeouts. Monitoring retention is unchanged.

Both actual R710 resolvers, 8.8.8.8 and 1.1.1.1, must return NOERROR and an A
answer for the ten configured Grafana, requests and application names. Both
failing for a name persists 60 seconds before paging. Queries accept an A
answer rather than pinning dynamic public addresses; HTTPS/API checks validate
endpoint identity and response semantics separately. IPv6 is not tested.

HTTPS checks cover both Grafana names at port 3000 (`/api/health`, database=ok),
`overseerr.a3f.link/api/v1/status`, and the actual public requests URL
`https://requests.neldridge.net:3579/api/v1/status` (version field).
Other application names (Sonarr, Radarr, Prowlarr, Bazarr, NZBGet, Tautulli) have
verified TLS/SNI handshake and chain-expiry checks at port 443, complementing
existing authenticated semantic API checks. TLS verification is never disabled.
The public requests URL is polled from the R710, not an external vantage point.
An initial DNS timeout recovered; all production probes subsequently passed.

HTTPS/TLS failure persists 60 seconds before paging. Chain expiry below 21 days
persists five minutes, allowing manual renewal in advance. This checks the
minimum chain certificate expiry reported by the standard exporter.
Expiry and recovery thresholds are configured; certificate renewal automation
is outside scope. Do not change application certificates to test this rule.
The existing single overview has five additional storage/dependency panels,
with links to DSM and Grafana alert management. Notifications link to panel 30.

### Backup evidence and limits

A separate 15-minute observer validates local scheduled backup artifacts under
90-second wall, 768 MiB memory and 50% CPU limits, with idle I/O priority.
Each ZIP is at most 64 MiB compressed, 512 MiB expanded and 16 entries.
It verifies CRC, required config/database members and SQLite `quick_check`
on private disposable copies. SQLite queries have an eight-second progress
budget. Config XML is parsed for Servarr; other config members are checked for
presence/nonempty content, and Tautulli's paired config INI is parsed.
Application databases and settings are never modified. Temporary copies are
cleaned automatically and remain outside the checkout.

Sonarr/Radarr/Prowlarr APIs expose seven-day scheduled backups and 28-day
retention. Their backup list is a filesystem listing, **not a job-success log**.
The collector therefore reports archive integrity and artifact age, never
`backup_success` or restore assurance. Age warns after the configured interval
plus one day (currently eight days); invalid artifacts and overdue age persist
five minutes. An API failure also makes validation unavailable/invalid and
requires investigation. Missing observer output for 20 minutes alerts.
Tautulli has a six-hour schedule and paired scheduled config/DB ZIPs; the age
budget is 12 hours. Bazarr is configured weekly; the age budget is eight days.
These discovered budgets are explicit in `backup_checks.py`; recheck after
changing application schedules.

Real issues discovered: newest Sonarr scheduled ZIP (2026-10-06 name,
2026-10-07 UTC mtime) passes ZIP CRC/XML but its embedded SQLite database has
btree/page/overflow errors. It must not be called restorable. Radarr and
Prowlarr latest archives pass structural validation. Bazarr's newest retained
archive is dated 2024-11-10 despite a weekly schedule. Keep real alerts active;
do not delete or repair archives as part of monitoring.

No verified scheduled off-host backup for the homelab config/runtime/media was
found on the R710. Existing migration/version backups are one-off copies, not
scheduled successful backups. The OS dpkg database backup timer has successful
systemd completion records but is not a homelab recovery backup. NAS jobs remain
unknown without access. Tautulli/Bazarr job result records, application restore
tests, Plex backups and off-host durability are not proven. A valid local
archive does not protect against loss of /opt/data.

### Phase 3 test procedure

Run isolated parser/archive tests with `python3 -m unittest discover -s monitoring`.
Do not unmount media or disconnect NAS. A private `phase3-fault-nfs` marker changes
only the library monitoring result. `phase3-fault-backup-radarr` makes only its
monitoring validation invalid/overdue. Remove markers and run the corresponding
observer unit to recover. These tests intentionally create real PagerDuty events.
For DNS/TLS tests, temporarily change only blackbox's query name or expected
certificate name; restore its configuration and reload. Single-file bind
replacement requires container recreation, as described above.

### Measured phase 3 acceptance (2026-10-11 UTC)

| Monitoring-side fault | Fault effective | Grafana PagerDuty event | Recovery event |
|---|---|---|---|
| Library mount/read result fixture | 20:43:08 | trigger 20:44:26 (79 s) | restore 20:49:56; resolve 20:50:26 (30 s) |
| NXDOMAIN on both resolver probes for Sonarr | 20:48:16 (collector recreated) | trigger 20:49:55 (99 s) | restore 20:49:56; resolve 20:50:25 (29 s) |
| Wrong expected certificate name for Grafana probes | 20:48:16 | trigger 20:49:53 (97 s) | restore 20:49:56; resolve 20:50:53 (57 s) |
| Radarr invalid/overdue artifact fixture | ~20:43:14 | invalid trigger 20:48:50; overdue trigger 20:48:51 (~337 s) | restore by 20:49:56; overdue resolve 20:50:21 (25 s); Radarr validation returns 1 |

The invalid-backup incident remains firing for the **real Sonarr corruption**;
removing the Radarr fixture correctly removes only that affected instance.
Grouping is still alert name and host, so the group must not resolve while a
real invalid archive remains. DNS/TLS faults initially did not reach the
collector because an earlier file replacement left its bind on the old inode;
timings above start at recreation when those faults actually became effective.
The test did not alter Grafana's HTTPS listener or certificates.

A local sleeping read fixture timed out in 4–5 seconds, left MainPID=0 and had
no automatic restarts. Nine parser/schema/archive fixture tests pass on R710.
Compose and Prometheus config validation pass; Grafana provisioning reloads
return 200. There were no NAS disconnects, unmounts or media container restarts.
All test markers were removed and the original blackbox configuration restored.

These times are **Grafana notifier event timestamps**, not measured phone
arrival latency. PagerDuty browser sign-in expired again when opening Incidents;
independent inspection of phase 3 incident creation, investigation links and
integration-driven resolution remains pending renewed access or user
confirmation. Do not describe notifier logs alone as verified PagerDuty
incidents. NAS SNMP/DSM acceptance and restorable/off-host backups remain gaps.
Nothing was committed; phase 4 and certificate renewal automation were not added.

Final live verification: all five NFS direct reads, 30 fixed dependency/DNS probes,
nine semantic APIs and four Exportarr scrapes are healthy. Both Healthchecks
checks are up. Certificate chains have about 89–90 days remaining. No phase 3
fault markers remain. Media container start times remain 16:25 UTC (Nginx
16:38 UTC), before phase 3 work, with zero restarts. Tautulli's valid paired
archive is about 14.7 hours old against a six-hour schedule (12-hour warning);
this is a further real overdue condition. NAS access and independent PagerDuty
incident verification remain outstanding.

At 21:00 UTC the Bazarr backup directory was observed empty, after containing
five old archives earlier. Its current validation and artifact timestamp are
both zero. Monitoring reports missing evidence; it did not remove any archives.

### Authenticated DSM and PagerDuty follow-up (2026-10-11)

Signed-in DSM confirms pelican, DS920+, DSM 7.3.2-86009 Update 3.
Storage Manager reports Pool 2 healthy, SHR with one-drive fault tolerance,
four healthy 20 TB WDC WD221KFGX-68B9KN0 HDDs; Volume 2 shows 21.7 TB used
and 35.9 TB free. Drive 1 Health Info reports 41 C. These are DSM observations,
not yet matched to SNMP: SNMP service, v1/v2c and v3 are all disabled.
UPS support is disabled and DSM explicitly reports no UPS connected. Do not
invent UPS readings or change power settings. Task Scheduler has no tasks.
USB Copy opens its Welcome screen and has no configured task summary.
Cloud Sync has B2 Backups, Extras and Pictures connections. The Backups
connection is up to date, encrypted, uploads local changes only, retains
remote files after local deletion, and enables advanced consistency checks.
This is configured replication; no completed backup/restore evidence is inferred.
No Hyper Backup application appears in the signed-in main menu; package
installation status and other-user jobs were not exhaustively checked.
All NAS inspection was read-only. Existing update notifications were untouched.
SNMP setup awaits user credential entry: browser policy requires handoff for
new credentials. Automatic browser review also rejected an ambiguous coordinate
click to the SNMP tab; it was not retried or bypassed and no service was enabled.

PagerDuty's renewed Incidents session verifies NFS #18, backup-age fixture #19,
TLS dependency #20 and DNS #21 are resolved through the integration API.
NFS #18 contains service=nfs-library, host=bb9b, explanation/persistence,
overview panel 30, rule, dashboard and prefilled silence links. The real
invalid-backup #17 and real overdue-backup #22 remain open, as expected.
This supersedes the earlier pending PagerDuty incident verification note.
Phone delivery latency remains unmeasured; timings above are notifier timestamps.

### Phase 3 NAS deployment (2026-10-11)

User enabled SNMPv3 only in DSM, SHA authentication and AES privacy, dedicated
`monitoring` identity. v1/v2c remains disabled. Credentials and generated
`snmp.yml` are root-owned mode 0600 under runtime, never in Git. Regenerate with
`sudo python3 monitoring/configure_snmp.py` then recreate only `snmp` after
credential/module changes. Exporter has no published port, caps, host filesystem
or Docker socket; root UID is solely to read the root-only configuration bind.
128 MiB, 32 tasks, 0.5 CPU, one module per scrape, 30-second interval,
10-second scrape timeout, two-second UDP timeout, no retries, 500 sample limit.
Module definitions derive from official snmp_exporter v0.30.1 Synology module;
limited to system/disks/RAID/UPS/SMART and HOST-RESOURCES storage, excluding
service users, serial numbers, iSCSI and IO histories. Duplicate Docker share
mounts and temporary filesystem metrics are dropped before ingestion.

Live v3 authPriv reads take about 0.47 seconds. Four disk deployment and health
statuses=1 agree with DSM's four healthy HDDs. All disk roles=data, bad sectors,
retries and identification failures=0; remaining life=-1 means unavailable,
not a failed drive. SMART returned OK attributes. Pool 2 and Volume 2 status=1
agree with DSM healthy SHR. Volume total 63.33e12 bytes and free 39.51e12 bytes
are approximately 57.6/35.9 TiB, matching DSM's displayed 21.7 used/35.9 free.
Pool free ~273 MB is unallocated pool space; never use it as volume free space.
System/power/system fan/CPU fan and thermal statuses=1; system 54 C and disks
42–43 C (earlier DSM drive-1 observation 41 C, before this scrape). Model matches
DS920+. SNMP version string is DSM 7.3-86009 and omits DSM UI's minor/update
suffix; DSM UI remains the authoritative full version.

Mappings verified against Synology's official MIB Guide:
https://global.download.synology.com/download/Document/Software/DeveloperGuide/Firmware/DSM/All/enu/Synology_DiskStation_MIB_Guide.pdf
Normal system/fan/power/thermal=1, failed=2. Disk deployment=1 normal,
2 initialized, 3 uninitialized, 4 system-partition failure, 5 crashed, 6
disconnected (enterprise); health=1 normal, 2 warning, 3 critical, 4 failing.
RAID 11 degraded, 12 crashed/read-only, 21 unknown page; background processing
including repair=2 and scrub=13 is displayed without treating it as failure.
Disk>50 C/system>75 C and volume<15% free warn after five minutes; urgent
collection/hardware/RAID/expected-disk completeness use 30-second persistence.
Isolated promtool fixtures test normal, failed and recovered disk/SMART, degraded
RAID and healthy scrubbing. Run `promtool test rules snmp-test.json` in
`monitoring/tests/`.

Unavailable: NAS is powered by a UPS (user confirmed), but the UPS has no data connection to DSM; no UPS values returned; no RPM sensors
in these returned MIBs (only aggregate fan status), no per-power-rail voltage,
HDD lifetime estimate=-1. CPU-fan status is firmware's aggregate reading, not
proof of a separately replaceable CPU fan. No expansion/enclosure or SSD cache
hardware was discovered; no fabricated signals. USB filesystem capacity is
visible, but no successful USB backup job is evidenced. Cloud Sync's up-to-date
state is replication status, not proof of a completed/restorable backup. DSM
update notification configuration was preserved.

The deployment above supersedes earlier notes that NAS access/SNMP were pending.
SNMP collector logs use the existing bounded Alloy/Loki pipeline and overview
log panel 24 (`monitoring-snmp`); they remain excluded from recurring application
error paging. Final NAS ingestion contains 178 series, below the 500 sample cap.
This host's Compose ignored `cpus: 0.5`; both new phase-3 exporters now use
explicit CPU period 100000/quota 50000, verified in Docker HostConfig.

NAS acceptance stopped only the collector, never the NAS/NFS. The first run
exposed redundant completeness/no-data pages, corrected by gating completeness
on successful collection and handling absent hardware data through the collector
outage rule. Test incidents #23/#24 resolved automatically. A final run with
these fixes stopped the collector at 21:25:36.994 UTC; the sustained outage
trigger was sent at 21:27:11.136 UTC (94.1 seconds). No other NAS rule fired in
that run. Earlier rule-state transitions during deployment/reload are not used
as the final acceptance measurement. Collector restored at 21:28:19.595 UTC;
all NAS rules returned inactive by the 21:28:49.981 observation (30.4 seconds).
Final PagerDuty incident #27 is Q39SRYPRIDGMI0. Incident #25 already verified
DSM, overview panel 35, rule, dashboard, and prefilled silence links.

Final live checks: authenticated NAS scrape up, thermal status normal, five
NFS reads healthy, 30 DNS/TLS/HTTP probes healthy, four Exportarr scrapes healthy,
nine semantic API checks healthy. Both metrics/log heartbeat rules are firing
with health=ok as intended. All media container start times and restart counts
remain unchanged. Nine Python regression tests and nine isolated PromQL fixture
assertions pass. No commits; no phase 4 or certificate-renewal automation.

Final NAS resolution sent at 21:29:11.238 UTC, 51.6 seconds after collection
was restored. PagerDuty incident #27 visibly reports Resolved (opened 5:27 PM,
resolved 5:29 PM). Timings measure notifier dispatch and verified PagerDuty
incident state, not handset delivery. This completes the phase-3 notification
acceptance, alongside the earlier NFS/DNS/TLS/backup fixture incidents.

UPS clarification: a UPS supplies NAS power, but its USB/network data connection
is absent. DSM cannot report battery charge, runtime or UPS power events.
No UPS hardware or power settings were changed.

## Phase 4: versions and maintenance

`version_checks.py` runs as a separate read-only host observer, using the same
root/Docker trust as the existing checks. There is no new daemon, container,
Docker socket mount, application exec, pull, restart, upgrade or migration.
Install/enable `systemd/homelab-monitoring-versions.{service,timer}`. The timer
runs daily at 07:00 server local time (Eastern), randomized up to 30 minutes,
with persistent catch-up. It requires only local /opt/data, never NFS/Synology.
Manual refresh: `sudo systemctl start homelab-monitoring-versions.service`.

Overview panels 40–42 extend the existing dashboard. Inventory is a **daily
snapshot**, not continuous container discovery; inspect its timestamp after
application changes. It shows configured running tag, local RepoDigests, actual
platform image/config ID, architecture, installed application version and source,
available stable tag/index digest, installed/release channels and maintenance
status. API versions cover Sonarr/Radarr/Prowlarr/Bazarr/Overseerr/Tautulli/NZBGet
and Plex; Kometa uses the current run log's version (last logged run, not a live
API). Nginx reports its live Server header. Monitoring components use actual
build metrics/Grafana health, with Exportarr's immutable application version
label. Do not substitute base-image OCI labels: Alloy's version label describes
Ubuntu 24.04, not Alloy. Failed application version reads remain unknown.

### Release mechanism and comparisons

A bounded Python standard-library observer fits this installation better than
adding Diun plus a separate API-version collector. Diun's pinned-reference checks
alone would miss future tags and would still need application/Plex handling.
The observer uses public metadata, downloads no image layers, and needs no new
registry/GitHub credentials:

- LinuxServer: enumerate the 200 most recently updated Docker Hub tags (two
  pages of 100), accepting only numeric stable `VERSION-lsBUILD` tags. Exclude
  develop/nightly/RC and architecture-prefixed aliases. Resolve the selected tag
  against the **actual configured registry**, including lscr.io; Hub mirror
  digests are never assumed equal to lscr.io digests.
- Nginx: numeric Alpine tags, even minor stable branch; mainline odd minor and
  prereleases are excluded. A newer stable branch can be discovered.
- Monitoring images: official GitHub latest non-draft/non-prerelease release,
  then verify that version's actual registry manifest. Exportarr metadata and
  registry results are shared across its four instances.
- Plex: authenticated installed version/platform from PMS; compare the matching
  platform with Plex's public download JSON. No Plex Pass/beta releases.

Multiarchitecture indexes and image config digests are different objects.
Candidate manifests must include the running OS/architecture; compare their
platform config digest with Docker's actual running image ID. Equal config IDs
are current even if index digests differ. Numeric installed-ahead versions never
suggest a downgrade. Same application version/new LSIO build is `image-rebuild`;
a newer application version is `update`. Mutable `latest`/`stable` tags have no
invented installed version; they are resolved by platform identity against
newly discovered stable version tags, and changed identity is explicit. Other
non-numeric branches are channel-review/unverified rather than silently healthy.
A failed lookup is unknown and has its own maintenance notification; failure to
finish leaves the previous snapshot stale, with a 28-hour freshness alert.

Plex runs separately at 192.168.11.129, reports Linux/Ubuntu 24.04.5 and a full
PMS version. Its API does not expose CPU architecture or installed public/beta
channel here. Those fields remain unknown/unverified; this is a release notice,
not proof that a particular binary is appropriate to install. DSM's separate
existing update notifications remain the NAS update mechanism.

### Notifications, bounds and acceptance

The specified fallback is implemented: low-urgency update notifications and the
dashboard list, rather than a custom weekly digest scheduler. Seven-day Grafana
repeat reminders are **not** a weekly digest. `scope=maintenance` routes to the
separate informational PagerDuty contact, grouped by alert name and host, with
resolved messages enabled. Existing workload routes remain critical. PagerDuty's
Homelab service uses severity-based urgency: Critical/Error/Not Available → High;
Warning/Info → Low. This service-side setting is not Grafana-provisioned; preserve
it when editing PagerDuty. Pushover is retained unused with no policy route.
Existing independent metrics/log heartbeats and Kometa review-only error/run
handling are unchanged. Overseerr deprecation is a maintenance notification,
not an automated migration: https://info.linuxserver.io/issues/2026-02-16-overseerr/.

Collection is sequential (one network request at a time), at most 32 running
containers plus external Plex. Up to 160 registry/release HTTP calls per run,
eight-second socket timeouts, two MiB metadata/read bounds, no retry loops beyond
one registry authentication exchange. API/build reads use five-second timeouts.
Docker commands have five/eight-second timeouts. The unit has a hard ten-minute
runtime, 128 MiB memory, 25% CPU, 32 task cap, GOMAXPROCS=2 and low CPU/IO priority.
The initial eight-task cap was insufficient for Docker's Go CLI and was corrected
before acceptance. Labels are limited to fixed inventory fields, each capped at
512 characters; no container IDs as separate series, request/media labels or
credentials. Roughly 100 current series, with ordinary 14-day Prometheus retention
bounding daily version-label churn. Snapshot JSON is mode 0600 and textfile metrics
0644 under private runtime; no credential/config contents are exposed as metrics.
Existing monitoring retention/log limits remain unchanged.

Live checks on October 11, 2026 found 20 inventory entries: 17 current,
Blackbox Exporter v0.28.0 → v0.29.0, Radarr application unchanged at 6.4.4.10685
but image build ls319 → ls320, and frozen/deprecated Overseerr v1.35.0-ls159.
All release lookups and installed-version reads succeeded. The daily unit
completed in about 24 seconds, 32 MiB peak memory, 2.3 CPU seconds and 106 metadata
calls. Twelve Python tests cover existing phases plus numeric future-tag discovery,
stable/mainline/prerelease exclusion, rebuild ordering, architecture filtering
and correct index-versus-platform-config comparison.

Real PagerDuty update incident #32 (`Q1OWNKPACJ21OL`) was verified as Info
severity, Low urgency, with both monitoring-blackbox and Radarr in the same
alert-name/host group, plus dashboard/panel/rule/silence links. Overseerr #31 is
separate and Low urgency. A monitoring-only `Phase4UpdateNotificationTest`
fixture triggered #30 (`Q31JZDTYAXADWJ`) at 18:28 Eastern and resolved via the
integration at 18:30 after its metric changed to zero. No UI resolve was used.
A short initial fixture NoData incident #29 also resolved automatically; the
first rule evaluation preceded its initial scrape. For repeat acceptance,
create/scrape the fixture metric **before** provisioning the temporary rule.
The test rule and metric were removed after resolution. Real maintenance and
backup incidents remain active; do not suppress them to make acceptance green.
Notification/incident state is verified in PagerDuty; handset arrival latency
is not measured. Grafana's authenticated dashboard API confirms panels 40–42
and the 20-row query returns data. Browser visual QA remains unverified because
that browser has no signed-in Grafana session. No authentication was weakened.
Both HTTPS health endpoints pass certificate validation/database=ok, nine API
checks/four Exportarr scrapes/NAS scrape remain healthy, both heartbeat rules
have health=ok, and media start times/image IDs/zero restart counts match the
pre-change inspection. No commits, unrelated backup repairs or later phases.

## Seerr migration (October 11, 2026)

The request application is now Seerr v3.5.0 using the official linux/amd64 image.
See [migration verification and exact rollback](../compose/SEERR_MIGRATION.md).
Earlier Overseerr observations above are historical. Semantic API checks and
stable GitHub/GHCR version tracking now use service `seerr`; the private
`app-keys.json` has its preserved API key under `seerr`. Docker discovery excludes
the retained stopped Overseerr rollback container and its historical event
counters, while automatically discovering Seerr's bounded JSON logs. The overview
service selector and dependency check use Seerr. The existing DNS name
`overseerr.a3f.link` intentionally remains unchanged.

PagerDuty contact points, grouping, resolution, both independent Healthchecks
heartbeats and Kometa review-only handling are unchanged. The deprecation metric
was set to zero only after successful migration; Grafana sent PagerDuty resolve
events before the obsolete `deprecated-overseerr` rule was removed using
`deleteRules`. All other maintenance and backup conditions retain their behavior.

### Tautulli manual backup support (October 11, 2026)

The backup observer now selects the newest Tautulli database ZIP and newest
configuration ZIP independently, including both manual and scheduled backups.
Their timestamps need not match. Both archives must pass validation; the
reported artifact timestamp is the older of the two, so a fresh database cannot
hide a stale configuration. The existing 12-hour age budget and alert routing
are unchanged. The newest invalid archive still fails rather than silently
falling back to an older valid one. Fresh API-created manual archives passed
CRC, SQLite quick_check and configuration parsing; Sonarr and Bazarr's fresh
October 11 archives also passed validation, superseding earlier missing/corrupt
latest-backup findings. No restore test or off-host durability is implied.

## HTTPS renewal implementation (October 11, 2026)

See [certificate renewal and exact rollback](../certificates/README.md). Guarded
Certbot DNS-01 renewal uses a dedicated least-privilege Route 53 IAM identity and
root-only runtime /opt/data/homelab/acme. Twice-daily scheduling uses
homelab-certificates.timer with persistent catch-up and up to one hour jitter.
Failed/stale renewal rules join the existing served-certificate expiry probes.
Both heartbeat routes, PagerDuty grouping/resolution and Kometa handling are
unchanged. This supersedes earlier manual-renewal notes above.

## Available wanted backlog (October 11, 2026)

`wanted_checks.py` runs through `homelab-monitoring-wanted.timer` every five
minutes, independently of the 25-second service-health check. Both applications
are read-only. A monitored missing movie must have `isAvailable=true` and a past
digital or physical release date; announced/theatrical availability alone does
not qualify. An episode and its series must be monitored, the episode must have
a past UTC air date, and no file may exist. Items in the application's download
queue are excluded (existing stuck/failed queue alerts handle downloads/imports).
No quality-upgrade/cutoff backlog is included. Release eligibility cannot prove
that an acceptable release exists on an indexer; the alert requests investigation.

Per-item IDs/timestamps persist in root-only `sonarr-wanted-state.json` and
`radarr-wanted-state.json` under runtime. The clock starts at first observation,
including for old backlog at deployment. It resets when an item stops qualifying,
enters the queue, or there is more than 15 minutes between successful observations.
A 10-hour age sets an aggregate overdue count by service; Grafana's
`AvailableWantedOverdue` persists one minute before the existing workload
PagerDuty route fires. Allow about six minutes beyond ten hours for polling and
evaluation, plus notification grouping/delivery. Recovery resolves automatically.
Alert descriptions link to each application's Wanted list. No titles/IDs are
exported as Prometheus labels. Metrics include eligible/overdue counts and oldest
age. `WantedObserverFailed` separately covers failed/missing/stale observations;
failed/partial API reads never publish a healthy zero backlog.

API reads have five-second socket timeouts and a 32 MiB response cap; paginated
wanted/queue snapshots are capped at ten pages/10,000 records, with incomplete
snapshots treated as failures. Radarr's full movie list has the same item cap.
The unit has a 120-second hard timeout, 128 MiB memory and 25% CPU budget.
Install `systemd/homelab-monitoring-wanted.{service,timer}` and enable the timer.
Manual refresh: `sudo systemctl start homelab-monitoring-wanted.service`.
Rollback: disable/stop this timer and remove the two `wanted-*` Grafana rules,
then reload alert provisioning; remove `textfile/wanted.prom` afterward.

Live deployment verified both collectors successful, one eligible item in each
application, zero overdue initially, and both Grafana rules inactive/health=ok.
Twenty Python regression tests passed, including release/monitor gates, the
10-hour boundary, queue/removal recovery, outage reset and pagination bounds.
No synthetic PagerDuty incident or handset delivery test was performed for this
addition. No application settings, downloads or media containers were changed.

## Search escalation and transient version failures (October 12, 2026)

Wanted monitoring now submits targeted automatic searches at 2 and 5 hours,
then keeps the existing 10-hour alert. See WANTED_MONITORING.md for persistence,
queue resets, batch bounds and catch-up behavior. The earlier read-only wanted
observer description is superseded by this explicitly authorized search behavior.

Version endpoint requests retry transient HTTP 408/429/5xx and network/timeouts
up to three times with 1- and 3-second backoff, within a 480-request run budget.
The daily inventory remains scheduled; an additional
`homelab-monitoring-versions-retry.timer` runs every 15 minutes, invoking its
matching service with `--retry-failed`. Healthy snapshots are skipped; failures
are rechecked, including after an incident opens. A lock prevents overlapping
runs. The retry guard requires at least 14 minutes since the prior snapshot.
`VersionLookupFailed` requires three consecutive failed inventory checks per
service, then the existing two-minute persistence. A successful check resets
the counter to zero and publishes healthy metrics so Grafana automatically
sends the existing PagerDuty resolve event. State and failure streaks persist in
versions.json. HTTP status codes are retained; response bodies and URLs are not.
Install/enable both new recovery units alongside the existing daily timer.
