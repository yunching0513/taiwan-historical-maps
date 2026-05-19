#!/bin/bash
# Generate 5 phone screenshots for Google Play submission.
# 540×960 viewport (triggers mobile UI) rendered at 2× scale → 1080×1920 PNG.

set -euo pipefail

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE="${BASE:-https://yunching0513.github.io/taiwan-historical-maps}"
OUT="$(cd "$(dirname "$0")" && pwd)/screenshots"
mkdir -p "$OUT"

shoot () {
  local name="$1"
  local query="$2"
  local delay="${3:-9000}"
  local url="${BASE}/?${query}"
  echo "▸ $name  ←  $url"
  "$CHROME" \
    --headless=new --disable-gpu --hide-scrollbars \
    --window-size=540,960 \
    --force-device-scale-factor=2 \
    --user-agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1" \
    --virtual-time-budget="$delay" \
    --screenshot="$OUT/$name.png" \
    "$url" >/dev/null 2>&1
  echo "  → $OUT/$name.png ($(stat -f %z "$OUT/$name.png" 2>/dev/null) bytes)"
}

# 01  Hero: Tainan + satellite + 1904 — main feature in one shot
shoot 01-hero       "city=tainan&base=satellite&layer=jm20k_1904"             12000

# 02  Full panel: 19 layers visible, panel open
shoot 02-layers     "city=taipei&layer=jm20k_1904&panel=open"                 10000

# 03  City picker open: 22 cities grouped by region
shoot 03-cities     "city=taichung&picker=open"                                9000

# 04  Mobile peek state in Kaohsiung with title visible
shoot 04-stroll     "city=kaohsiung&layer=jm25k_1921"                          10000

# 05  Plain base in Tainan (no historical) — emphasises the mobile UI itself
shoot 05-modern     "city=hualien"                                              8000

echo ""
echo "✓ All screenshots written to $OUT"
ls -la "$OUT"
