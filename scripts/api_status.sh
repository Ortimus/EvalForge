#!/usr/bin/env bash
# Check EvalForge API status
# Usage: ./scripts/api_status.sh

PID_FILE=".api.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "⭕ API is not running"
  exit 0
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
  echo "✅ API is running (PID $PID)"
  echo "   Docs: http://localhost:8000/docs"
  echo "   Logs: tail -f logs/api.log"
else
  echo "⭕ API is not running (stale PID file — cleaning up)"
  rm -f "$PID_FILE"
fi
