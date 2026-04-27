#!/usr/bin/env bash
# Start EvalForge Streamlit UI in the background
# Usage: ./scripts/ui_start.sh

VENV_PYTHON="$(pwd)/.venv/bin/python3"
PID_FILE=".ui.pid"
LOG_FILE="logs/ui.log"

# Guard: must be run from project root
if [ ! -f "$VENV_PYTHON" ]; then
  echo "❌ Venv not found at $VENV_PYTHON"
  echo "   Make sure you're running from the EvalForge/ root"
  exit 1
fi

if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
  echo "⚠️  UI is already running (PID $(cat $PID_FILE))"
  echo "   Run ./scripts/ui_stop.sh to stop it first"
  exit 1
fi

mkdir -p logs

"$VENV_PYTHON" -m streamlit run ui/app.py \
  --server.port 8501 \
  --server.headless true \
  > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

sleep 2

if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
  echo "✅ UI started (PID $(cat $PID_FILE))"
  echo "   App:  http://localhost:8501"
  echo "   Logs: tail -f $LOG_FILE"
else
  echo "❌ UI failed to start — check logs/ui.log"
  rm -f "$PID_FILE"
  exit 1
fi
