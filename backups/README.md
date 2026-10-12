# Homelab off-host recovery — implementation in progress

## Verified state, October 11, 2026

bb9b is 192.168.11.10. Data is local ext4 under /opt/data. pelican is
192.168.11.131, DS920+, DSM 7.3.2-86009 Update 3, Eastern timezone.
Hyper Backup was absent, was installed with approval, and initially had no tasks.
Cloud Sync B2 (Backups) covers /storage/Backups, encrypted, upload-only,
retains destination files after local deletion, and reported up to date.
Do not repurpose or change that connection or its bucket.

First completed bundle: /opt/data/homelab/backups/20261011T234657Z
(1,541,524,170 file bytes, 3,400 files, nine SQLite databases). Manifest hashes
and full SQLite integrity checks passed independently. A private copy under
backups/restore-tests/20261011T234657Z passed the same checks. This was a LOCAL
restore, not a NAS or B2 restore. A newer bundle adds the local checkout snapshot.
No application containers were stopped or started for verification.

## Scope and consistency

create_bundle.py runs as root on bb9b. Output directories are private (0700),
files 0600. SQLite files are recognized by their header and copied with SQLite's
online backup API, with a bounded deadline and full integrity_check. WAL/SHM
files are never substituted for snapshots. Unknown .db formats fail closed.
Config files must remain unchanged during their individual copy. Each database
is consistent independently; this is not a cross-application transaction or a
filesystem-wide point-in-time snapshot. Do not edit application settings during
a backup if config/database agreement is important; use a scoped stop for such
changes and immediately take a new bundle.

Included: Sonarr, Radarr, Prowlarr, Bazarr, Seerr, Tautulli, NZBGet, Kometa
(plexmetamanager), preserved Overseerr, legacy HTPC Manager/Muximux configs;
server Git checkout with uncommitted changes and .git history; materialized
Nginx certificates; monitoring runtime.env, app-keys.json, snmp.yml,
synology-snmp.json, TLS, Grafana online DB snapshot and plugins;
fstab, hostname, hosts, netplan, Docker config, cron.d and homelab systemd units;
package/unit/mount/container inventory; private Seerr rollback bundle.
Private source-inputs may additionally contain a local checkout snapshot,
including ignored secrets, Terraform state and local deployment changes.
These archives must never be added to Git.

Excluded: bulk media, downloads, logs, caches, media-cover cache, historical app
ZIP backups, known corrupt/recovery scratch databases, Prometheus/Loki/Alloy
history, external Plex data, host SSH private keys. SSH identities can be
reissued; NAS/B2 recovery credentials must be held independently. Old corrupt
DBs and prior backups are retained at their original locations.
Full Grafana DB plus GRAFANA_SECRET_KEY is necessary to recover encrypted
contact-point secrets; restoring only provisioning is insufficient.

## Active schedule and retention

Local daily 03:00 America/New_York. Transfer only after validation. Hyper Backup
04:30 Eastern, with weekly Sunday 06:00 integrity checks.
Customized cloud rotation keeps daily versions for 30 days, weekly through
12 weeks, monthly thereafter, capped at 54 total versions. Age tiers overlap;
this does not guarantee three independent counts of 30/12/12 versions.
Keep local/NAS staging bounded only after explicit approval of deletion rules.
No existing backup deletion is authorized. The enabled daily job refuses to
start unless backup storage plus an 8 GiB reserve fits within 64 GiB, and the
filesystem has at least 8 GiB free. It records failure for monitoring when this
guard trips. This temporary guard bounds accumulation; an approved pruning
policy is required for continued unattended operation.

Use stable source paths in the eventual NAS publication layout for incremental
block deduplication. Transfer to an excluded staging directory, read back and
verify, then publish a completed generation atomically. Never back up a partial
upload. Prefer userspace SMB transfers with process and protocol timeouts, no
persistent CIFS/NFS mount, and a dedicated nonadministrator account permitted
only on homelab-recovery. NAS failure must not affect media services or local
bundle completion. A failed transfer leaves the previous completed generation.

## B2 configuration to approve/finish

Dedicated private bucket: neldridge-homelab-recovery.
Endpoint observed on existing buckets: s3.us-west-002.backblazeb2.com.
Hyper Backup: S3 Storage, custom endpoint, signature v4, TLS, bucket-restricted
read/write/delete application key plus List All Bucket Names if discovery
requires it. Do not use the account master key. Read/write/delete is needed for
repository management and rotation; a write-only key is insufficient.
Enable Hyper Backup client-side encryption and compression. SSE-B2 at rest is
additional protection, not a replacement for client-side encryption.

