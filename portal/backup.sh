#!/bin/bash
# Backup dunia otomatis (dijalankan cron via portal). Simpan 7 terbaru.
set -u
MC=/home/hatch/workspace/minecraft/server
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p "$MC/backups"
cd "$MC" || exit 1
dirs=""
for d in world world_nether world_the_end; do
  [ -d "$d" ] && dirs="$dirs $d"
done
[ -z "$dirs" ] && exit 0
tar -czf "backups/world-auto-$TS.tar.gz" $dirs 2>/dev/null
ls -t backups/world-auto-*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm -f
