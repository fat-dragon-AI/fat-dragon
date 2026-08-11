#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$DIR/app.pid"
if [[ ! -f "$PID_FILE" ]]; then
  echo "no pid file"
  exit 0
fi
PID="$(cat "$PID_FILE")"
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID" || true
  sleep 2
  kill -9 "$PID" 2>/dev/null || true
fi
rm -f "$PID_FILE"
echo "stopped"
