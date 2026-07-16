#!/usr/bin/env bash
# Build a standalone Windows release package
# Creates openjyotish-windows.zip with everything needed to run
set -e

VERSION=$(python3 -c "import jhora; print(jhora.__version__)" 2>/dev/null || echo "1.1.0")
RELEASE="openjyotish-v${VERSION}-windows"
TMPDIR="/tmp/$RELEASE"

echo "Building $RELEASE..."

rm -rf "$TMPDIR"
mkdir -p "$TMPDIR/jhcore/ephe"

# Copy source
rsync -a --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
      --exclude 'venv' --exclude '*.egg-info' \
      src/ "$TMPDIR/src/"

# Copy config
cp pyproject.toml requirements.txt README.md LICENSE "$TMPDIR/" 2>/dev/null || true

# Copy install scripts
cp install.bat run.bat "$TMPDIR/"

# Copy minimal ephemeris for 1950-2050
echo "Copying ephemeris data..."
for f in jhcore/ephe/sepl_*.se1 jhcore/ephe/semo_*.se1; do
    # Only copy files covering 1950-2050 (files 24-96)
    num=$(echo "$f" | grep -oP '\d+' | head -1)
    if [ "$num" -ge 18 ] && [ "$num" -le 108 ]; then
        cp "$f" "$TMPDIR/jhcore/ephe/" 2>/dev/null || true
    fi
done

# Copy database
cp data/jhora.db "$TMPDIR/data/" 2>/dev/null || true

# Create Windows launcher batch file
cat > "$TMPDIR/OpenJyotish.bat" << 'EOF'
@echo off
title OpenJyotish
if not exist venv\ (
    echo First run: setting up...
    call install.bat
)
call venv\Scripts\activate.bat 2>nul || (
    echo Please run install.bat first to set up Python dependencies.
    pause
    exit /b 1
)
python -m jhora --gui
pause
EOF

# Create zip using Python
python3 -c "
import zipfile, os
zf = zipfile.ZipFile('/tmp/$RELEASE.zip', 'w', zipfile.ZIP_DEFLATED)
for root, dirs, files in os.walk('/tmp/$RELEASE'):
    for f in files:
        path = os.path.join(root, f)
        arcname = os.path.relpath(path, '/tmp')
        zf.write(path, arcname)
zf.close()
"

SIZE=$(du -sh "$RELEASE.zip" | cut -f1)
echo
echo "Done: /tmp/$RELEASE.zip ($SIZE)"
echo
echo "Upload to GitHub Releases: https://github.com/velteyn/OpenJyotish/releases/new"
