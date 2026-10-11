#!/usr/bin/env bash
# Switch the existing bb9b installation to a checkout without moving app data.
set -euo pipefail

[[ $(id -u) -eq 0 ]] || { echo 'Run this on bb9b as root.'; exit 1; }
runtime=/opt/data/homelab
repo="$runtime/repo"
branch="${HOMELAB_BRANCH:-neldridge/composemigration}"
mountpoint -q /opt/data
mountpoint -q /mnt/media-library
test -f "$runtime/.env"
test -f "$runtime/nginx/certs/fullchain.pem"
test -f "$runtime/nginx/certs/requests/fullchain.pem"

if [[ -e "$repo" ]]; then
    test -d "$repo/.git"
    [[ $(git -C "$repo" branch --show-current) == "$branch" ]]
    [[ -z $(git -C "$repo" status --porcelain) ]] || {
        echo 'STOP: checkout has local changes; preserve them before updating.'
        exit 1
    }
    git -C "$repo" pull --ff-only origin "$branch"
else
    git clone --branch "$branch" https://github.com/neldridge/homelab.git "$repo"
fi

# Symlinks are ignored by Git. Secrets remain in the original runtime tree.
for path in "$repo/compose/.env" "$repo/compose/nginx/certs"; do
    [[ ! -e "$path" && ! -L "$path" ]] || [[ -L "$path" ]] || {
        echo "STOP: refusing to replace existing $path"
        exit 1
    }
done
ln -sfn "$runtime/.env" "$repo/compose/.env"
ln -sfn "$runtime/nginx/certs" "$repo/compose/nginx/certs"

cd "$repo/compose"
docker compose -f compose.yaml -f compose.proxy.yaml config --quiet
docker compose -f compose.yaml -f compose.proxy.yaml run --rm -T --no-deps nginx nginx -t

backup="$runtime/git-switch-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 "$backup"
cp -a /etc/systemd/system/homelab.service "$backup/"
cp -a "$runtime/compose.yaml" "$runtime/compose.proxy.yaml" "$backup/"
install -m 644 systemd/homelab.service /etc/systemd/system/homelab.service
systemctl daemon-reload
docker compose -f compose.yaml -f compose.proxy.yaml up -d
systemctl enable homelab.service
systemctl start homelab.service
docker compose -f compose.yaml -f compose.proxy.yaml ps -a
printf '\nCheckout: %s\nPrevious deployment backup: %s\n' "$repo" "$backup"
