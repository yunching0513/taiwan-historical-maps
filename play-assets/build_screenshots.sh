#!/bin/bash
# Generate 5 phone screenshots (1080×1920) for Google Play submission.
# Drives the LIVE deployed site via Chrome headless. Uses the deep-link
# query params we added so each screenshot lands in the right state.

set -euo pipefail

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE="${BASE:-https://yunching0513.github.io/taiwan-historical-maps}"
OUT="$(cd "$(dirname "$0")" && pwd)/screenshots"
mkdir -p "$OUT"

shoot () {
  local name="$1"
  local query="$2"
  local delay="${3:-8000}"
  local url="${BASE}/?${query}"
  echo "▸ $name  ←  $url"
  "$CHROME" \
    --headless=new --disable-gpu --hide-scrollbars \
    --window-size=1080,1920 \
    --virtual-time-budget="$delay" \
    --screenshot="$OUT/$name.png" \
    "$url" >/dev/null 2>&1
  echo "  → $OUT/$name.png ($(stat -f %z "$OUT/$name.png" 2>/dev/null) bytes)"
}

# 01  Tainan with the 1904 Taiwan Daichō overlay — the killer scene
shoot 01-hero       "city=tainan&layer=jm20k_1904"                    10000

# 02  City picker open, showing all 22 cities grouped by region
shoot 02-cities     "city=taichung&picker=open"                       8000

# 03  Satellite base + 1904 overlay — modern aerial vs century-old layout
shoot 03-satellite  "city=tainan&base=satellite&layer=jm20k_1904"     12000

# 04  Kaohsiung with 1944 U.S. Army map
shoot 04-army       "city=kaohsiung&layer=am25k_1944a"                10000

# 05  Taipei with CORONA 1966 satellite imagery — cold-war reveal
shoot 05-corona     "city=taipei&layer=corona_1966"                   10000

echo ""
echo "✓ All screenshots written to $OUT"
ls -la "$OUT"
