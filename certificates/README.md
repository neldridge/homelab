# HTTPS renewal on bb9b

Status: deployed October 11, 2026. Dedicated IAM user `homelab-bb9b-acme` in
AWS account 756222192529 was provisioned using the authorized org-talloaksit
administrator profile. Its access key exists only in root-only server runtime.
The old invalid /root/.aws profile was left untouched. No console login,
administrative permissions or unrelated DNS writes were granted. Certbot 4.0.0
and python3-certbot-dns-route53 are installed. The distribution certbot.timer is
disabled; use the guarded homelab timer instead.

Use Certbot DNS-01 for all three independent lineages: `a3f` (*.a3f.link),
`requests` (requests.neldridge.net), and `grafana` (grafana.a3f.link and
grafana.neldridge.net). No inbound ACME port or router change is needed.
Official references checked October 11, 2026:
https://certbot-dns-route53.readthedocs.io/en/stable/
https://eff-certbot.readthedocs.io/en/stable/using.html

## Credentials and activation

Create /opt/data/homelab/acme/aws-credentials privately as root:root 0600 with
an AWS [default] profile. Parent directory must be 0700. Never paste credentials
into chat or Git. `route53-policy.json` limits TXT writes to the four challenge
names in the repository's two hosted zones; confirm the zone IDs against AWS.
ListHostedZones requires a global resource; GetChange is limited to change ARNs.
Each zone has its own approved name list. IAM simulation confirms unrelated
names, non-TXT record types, cross-zone writes, IAM administration and zone
deletion are denied.
ACME accounts, lineages, logs and private backups stay under the 0700 runtime
root /opt/data/homelab/acme; no account data enters Git.

After copying certificates/ into /opt/data/homelab/repo/certificates, run as root:

```sh
python3 /opt/data/homelab/repo/certificates/renew.py staging
# Stop if staging fails. Staging has separate state and never deploys.
python3 /opt/data/homelab/repo/certificates/renew.py issue
python3 /opt/data/homelab/repo/certificates/renew.py verify
python3 /opt/data/homelab/repo/certificates/renew.py dry-run
install -m 644 /opt/data/homelab/repo/certificates/systemd/* /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now homelab-certificates.timer
systemctl start homelab-certificates.service
systemctl list-timers homelab-certificates.timer
```

Schedule: 03:00 and 15:00 server local time (Eastern), randomized up to one hour,
with persistent catch-up. Certbot decides when renewal is due; its additional random sleep is disabled
because the systemd timer already supplies jitter. The runner checks
and reconciles every lineage even when no certificate was renewed, retrying a
previous unsuccessful deployment. A host flock prevents overlapping runs.
The custom deployment stage follows successful issuance/renewal rather than
Certbot's deploy-hook so failed deployments retry even on no-renewal runs.

Before replacement: exact SAN set, matching public keys, at least 30 days left,
trusted chain, and quiet Compose validation. Private backups retain the old pair.
Replace files within the existing bind directories; never replace the mounted
parent directory. Nginx validates its configuration then reloads. Grafana alone
is force-recreated, also preventing stale single-file binds if mounts later change.
HTTPS checks verify hostname/chain and exact leaf identity, Seerr status JSON,
and Grafana database health. Failures restore both old files, reactivate and
verify; rollback failure exits nonzero and requires operator intervention.
No unrelated service is restarted. Backups are retained without automatic pruning;
include ACME runtime in private backup policy and review disk usage periodically.

## Exact rollback

Disable scheduling first. Select the absolute backup directory printed by the
successful deployment (or inspect /opt/data/homelab/acme/backups privately).
Run as root, replacing BACKUP_DIRECTORY and selecting a3f, requests or grafana:

```sh
systemctl disable --now homelab-certificates.timer
python3 /opt/data/homelab/repo/certificates/renew.py rollback \
  --name grafana --backup /opt/data/homelab/acme/backups/BACKUP_DIRECTORY
python3 /opt/data/homelab/repo/certificates/renew.py verify
```

Rollback validates the old pair and saves the current pair before restoring it.
It refuses certificates with less than 30 days left; emergency near-expiry
restoration needs an operator decision. Keep the timer disabled until the cause
is corrected: the next renewal reconciliation would redeploy the ACME lineage.
Never delete production account state or revoke certificates merely to roll back.

