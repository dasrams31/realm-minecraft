#!/bin/bash
# Backup harian realm-minecraft ke GitHub
# Dijalankan via cron tiap hari. Token dibaca dari config/github_token (chmod 600).
set -e
STAGE="$HOME/workspace/releases/realm-minecraft"
TOKEN_FILE="$HOME/workspace/mc-portal/config/github_token"

# 1. Sync file terbaru
cp "$HOME/workspace/mc-portal/portal.py" "$STAGE/portal/"
cp "$HOME/workspace/mc-portal"/make_*.py "$STAGE/portal/"
rm -rf "$STAGE/portal/static" && cp -r "$HOME/workspace/mc-portal/static" "$STAGE/portal/"
cp "$HOME/workspace/mc-portal/backup.sh" "$STAGE/portal/" 2>/dev/null || true
cp "$HOME/workspace/minecraft/server/server.properties" "$STAGE/server-config/"
cp "$HOME/workspace/minecraft/server/bukkit.yml" "$STAGE/server-config/" 2>/dev/null || true
cp "$HOME/workspace/minecraft/server/spigot.yml" "$STAGE/server-config/" 2>/dev/null || true

# 2. Commit jika ada perubahan
cd "$STAGE"
git add -A
if git diff --cached --quiet; then
  echo "no changes"
  exit 0
fi
git -c user.name="dasrams31" -c user.email="ramadanadipa176@gmail.com" \
  commit -qm "Daily backup $(date +%F)"

# 3. Push
TOKEN="$(cat "$TOKEN_FILE")"
git push "https://dasrams31:${TOKEN}@github.com/dasrams31/realm-minecraft.git" main 2>&1 | tail -2
echo "pushed $(date -Is)"
