#!/usr/bin/env bash
# =============================================================================
# StudyAI — Linux/macOS Startup Script
# =============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "========================================================================="
echo "  StudyAI — Starting Django Backend & React Frontend"
echo "========================================================================="

# 1. If Node is installed, use unified runner
if command -v node >/dev/null 2>&1; then
    echo "[OK] Launching StudyAI via Unified Node Runner..."
    node start_all.js
    exit 0
fi

# 2. Fallback execution
VENV_PY="python3"
if [ -f "$DIR/.venv/bin/python" ]; then
    VENV_PY="$DIR/.venv/bin/python"
elif [ -f "$DIR/backend/venv/bin/python" ]; then
    VENV_PY="$DIR/backend/venv/bin/python"
fi

echo "[1/3] Applying Django Database Migrations..."
cd "$DIR/backend"
"$VENV_PY" manage.py migrate --noinput

echo "[2/3] Launching Django Backend on port 8000..."
"$VENV_PY" manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

echo "[3/3] Launching React Frontend on port 5173..."
cd "$DIR/frontend"
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "StudyAI is live at http://localhost:5173"
echo "Press Ctrl+C to stop servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true" EXIT INT TERM
wait
