#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
JAR="$DIR/@JAR_NAME@"
PID_FILE="$DIR/app.pid"
LOG_DIR="$DIR/logs"
mkdir -p "$LOG_DIR"
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "already running pid=$(cat "$PID_FILE")"
  exit 0
fi
nohup java -jar "$JAR" >> "$LOG_DIR/app.log" 2>&1 &
echo $! > "$PID_FILE"
echo "started pid=$(cat "$PID_FILE")"
