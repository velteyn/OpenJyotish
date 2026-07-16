#!/usr/bin/env bash
# Download required Swiss Ephemeris data files
# These are NOT in git — they must be downloaded separately
set -e

DEST="jhcore/ephe"
mkdir -p "$DEST"

BASE="https://www.astro.com/ftp/swisseph/ephe"

# Files needed for 1900-2100 (minimum set)
FILES=(
    # Planets (required — 1 per 600 years)
    sepl_18.se1 sepl_24.se1 sepl_30.se1 sepl_36.se1 sepl_42.se1
    sepl_48.se1 sepl_54.se1 sepl_60.se1 sepl_66.se1 sepl_72.se1
    sepl_78.se1 sepl_84.se1 sepl_90.se1 sepl_96.se1
    sepl_102.se1 sepl_108.se1 sepl_114.se1 sepl_120.se1
    sepl_126.se1 sepl_132.se1
    # Moon (required — 1 per 2 years for 1900-2100)
    semo_18.se1 semo_24.se1 semo_30.se1 semo_36.se1 semo_42.se1
    semo_48.se1 semo_54.se1 semo_60.se1 semo_66.se1 semo_72.se1
    semo_78.se1 semo_84.se1 semo_90.se1 semo_96.se1
    semo_102.se1 semo_108.se1 semo_114.se1 semo_120.se1
    semo_126.se1 semo_132.se1
    # Main asteroids (optional but useful)
    seas_18.se1 seas_24.se1
    # Fixed stars (optional)
    sefx_18.se1 sefx_24.se1
)

echo "Downloading Swiss Ephemeris data ($DEST)..."
echo "Files: ${#FILES[@]}"
echo

for f in "${FILES[@]}"; do
    if [ -f "$DEST/$f" ]; then
        echo "  skip $f (exists)"
        continue
    fi
    echo "  downloading $f..."
    curl -sS -o "$DEST/$f" "$BASE/$f" || wget -q -O "$DEST/$f" "$BASE/$f"
done

echo
echo "Done. Ephemeris files in $DEST/"
ls "$DEST"/*.se1 2>/dev/null | wc -l | xargs echo "Total files:"
