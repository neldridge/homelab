# Deploy this media stack with Codex

Clone this repository, open the clone in Codex, and use the following prompt.
This supports a fresh Linux deployment or migration of an existing installation.
The checked-in configuration describes the maintainer's working deployment;
its addresses, domains, mountpoints, and user IDs must be adapted to your host.

---

Deploy the Docker Compose media stack in this repository on my server.
Read `compose/README.md`, both Compose files, `compose/.env.example`,
`compose/nginx/default.conf`, and `compose/systemd/homelab.service` first.
Do not apply the Kubernetes Terraform to deploy this stack.

Work in small steps. Inspect what is already available before asking me to
provide information. Ask only for missing choices, explain what each step
accomplishes, and verify the result before moving on. Use available terminal
access directly. If I must run a command, give me one complete pasteable block
and read its output before continuing. Never claim a deployment or test passed
without checking it.

## Discover and adapt

1. Establish the intended server, SSH account, Linux distribution, CPU
   architecture, Docker/Compose availability, privilege level, available disk
   space, current containers, and occupied ports. Distinguish my workstation
   from the target server. Do not assume sudo or root access.
2. Determine whether this is a fresh installation or a migration. Identify
   the existing Plex URL, chosen services, timezone, runtime UID/GID, deployment
   directory, local config/download directories, and movie/TV library paths.
   Plex runs separately; do not install Plex or change its host unless I ask.
3. Ask for my internal service domain and whether requests need public access.
   Replace the maintainer's `a3f.link`, `requests.neldridge.net`, IP addresses,
   public port 3579, and systemd mountpaths with my choices. Do not configure
   DNS or router forwarding against the maintainer's infrastructure.
4. Check the chosen image pins exist and support my architecture. Use stable
   releases and explicit version tags plus digests. Do not invent tags, fall
   back silently to `latest`, or upgrade application databases during discovery.
   Overseerr's LinuxServer image is deprecated: explain the Seerr successor
   and agree on the requests application before deploying a fresh installation
   or migrating existing requests data. Follow that application's official
   mount, permissions, and migration instructions if changing images.

## Prepare storage and configuration

5. Keep configs/databases and temporary downloads on local storage. Put final
   movies and TV in the selected library, which may be local or NFS. Preserve
   consistent container paths: `/downloads`, `/movies`, `/tv`. Remove unused
   `/books` mounts if I do not have a Books directory. Keep the existing
   `plexmetamanager` config directory when migrating Kometa, or adjust its bind
   source explicitly for a fresh installation.
6. For migrations, stop only the source services being migrated, then make a
   dated backup of their configs/databases and required download queue state.
   Never mount a block filesystem read/write on two hosts. Preserve the
   original backup and source volumes until the new setup is verified.
   Do not replace existing configs with blank files or recursively change
   ownership of my entire library. Back up configs before upgrades; reverting
   an image alone may not undo a database migration.
7. For fresh installations, create only the required bind directories on the
   intended mounted filesystems. Populate `.env` from `.env.example` using my
   paths and IDs. Keep `create_host_path: false`. Verify reads and writes using
   the actual runtime UID/GID. The checked-in NZBGet port is 6790; a fresh
   NZBGet installation may listen on 6789. Make its saved ControlPort, Compose
   port mapping, Nginx upstream, and download-client connections consistent.
8. Keep passwords, API tokens, application databases, `.env`, ACME account
   credentials, and TLS private keys out of Git and tool output. Use private
   local files or hidden input for secrets. Configure NZBGet log rotation and
   preserve the Compose log size limits.

## Deploy and connect

9. Prepare valid TLS certificates for my chosen hostnames using an appropriate
   ACME method. Set up and verify renewal and Nginx reload. Do not start the
   checked-in HTTPS proxy until its certificate files exist. For local-only
   deployments, agree on a suitable local certificate/trust method or an
   explicit temporary HTTP configuration. Never bypass certificate checking
   and describe the result as working TLS.
10. Validate the adapted Compose configuration, pull its pinned images, and
    start the selected services. Use both Compose files when running Nginx.
    Check container state and application logs. Nginx uses Docker DNS for
    service upstreams, and routes applications by hostname. DNS should resolve
    to the target server. Public request access needs the correct hostname,
    certificate, proxy headers, and router forwarding; expose only the intended
    service. Do not modify router/DNS accounts without authorization.
11. Complete initial application setup or retain migrated settings. Configure
    authentication. Within Compose use service DNS names: Sonarr `sonarr:8989`,
    Radarr `radarr:7878`, Prowlarr `prowlarr:9696`, and NZBGet at its confirmed
    port. Set allowed hostnames and connect services with their API keys without
    printing keys. Ensure download categories and paths agree between clients.
12. Connect the requests application to Plex, Sonarr, and Radarr. Connect
    Tautulli to Plex. Configure Bazarr connections, subtitle providers, language
    profiles, and assignments. If Kometa is selected, configure its Plex token,
    libraries, optional provider keys, and schedule. Run at most one Kometa
    validation job at a time; following its logs does not stop the job. Inspect
    the final run summary before starting the scheduled container. Do not reset
    Plex posters or delete existing collections without my instruction.

## Verify and make persistent

13. Check application login, inter-service connection tests, library access,
    and proxy TLS/host routing. Where I have suitable content, verify a download
    and completed import to the library, then Plex visibility/playback. Check
    public requests from outside the LAN if public access is configured. Report
    any test that cannot be performed rather than assuming success.
14. Adapt the systemd unit's WorkingDirectory and required mountpoints. Ensure
    mounts persist in fstab without reformatting disks. The checked-in
    `on-failure` policies rely on systemd to start the stack after mounts at
    boot. Validate and enable the unit. When I am ready for the interruption,
    reboot, wait for SSH, and verify mounts, unit state, containers, and routes
    came back automatically. Do not reboot during an active transfer or Kometa
    run without coordinating with me.
15. Document my deployment paths, versions, operating commands, backup/restore
    procedure, and certificate renewal. Commit only non-secret configuration
    and documentation. Leave unrelated repository edits intact. Summarize
    what was deployed, what was tested, and any outstanding work.

Start by inspecting this repository and available server access, then ask for
the missing deployment details.
