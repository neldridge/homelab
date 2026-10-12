# Available wanted backlog

`wanted_checks.py` runs through `homelab-monitoring-wanted.timer` every five
minutes, independently of the 25-second service-health check. The observer submits automatic search commands at 2 and 5 hours; other
application access is read-only. A monitored missing movie must have `isAvailable=true` and a past
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

## Automatic search before paging (October 12, 2026)

Each continuous eligible cycle submits a targeted `MoviesSearch` (Radarr) or
`EpisodeSearch` (Sonarr) at 2 hours and again at 5 hours. Five-minute polling
adds up to five minutes of scheduling delay. Commands follow existing quality,
indexer and download settings and can initiate downloads. Queued or no-longer
eligible items are excluded; queue entry/removal or a >15-minute observation gap
starts a fresh cycle. The original 10-hour alert and recovery route remain.

Attempts are saved before submission, including command IDs on acceptance.
An ambiguous timeout is recorded as an error rather than automatically repeated;
the later five-hour attempt still applies. State survives observer restarts.
Commands batch at most 100 IDs per service/stage per poll. Delayed observers skip
the two-hour attempt if already past five hours, and skip all catch-up searches
for items already ten hours overdue (including existing backlog at deployment).
No search is triggered merely by installing this change. Submission failures
are exported as `homelab_wanted_search_failures`; the ten-hour page still applies.
