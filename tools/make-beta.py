#!/usr/bin/env python3
"""Build the β test channel (beta/) from the stable root app.

The beta channel lives at /taiwan-historical-maps/beta/ on the same GitHub
Pages site. It shares the heavy assets (icons/, data/) with the root app via
../ references, but has its own index.html, service worker (separate cache
namespace + scope) and manifest, so it installs as a separate PWA and can be
updated independently of the production app.

Beta-only features are injected here. (None at the moment: 街景漫遊 walk mode
graduated to the root app in 2026-11 and now lives in index.html.)

Usage:  python3 tools/make-beta.py     (from repo root)
"""
import re, os, sys, json, pathlib

# --native OUT ：輸出「原生打包用」變體 —— 含 β 功能（目前沒有），保留根目錄
# 相對路徑（icons/、data/），不掛 β 識別。給 Capacitor（iOS/Android）內嵌用。
NATIVE_OUT = None
argv = sys.argv[1:]
if '--native' in argv:
    NATIVE_OUT = argv[argv.index('--native') + 1]

ROOT = pathlib.Path(__file__).resolve().parent.parent
html = (ROOT / 'index.html').read_text(encoding='utf-8')

if not NATIVE_OUT:
    # ── 1. shared-asset paths: beta/ page reaches root assets via ../ ──
    html = re.sub(r'(["\'`(])icons/', r'\1../icons/', html)
    html = html.replace('src="data/postcards.js"', 'src="../data/postcards.js"')

    # ── 2. beta identity ──
    html = html.replace(
        '<title>台灣舊地圖散策 — Taiwan Old-Map Stroll</title>',
        '<title>台灣舊地圖散策 β — Beta Channel</title>\n<meta name="robots" content="noindex" />')
    html = html.replace(
        '<h1 class="head-zh">舊地圖散策</h1>',
        '<h1 class="head-zh">舊地圖散策 <span class="beta-tag">β</span></h1>')

# ── 3. 街景漫遊已在 2026-11 升上正式站，程式碼直接寫在 index.html，這裡不再注入。
#       β 頻道之後要試新功能，照同樣模式在這裡注入即可（記得防重複注入）。

# ── 6. write output ──
if NATIVE_OUT:
    pathlib.Path(NATIVE_OUT).write_text(html, encoding='utf-8')
    print('native variant (root paths) →', NATIVE_OUT)
    sys.exit(0)

beta = ROOT / 'beta'
beta.mkdir(exist_ok=True)
(beta / 'index.html').write_text(html, encoding='utf-8')

sw = (ROOT / 'sw.js').read_text(encoding='utf-8')
sw = sw.replace("tw-historical-shell-", "tw-beta-shell-")
sw = sw.replace("tw-historical-runtime-", "tw-beta-runtime-")
sw = sw.replace("tw-historical-tiles-", "tw-beta-tiles-")
sw = sw.replace("'tw-historical-pinned'", "'tw-beta-pinned'")
# only ever delete our own (tw-beta-*) stale caches — never production's
sw = sw.replace(
    "          // 同源的 β 測試頻道（/beta/）有自己的 tw-beta-* 快取——不是我們的，別動。\n"
    "          .filter(k => !k.startsWith('tw-beta-'))",
    "          // β 頻道只清自己的舊快取（tw-beta-*）；正式版的快取一律不動。\n"
    "          .filter(k => k.startsWith('tw-beta-'))")
# beta has its own version line so channels rev independently
sw = re.sub(r"const CACHE_VERSION = '[^']+'; //.*",
            "const CACHE_VERSION = 'beta15-2026-11-24'; // map reading notes",
            sw, count=1)
sw = sw.replace("""const SHELL_URLS = [
  './',
  './index.html',
  './data/postcards.js',
  './manifest.webmanifest',
  './icons/icon.svg',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-180.png',
];""", """const SHELL_URLS = [
  './',
  './index.html',
  './manifest.webmanifest',
  '../data/postcards.js',
  '../icons/icon.svg',
  '../icons/icon-192.png',
  '../icons/icon-512.png',
  '../icons/icon-180.png',
];""")
(beta / 'sw.js').write_text(sw, encoding='utf-8')

manifest = {
  "name": "台灣舊地圖散策 β — Beta",
  "short_name": "散策β",
  "description": "台灣舊地圖散策的搶先測試版：最新實驗功能先在這裡登場。",
  "lang": "zh-Hant", "dir": "ltr",
  "start_url": "./", "scope": "./", "display": "standalone",
  "theme_color": "#F1EFE9", "background_color": "#F1EFE9",
  "icons": [
    {"src": "../icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
    {"src": "../icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
    {"src": "../icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
  ]
}
(beta / 'manifest.webmanifest').write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

print('beta/ built:', sorted(p.name for p in beta.iterdir()))