Do not apply independent B2 lifecycle expiration to repository objects. Let
Hyper Backup manage its own version graph. Proposed Object Lock setting is
disabled: this repository is mutable and no integration-specific immutability
behavior has yet been verified. Backblaze's July 2026 integration guide says to
enable Object Lock but does not document compatible Hyper Backup retention or
mutation semantics. Enabling the bucket feature alone is distinct from imposing
default object retention. Treat immutability as a separate unverified requirement;
do not claim ransomware-proof storage. Never alter existing bucket retention.

Published B2 pricing checked October 11: $6.95/TB/month; first 10 GB account-wide
free, already consumed here. Nine-DB bundle is 1.54 GB. 54 full independent copies
are approximately 83 GB, $0.58/month before compression/deduplication, taxes and
growth. Budget proposal $2/month additional. An alert is not a spending cap.
Existing account storage is separate and substantial; do not lower account-wide
caps in a way that interrupts existing Cloud Sync. Measure actual HB repository
size/churn after the first week, including B2 retained object versions.

## Credential and recovery-key custody

Enter secrets directly in DSM/B2 or a private root-only server file via your
terminal/password manager, never chat or Git. The user must complete credential
creation/entry in browser flows. Save the one-time B2 application key securely.
Save the downloaded Hyper Backup encryption key AND encryption password in a
password-manager vault accessible without bb9b/pelican, plus an offline copy
stored separately from the NAS. Record the bucket, endpoint, task/repository
path and required account recovery/MFA methods in that vault. Verify the offline
key by using it in the isolated restore. Losing both key/password makes encrypted
backups unrecoverable. Do not store the sole key in its own encrypted backup.

## Evidence and monitoring

Existing backup_checks.py still validates the five app-generated backup sets.
recovery_checks.py separately exposes local/NAS/cloud known, success,
completion time and observation time. Missing NAS/cloud observations mean
UNKNOWN, never success based on a local file's mtime. NAS evidence must come
from remote readback; cloud evidence must come from a real Hyper Backup task
observer, including last successful task, selected source generation, integrity
check and errors. That observer and its alert rules remain pending setup.
Do not fabricate cloud-status.json by hand to make a dashboard green.

Preserve existing PagerDuty alert-name/host grouping and automatic resolution,
both separate metrics/log Healthchecks heartbeats, and Kometa review-only
handling. No notification policy modifications are needed for the local builder.
Final cloud alerts and failure-notification delivery require live acceptance.

## Local verification and isolated restore

Run without starting applications:

```sh
ssh neldridge@192.168.11.10
sudo python3 /tmp/verify_bundle.py /opt/data/homelab/backups/20261011T234657Z
sudo python3 /tmp/verify_bundle.py /opt/data/homelab/backups/restore-tests/20261011T234657Z
```

/tmp is a temporary implementation location until deployment is completed.
Checks validate the COMPLETE manifest hash, every listed file hash/length,
SQLite integrity and table counts, selected JSON, Servarr XML and Tautulli INI.
They do not prove semantic restore of every application or external integration.
Do not launch a test Compose project with production configs: schedulers and
Plex/Sonarr/Radarr/download credentials would point at live services.

## Recovery when bb9b is lost (planned, not yet rehearsed)

1. On a clean replacement host install the recorded OS/Docker dependencies.
2. Retrieve a completed NAS generation or restore one from B2 using Hyper Backup
   into a separate destination share; enter the independently stored key.
3. Copy the restored tree to private local storage and run verify_bundle.py.
4. Recover deployment files from deployment/server-repo. Restore configs to
   /opt/data/homelab/config and monitoring state/secrets to its private runtime
   root. Use manifest uid/gid/mode values deliberately; staging permissions are
   private and are not production runtime permissions (Grafana uses UID 472).
5. Remove stale DB WAL/SHM files only in the new restore destination, never on the
   running source. Use the snapshot DB files, not app backup/recovery scratch DBs.
6. Recreate required local mounts and certificate paths from inventories; inspect
   host identity/network configuration rather than blindly replacing it.
7. Keep application startup disabled until the intended NAS mounts and secrets
   are restored. Start Seerr only; retained Overseerr is rollback data, not an
   additional scheduler. Restore monitoring independently of NAS availability.
