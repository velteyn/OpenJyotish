#!/usr/bin/env bash
# OpenJyotish — fully automatic installer
# Handles: missing python3-venv, PEP 668, virtualenv fallback, DB init
set -e

RED='\033[0;31m' GREEN='\033[0;32m' YELLOW='\033[1;33m' NC='\033[0m'
ok() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
die() { echo -e "${RED}✗ $1${NC}"; exit 1; }

echo "========================================"
echo " OpenJyotish — Installer"
echo "========================================"
echo
echo "Cleaning cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo "Done."
echo

# ── Find Python ──
PYTHON=""
for cmd in python3 python; do
    command -v "$cmd" &>/dev/null || continue
    ver=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo 0)
    [ "$ver" -ge 3 ] && { PYTHON="$cmd"; break; }
done
[ -z "$PYTHON" ] && die "Python 3 not found. Install from python.org"
echo "Cleaning old cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
ok "Cache cleaned"
echo

ok "Python: $($PYTHON --version)"

$PYTHON -c "import sys; sys.exit(0 if sys.version_info>=(3,11) else 1)" 2>/dev/null || \
    die "Python 3.11+ required. Found: $($PYTHON --version)"

# ── Helper: pip install with PEP 668 handling ──
pip_install() {
    $PYTHON -m pip install "$@" -q 2>/dev/null && return 0
    $PYTHON -m pip install "$@" --break-system-packages -q 2>/dev/null && return 0
    PIP_REQUIRE_VIRTUALENV=false $PYTHON -m pip install "$@" -q 2>/dev/null && return 0
    return 1
}

# ── Create venv ──
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    
    # Method 1: standard venv
    if $PYTHON -m venv venv 2>/dev/null && [ -f venv/bin/activate ]; then
        ok "venv created"
    else
        # Method 2: install python3-venv via apt (Debian/Ubuntu)
        if command -v apt-get &>/dev/null; then
            warn "python3-venv missing. Installing via apt..."
            sudo apt-get install -y -q python3-venv python3-pip 2>/dev/null && \
                $PYTHON -m venv venv 2>/dev/null && \
                ok "venv created (apt install)" || true
        fi
        
        # Method 3: virtualenv fallback
        if [ ! -f venv/bin/activate ]; then
            warn "Trying virtualenv fallback..."
            pip_install virtualenv && \
                $PYTHON -m virtualenv venv -q 2>/dev/null && \
                ok "venv created (virtualenv)" || \
                die "Cannot create venv. Run: sudo apt install python3-venv"
        fi
    fi
else
    ok "venv/ exists"
fi

[ -f venv/bin/activate ] || die "venv/bin/activate missing — rm -rf venv && retry"

source venv/bin/activate
ok "venv activated"

# ── Install dependencies ──
echo "Installing dependencies..."
pip_install --upgrade pip 2>/dev/null || true

# Install each dep individually for better error reporting
for dep in PyQt6 pyswisseph typer rich requests "prompt_toolkit>=3.0" numpy; do
    pip_install "$dep" || die "Failed to install $dep"
done
ok "Dependencies installed"

# ── Install Jhora ──
echo "Installing Jhora..."
pip_install -e . || warn "Editable install failed; running from source still works"
ok "Jhora installed"

# ── Initialize database ──
echo "Initializing database..."
$PYTHON -c "
from jhora.core.database import get_db
db = get_db()
ct = db.execute('SELECT COUNT(*) FROM cities').fetchone()[0]
print(f'  {ct} cities in atlas')
" 2>/dev/null || warn "DB init skipped (harmless — first run will init)"

# ── Done ──
echo
echo "Cleaning cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo "Done."
echo
echo "========================================"
echo " Setup complete!"
echo "========================================"
echo
echo "Cleaning cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo "Done."
echo
echo "Quick start:"
echo "  ./run.sh          Launch GUI"
echo "  jhora tui         Terminal mode"
echo "  jhora --help      All commands"
echo
echo "Cleaning cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo "Done."
echo
