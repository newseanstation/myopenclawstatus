#!/usr/bin/env bash
set -euo pipefail

APP="/home/k23linux/.openclaw/workspace/dist/X-linux"

if [ ! -x "$APP" ]; then
  echo "未找到可执行文件: $APP"
  echo "请先构建 Linux 版本。"
  exit 1
fi

exec "$APP"
