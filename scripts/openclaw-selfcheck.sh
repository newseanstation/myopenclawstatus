#!/usr/bin/env bash
set -euo pipefail

echo "=== OpenClaw Selfcheck ==="
date

echo "\n[1] OpenClaw status (summary)"
openclaw status | sed -n '1,80p'

echo "\n[2] Core tools"
for c in git curl wget unzip 7z htop python3 pip3 cmake node npm ffmpeg jq rg fdfind tmux tree rsync; do
  if command -v "$c" >/dev/null 2>&1; then
    printf "[OK] %s\n" "$c"
  else
    printf "[MISSING] %s\n" "$c"
  fi
done

echo "\n[3] NTFS drive check (if mounted)"
if lsblk -f | grep -qi ntfs; then
  lsblk -f | grep -i ntfs || true
  if mount | grep -q '/mnt/shawn'; then
    echo "[OK] /mnt/shawn mounted"
    ls -la /mnt/shawn | sed -n '1,20p'
  else
    echo "[INFO] NTFS detected but /mnt/shawn is not mounted"
  fi
else
  echo "[INFO] No NTFS volume detected"
fi

echo "\n[4] Cron jobs"
openclaw cron list || true

echo "\nDone."
