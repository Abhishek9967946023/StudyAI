#!/usr/bin/env bash
# =============================================================================
# StudyAI — First-Time Environment Setup (Linux / macOS)
# =============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "========================================================================="
echo "  StudyAI — Automated Environment Setup & Prerequisite Verification"
echo "========================================================================="
echo ""

# 1. Check Python
echo "[1/7] Checking Python prerequisite..."
PYTHON_BIN=""
for cmd in python3.12 python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        ver=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -eq 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON_BIN="$cmd"
            echo "  Found: $($cmd --version)"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "  [ERROR] Python 3.10+ (recommended: 3.12) is required but was not found."
    echo "  Please install Python 3.12 via your package manager (brew, apt, pacman)."
    exit 1
fi

# 2. Check Node & npm
echo ""
echo "[2/7] Checking Node.js and npm..."
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    echo "  [ERROR] Node.js and npm are required. Please install Node.js 20+ (LTS)."
    exit 1
fi
echo "  Node.js: $(node --version)"
echo "  npm:     v$(npm --version)"

# 3. Create Virtual Environment
echo ""
echo "[3/7] Setting up Python virtual environment..."
VENV_DIR="$DIR/.venv"
if [ ! -f "$VENV_DIR/bin/python" ]; then
    if [ -f "$DIR/backend/venv/bin/python" ]; then
        VENV_DIR="$DIR/backend/venv"
        echo "  Found existing virtual environment at backend/venv."
    else
        echo "  Creating clean virtual environment in .venv ..."
        $PYTHON_BIN -m venv "$VENV_DIR"
    fi
fi
VENV_PY="$VENV_DIR/bin/python"

# 4. Install Backend Dependencies
echo ""
echo "[4/7] Installing backend dependencies from backend/requirements.txt..."
"$VENV_PY" -m pip install --upgrade pip >/dev/null 2>&1
"$VENV_PY" -m pip install -r "$DIR/backend/requirements.txt"
echo "  [OK] Backend dependencies installed."

# 5. Install Frontend Dependencies
echo ""
echo "[5/7] Installing frontend dependencies..."
cd "$DIR/frontend"
if [ -f "package-lock.json" ]; then
    npm ci || npm install
else
    npm install
fi
cd "$DIR"
echo "  [OK] Frontend dependencies installed."

# 6. Configure Environment File (.env)
echo ""
echo "[6/7] Checking environment configuration (.env)...
if [ ! -f "$DIR/.env" ]; then
    if [ -f "$DIR/.env.example" ]; then
        echo "  Creating .env from .env.example ..."
        cp "$DIR/.env.example" "$DIR/.env"
        echo "  [OK] Created .env template."
    fi
else
    echo "  [OK] Existing .env file preserved."
fi

# 7. Apply Database Migrations & Diagnostics
echo ""
echo "[7/7] Applying database migrations and running system diagnostic..."
cd "$DIR/backend"
"$VENV_PY" manage.py migrate --noinput
"$VENV_PY" manage.py check_configuration
cd "$DIR"

echo ""
echo "========================================================================="
echo "  🎉 StudyAI Setup Completed Successfully!"
echo "========================================================================="
echo "  To start StudyAI, run:"
echo "      ./start_studyai.sh"
echo "  or:"
echo "      npm start"
echo "========================================================================="
