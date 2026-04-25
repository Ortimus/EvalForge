#!/usr/bin/env bash
# Stop EvalForge API
# Usage: ./scripts/api_stop.sh

PID_FILE=".api.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "⚠️  No PID file found — API may not be running"
  exit 0
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  rm -f "$PID_FILE"
  echo "✅ API stopped (PID $PID)"
else
  echo "⚠️  Process $PID not found — cleaning up stale PID file"
  rm -f "$PID_FILE"
fi
