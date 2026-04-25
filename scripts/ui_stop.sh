#!/usr/bin/env bash
# Stop EvalForge Streamlit UI
# Usage: ./scripts/ui_stop.sh

PID_FILE=".ui.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "⚠️  No PID file found — UI may not be running"
  exit 0
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  rm -f "$PID_FILE"
  echo "✅ UI stopped (PID $PID)"
else
  echo "⚠️  Process $PID not found — cleaning up stale PID file"
  rm -f "$PID_FILE"
fi
