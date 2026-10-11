# Media services on Compose

Working deployment migrated from MicroK8s on October 11, 2026. Runs on
bb9b (192.168.11.10). Plex stays on its separate host.

Services: Sonarr, Radarr, Prowlarr, Bazarr, Overseerr, NZBGet, Tautulli,
Kometa, and Nginx. Muximux and HTPC Manager were retired.

For a fresh installation on your own infrastructure, use
[the Codex deployment prompt](../CODEX_PROMPT.md). The addresses and domains
here describe bb9b and must be adapted for other users.

## Files and storage

The server checkout lives at `/opt/data/homelab/repo`. During migration it tracks
`neldridge/composemigration`; switch to `main` after the pull request is merged.
Compose runs from `/opt/data/homelab/repo/compose`.
The existing bb9b installation links `.env` and `nginx/certs` to the runtime
files outside the checkout. Systemd runs Compose from this checkout.
For a fresh installation, copy `.env.example` to `.env` and adjust the host
paths and UID/GID, then provide certificates and adapt the systemd unit.
Application configs/databases, downloads, certificates, and private keys are
not in Git and must be backed up separately.

- `/opt/data`: local ext4 disk; configs and downloads live here.
- `/mnt/media-library`: Synology NFS library; imported movies and TV go here.
- Kometa retains its existing `config/plexmetamanager` directory name.
- NZBGet uses port **6790**, matching its saved application config.
- Bind sources must already exist (`create_host_path: false`). Restore
  application data before starting; this repository alone is not a data backup.

Nginx requires these files under the deployment directory:

```
nginx/certs/fullchain.pem
nginx/certs/privkey.pem
nginx/certs/requests/fullchain.pem
nginx/certs/requests/privkey.pem
```

The first certificate covers `*.a3f.link`; the second covers
`requests.neldridge.net`. Certificate renewal still needs automation.
Internal service names resolve to bb9b. The router forwards public TCP 3579
to bb9b TCP 443 for `https://requests.neldridge.net:3579/` (Overseerr).
Application ports are also published on the host, as in the working deployment.

## Start and inspect

From `/opt/data/homelab/repo/compose`:

```bash
docker compose -f compose.yaml -f compose.proxy.yaml config --quiet
docker compose -f compose.yaml -f compose.proxy.yaml up -d
docker compose -f compose.yaml -f compose.proxy.yaml ps -a
```

Both Compose files are needed to include Nginx. Images use explicit release
tags plus immutable digests, verified against published registry tags on
October 11, 2026. A tag makes the version readable; the digest fixes the exact
image content.

| Service | Release tag |
| --- | --- |
| Sonarr | `4.0.20.3014-ls327` |
| Radarr | `6.4.4.10685-ls319` |
| Prowlarr | `2.6.5.5623-ls163` |
| Bazarr | `v1.6.2-ls367` |
| Overseerr | `v1.35.0-ls159` |
| NZBGet | `v26.3-ls267` |
| Kometa | `v2.5.2-ls122` |
| Tautulli | `v2.18.2-ls247` |
| Nginx (stable) | `1.30.5-alpine` |

LinuxServer has [deprecated Overseerr](https://info.linuxserver.io/issues/2026-02-16-overseerr/)
in favor of Seerr. This stack retains Overseerr's final published release
on Docker Hub because that exact version tag is unavailable through LSCR.
Migrating to Seerr requires changing the image, config mount and permissions
according to its migration guide; do not substitute it blindly into this service.

Before upgrading, stop affected applications and back up their config/database
directories. Pull the pinned images, then run `up -d` to apply the update.
Database migrations may require restoring the backup to roll back.

## Boot persistence

Ensure `/opt/data` and `/mnt/media-library` are configured in `/etc/fstab`.
The systemd unit checks both mountpoints before starting the stack:

```bash
install -m 644 systemd/homelab.service /etc/systemd/system/homelab.service
systemctl daemon-reload
systemctl enable --now homelab.service
systemctl status homelab.service --no-pager
```

Run the installation commands as root. `active (exited)` is expected for this
oneshot unit. Containers use `on-failure`; systemd starts them at boot after
storage is available. Reboot persistence was verified on bb9b.

To stop the managed stack, use `systemctl stop homelab`. For configuration
updates while the unit is active, use the Compose `up -d` command above.

Keep Kubernetes Servarr deployments at zero while Compose owns the data.

## Pull and deploy

Run as root on bb9b:

```bash
cd /opt/data/homelab/repo
git pull --ff-only
cd compose
docker compose -f compose.yaml -f compose.proxy.yaml config --quiet
docker compose -f compose.yaml -f compose.proxy.yaml pull
docker compose -f compose.yaml -f compose.proxy.yaml up -d
docker compose -f compose.yaml -f compose.proxy.yaml up -d --no-deps --force-recreate nginx
docker compose -f compose.yaml -f compose.proxy.yaml ps -a
```

Git updates the files; Compose applies them to containers. Recreating Nginx
also rebinds its config file after Git replaces it. Back up application data
before image upgrades. If changing the systemd unit, reinstall it and run
`systemctl daemon-reload` as shown above. Keep edits to tracked files in Git;
local `.env`, certificates, configs and downloads stay outside the checkout.

After merging the migration pull request, switch the server checkout:

```bash
cd /opt/data/homelab/repo
git fetch origin main
git switch --track origin/main
```
