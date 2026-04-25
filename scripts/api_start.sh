#!/usr/bin/env bash
# Start EvalForge API in the background
# Usage: ./scripts/api_start.sh

PID_FILE=".api.pid"
LOG_FILE="logs/api.log"

if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
  echo "⚠️  API is already running (PID $(cat $PID_FILE))"
  echo "   Run ./scripts/api_stop.sh to stop it first"
  exit 1
fi

mkdir -p logs

python3 -m uvicorn api.main:app --reload --port 8000 > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

sleep 1  # give it a moment to start

if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
  echo "✅ API started (PID $(cat $PID_FILE))"
  echo "   Docs:  http://localhost:8000/docs"
  echo "   Logs:  tail -f $LOG_FILE"
else
  echo "❌ API failed to start — check logs/api.log"
  rm -f "$PID_FILE"
  exit 1
fi
