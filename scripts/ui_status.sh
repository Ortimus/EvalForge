#!/usr/bin/env bash
# Check EvalForge Streamlit UI status
# Usage: ./scripts/ui_status.sh

PID_FILE=".ui.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "⭕ UI is not running"
  exit 0
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
  echo "✅ UI is running (PID $PID)"
  echo "   App:  http://localhost:8501"
  echo "   Logs: tail -f logs/ui.log"
else
  echo "⭕ UI is not running (stale PID file — cleaning up)"
  rm -f "$PID_FILE"
fi
