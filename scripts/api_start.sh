#!/usr/bin/env bash
# Start EvalForge API in the background
# Usage: ./scripts/api_start.sh

VENV_PYTHON="$(pwd)/.venv/bin/python3"
PID_FILE=".api.pid"
LOG_FILE="logs/api.log"

# Guard: must be run from project root
if [ ! -f "$VENV_PYTHON" ]; then
  echo "❌ Venv not found at $VENV_PYTHON"
  echo "   Make sure you're running from the EvalForge/ root"
  echo "   and have run: python3 -m venv .venv && pip install -r requirements.txt"
  exit 1
fi

if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
  echo "⚠️  API is already running (PID $(cat $PID_FILE))"
  echo "   Run ./scripts/api_stop.sh to stop it first"
  exit 1
fi

mkdir -p logs

"$VENV_PYTHON" -m uvicorn api.main:app --reload --port 8000 > "$LOG_FILE" 2>&1 &
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
