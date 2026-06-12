#!/usr/bin/env bash
# 把 repo 根目錄的 PWA 複製進 ios-app/www，作為 iOS App 內嵌的網頁內容。
# 每次根目錄的 index.html 有更新，重跑一次再 `npx cap sync ios` 即可。
set -euo pipefail
cd "$(dirname "$0")"

rm -rf www
mkdir -p www
cp ../index.html ../manifest.webmanifest ../sw.js www/
cp -R ../icons www/icons

echo "✓ www/ 已同步（index.html + icons + manifest + sw.js）"