## Monitoring

Each production runner attempt atomically writes certificates.prom to the existing
Alloy textfile directory: last-attempt success and last-success timestamp. Failed
attempt alerts after five minutes; missing/stale success alerts after 36 hours
plus five minutes. Staging cannot mark production healthy. Existing blackbox TLS
expiry alerts remain at 21 days and probe the served chain independently.
New rules use scope=workload and host=bb9b, preserving existing PagerDuty grouping,
resolution, both heartbeat routes and Kometa review-only handling.
Deploy/reload the updated Grafana alert provisioning only after the initial
successful production run creates its metrics. Verify ingestion and rule state,
then test failure/staleness with isolated fixture metrics before claiming alert
acceptance. These new rules are loaded and healthy.

## Inspection on October 11, 2026

All existing pairs and live HTTPS health checks passed:

| Lineage | Issuer | Expiration (UTC) |
| --- | --- | --- |
| a3f | Let's Encrypt YE1 | 2027-01-09 23:47:28 |
| requests | Let's Encrypt YE2 | 2027-01-09 23:47:58 |
| grafana | Let's Encrypt YE1 | 2027-01-09 23:48:40 |

Nginx keys are root:root 0600; certificate files 0644. Grafana pair is 472:0
0640. Compose's nginx/certs symlink targets /opt/data/homelab/nginx/certs.
Both live containers mount TLS directories. Local rollback and invalid-candidate
unit tests pass. All three staging issuances and production deployments passed.
An actual staging certificate is rejected by the trusted-chain validator.
Five isolated Prometheus fixtures cover success, failure, recovery, staleness and
missing metrics. Grafana confirms new rules inactive/healthy, existing expiry
inactive/healthy and both heartbeat rules firing/healthy. Both independent
Healthchecks API statuses are up. All dependency probes report success.
The public requests URL on port 3579 returned Seerr 3.5.0 with valid TLS from
this workstation; an independent off-LAN vantage was not available.
New certificate alert notification delivery was not separately fault-injected
through PagerDuty; existing notification policy/grouping/resolution is unchanged.

Initial deployment rollback (run on bb9b as root; these backups contain the
original January 9 certificates):

```sh
systemctl disable --now homelab-certificates.timer
python3 /opt/data/homelab/repo/certificates/renew.py rollback --name a3f --backup /opt/data/homelab/acme/backups/1791766034183008062-a3f
python3 /opt/data/homelab/repo/certificates/renew.py rollback --name requests --backup /opt/data/homelab/acme/backups/1791766037613008167-requests
python3 /opt/data/homelab/repo/certificates/renew.py rollback --name grafana --backup /opt/data/homelab/acme/backups/1791766040763230237-grafana
python3 /opt/data/homelab/repo/certificates/renew.py verify
```

Do not run these during an active renewal; the lock rejects overlap. Timer
disable does not terminate an already running service. Check
`systemctl is-active homelab-certificates.service` and wait for it to finish.
Re-enable the timer only after resolving the deployment issue.

Final activation acceptance: saved production renewal configurations passed
`renew.py dry-run` for all three lineages. Live injected Nginx health failure
restored the previous deployed pair byte-for-byte and verified served HTTPS.
This exposed an asynchronous reload verification race, fixed by adding the
same bounded readiness wait on rollback. Timer is enabled and persistent;
first scheduled run October 12, 2026 at 03:03:18 Eastern. Manual systemd service
execution returned Result=success/ExecMainStatus=0. Only Grafana's container
start state changed; Nginx reloaded and unrelated containers retained their
start times and restart counts. No Git commits or router/authentication changes.

Remaining operational limits: new alert expressions were fixture-tested and
live rule health verified, but a new certificate-specific PagerDuty incident
was not deliberately generated. Existing PagerDuty grouping and automatic
resolution routes were preserved. This workstation's public URL check is not
an independent off-LAN test. Root-only backups remain on the same host and
have no automated pruning/off-host restore acceptance. Rotate the dedicated
IAM key privately according to your credential policy; never use the admin
profile as the unattended renewal identity.
