# Media services on Compose

Working deployment migrated from MicroK8s on October 11, 2026. Runs on
bb9b (192.168.11.10). Plex stays on its separate host.

Services: Sonarr, Radarr, Prowlarr, Bazarr, Overseerr, NZBGet, Tautulli,
Kometa, and Nginx. Muximux and HTPC Manager were retired.

## Files and storage

Deploy the contents of this directory to `/opt/data/homelab` on the server.
Copy `.env.example` to `.env` and adjust the host paths and UID/GID if needed.
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

From `/opt/data/homelab`:

```bash
docker compose -f compose.yaml -f compose.proxy.yaml config --quiet
docker compose -f compose.yaml -f compose.proxy.yaml up -d
docker compose -f compose.yaml -f compose.proxy.yaml ps -a
```

Both Compose files are needed to include Nginx. Most images are pinned by
digest; Nginx currently uses `stable-alpine`.

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