8. Start approved services in order and verify authenticated APIs/DB counts,
   both heartbeats and PagerDuty resolution. Never commit recovered secrets.

## Recovery when the NAS is also lost (planned, not yet rehearsed)

On another compatible Synology install Hyper Backup, choose restore from an
existing S3 repository using the recorded B2 endpoint/bucket/path and a recovery
credential, and import the offline encryption key. Restore the bundle to a
separate private share, then follow the bb9b steps. An alternative is to download
the complete .hbk repository using an authenticated B2/S3 client and open the
local repository in Hyper Backup Explorer; do not assume Explorer connects
directly to arbitrary S3 storage. That path needs an actual test before signoff.
A B2 file listing or successful HB integrity check alone is not a restore test.

## Plex remains separate

Plex is on 192.168.11.129; SSH from bb9b failed host-key verification, so no key
was accepted and no Plex files were read/copied. Need separately verified access
and its actual data directory, metadata size, scheduled DB-backup location and
preferences. Use Plex's documented database backups/custom SQLite procedure or
a scoped Plex stop for a full data-directory backup; ordinary copying of its
running databases is not accepted. Exclude transcode/cache data. A scheduled
Plex database backup alone omits metadata and preferences. Include the measured
Plex scope/cost only after access and approval; it is currently unprotected by
this new pipeline.

## Failures and rollback

Incomplete local runs remain .partial-* and are never advertised as complete.
Do not publish them. Inspect the failure, free local space if necessary without
deleting existing backups, and rerun. No NAS work is in the local builder.
On NAS failure retain the completed local bundle and previous NAS generation;
retry the transfer after access recovers. On cloud failure inspect Hyper Backup
logs, credential permissions, quota, retention/lifecycle and integrity results;
never recreate a repository over an existing one to silence an error.
Disable only new backup timers to roll back. Preserve completed bundles, Cloud
Sync jobs, old backups, recovery keys and repository data. No Git commits,
router changes or unrelated service restarts are part of this implementation.

## Official references

- https://www.backblaze.com/docs/cloud-storage-integrate-synology-hyper-backup-with-backblaze-b2
- https://www.backblaze.com/cloud-storage/pricing
- https://kb.synology.com/en-id/DSM/help/HyperBackup/data_backup?version=7
- https://kb.synology.com/en-uk/DSM/help/HyperBackup/restore?version=7
- https://www.synology.com/en-sg/dsm/7.4/software_spec/hyper_backup
  (current general specifications; installed DSM is 7.3.2)
- https://blog.synology.com/hyper-backup-encryption-technologies-explained/
- https://support.plex.tv/articles/201539237-backing-up-plex-media-server-data/
  (fetch returned 403; detailed installed Plex procedure still needs verification)

## Follow-up configuration review

The user completed NAS account and B2 key creation. Review found the NAS account
had only the users group (correct), but inherited access to docker and
media-downloads and lacked recovery-share write access. Corrected only this
account: explicit No Access on all ten other shares, Read/Write on
homelab-recovery; explicit Deny for AFP, Cloud Sync, DSM, FTP, File Station,
SFTP, Surveillance Station, Universal Search and rsync; explicit Allow for SMB.
The save completed. Functional SMB authentication/readback remains pending the
private authentication file and smbclient installation approval.

B2 key pelican-hyperbackup-homelab exists, restricted to
neldridge-homelab-recovery, with list/read/write/delete file capabilities.
It does NOT have listAllBucketNames. Do not broaden it without explicit approval.
Hyper Backup still had no tasks. A new wizard is prepared for S3 custom endpoint
s3.us-west-002.backblazeb2.com, signature v4, region us-west-002, certificate
verification enabled, directory bb9b-configs. Secret entry, bucket selection,
source, encryption, rotation, schedule and completion remain pending.

Private NAS password entry (not chat):

```sh
ssh -t neldridge@192.168.11.10 'sudo python3 /opt/data/homelab/repo/backups/configure_nas_credentials.py'
```

The helper atomically saves /opt/data/homelab/backups/nas-smb.auth as root 0600.
No credential is printed or passed in command arguments.

## October 11 continuation

The user approved a replacement bucket-restricted B2 key with bucket-name
listing metadata permission. Hyper Backup destination lookup succeeded.
Task `bb9b-configs-b2` now exists, targeting bucket
`neldridge-homelab-recovery`, repository `bb9b-configs.hbk` at the regional
S3 endpoint above. Client-side encryption and compression are enabled;
notifications are enabled (delivery still needs testing). Daily backup time
is 04:30 Eastern; integrity checks Sunday 06:00. Custom rotation uses daily
versions for 30 days, weekly through 12 weeks, monthly thereafter, capped at
54 total versions. This is age-tier retention, not three independent version
counts. Object Lock and B2 lifecycle expiration remain disabled.

The private NAS credential file was created interactively. Ubuntu smbclient
installation was approved and completed. Encrypted SMB login to the dedicated
share succeeded. `publish_nas.py` validates a completed local bundle, creates
an uncompressed tar, uploads under staging, reads it back and verifies both
the archive checksum and all bundle databases/configuration. Only then does
it rename into `published/recovery.tar` and read back the published file.
Previous published archives move to `prior`; none are deleted. Hyper Backup
selects only `homelab-recovery/published`, excluding staging/prior.

Transfer jobs have a separate flock, 30-second SMB operation timeout and
30-minute process deadlines per bulk operation; no kernel mount or application
dependency is created. Publication replacement has a short gap between moving
the previous file and renaming the new one; do not overlap Hyper Backup with
publication. Retention/pruning of local and prior NAS generations is not yet
enabled, so space usage must be watched. No daily bundle/transfer timer has yet
been enabled. Key custody, cloud backup completion and a B2 restore remain
required before signoff.

The first NAS publication subsequently passed all checks: bundle
`20261011T235000Z`, 3,401 files, nine SQLite databases, 1,550,069,760-byte tar,
SHA-256 `7a0999d504275069b47f52bcb78c738b7b72d5a841765079131cb4914ee2875c`.
The published path was read back a second time and matched. Access to
media-library with the transfer account was denied. This is NAS evidence,
not a cloud restore. Hyper Backup's first upload subsequently reported Success,
last successful backup October 11, 2026 at 20:34 Eastern. This actual DSM UI
completion was recorded in cloud-status.json with method=manual-dsm-ui and
automatic=false. It is not inferred from local file age. Cloud restore remains
unverified until Backup Explorer extraction and independent validation finish.
The Explorer requires the encryption password; the user must enter it privately.

`homelab-recovery.timer` is now enabled for 03:00 America/New_York, with
Persistent=false (no unexpected catch-up run overlapping cloud backup).
The service has a hard 70-minute deadline, stopping by 04:10 for a normal
03:00 start. Inspect `systemctl list-timers homelab-recovery.timer` and
`journalctl -u homelab-recovery.service`. Roll back scheduling with
`sudo systemctl disable --now homelab-recovery.timer`; this does not delete data.
The service does not restart any application. Initial retained local test
copies use approximately 5.8 GiB plus the source bundle; retention/pruning is
still deliberately disabled. Capacity alerts exist; no cost hard cap exists.

Dashboard panels 60/61 separate stage evidence and age. RecoveryStageUnhealthy
alerts after five minutes of unknown/failed evidence or completion older than
36 hours. It uses the existing workload PagerDuty grouping and automatic
resolution. Both Healthchecks routes and Kometa review-only handling are
unchanged. Cloud evidence remains unknown until real Hyper Backup evidence is
observed; automated cloud observation is still a gap. The alert/dashboard
provisioning reload succeeded without restarting Grafana.

DSM default email rule already selects Hyper Backup failure, cancellation,
partial completion, suspension and integrity-error events. An existing recipient
profile is present. The user approved a test email to that recipient; DSM reports
the test email was sent. Inbox receipt confirmation remains pending. The user
confirmed the downloaded encryption key is saved separately from bb9b/pelican.
Keep its password and key available after loss of either host, and keep a second
offline copy. Never store the only recovery key inside the encrypted repository.

Cost caveat: the roughly $0.58/month estimate covers 54 full logical versions
at the measured size, before deduplication, growth and taxes. B2 keep-all object
versions can retain superseded objects independently of Hyper Backup rotation;
actual billable bucket usage must be measured. Do not describe the 54-version
limit or $2 planning budget as a storage/billing cap. Do not change lifecycle
expiration until its effect on this mutable repository has been verified and
approved. Backblaze's integration guide currently recommends the default
keep-all setting; its general file-version documentation explains additional
object-version storage: https://www.backblaze.com/docs/cloud-storage-file-versions
