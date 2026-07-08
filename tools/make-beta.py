#!/usr/bin/env python3
"""Build the β test channel (beta/) from the stable root app.

The beta channel lives at /taiwan-historical-maps/beta/ on the same GitHub
Pages site. It shares the heavy assets (icons/, data/) with the root app via
../ references, but has its own index.html, service worker (separate cache
namespace + scope) and manifest, so it installs as a separate PWA and can be
updated independently of the production app.

Beta-only features are injected here (currently: 街景漫遊 walk mode — the
historical map rendered as a perspective ground plane under your feet).

Usage:  python3 tools/make-beta.py     (from repo root)
"""
import re, os, sys, json, pathlib

# --native OUT ：輸出「原生打包用」變體 —— 含 β 功能（街景漫遊），但保留根目錄
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

# ── 3. walk-mode CSS (before the closing </style> of the main stylesheet) ──
WALK_CSS = """
  /* ── β 測試版標記 + 街景漫遊 walk mode ─────────────── */
  .beta-tag{display:inline-block;font-family:var(--mono);font-size:11px;color:#fff;
    background:var(--vermilion);border-radius:3px;padding:1px 6px;vertical-align:8px;letter-spacing:.05em}
  /* 背景一律用紙色：平面旋轉時若露出缺角，看起來是「霧」不是黑色破洞
     （Android 實測：黑底 + 旋轉缺角 = 黑白交替閃爍感） */
  .walk-overlay{position:fixed;inset:0;z-index:9600;display:none;background:#EDE0C4;overflow:hidden}
  .walk-overlay.show{display:block}
  .walk-sky{position:absolute;left:0;top:0;right:0;height:27%;
    background:linear-gradient(180deg,#c9c0ab 0%,#e2d7bd 70%,#EDE0C4 100%)}
  .walk-groundwrap{position:absolute;left:0;right:0;top:26%;bottom:0;overflow:hidden;
    background:#EDE0C4;perspective:640px;perspective-origin:50% 0}
  /* 不用 preserve-3d：子層(#walk-map)只做 2D rotateZ，沒有巢狀 3D。
     preserve-3d 在 Android WebView 會建立昂貴且會 z 序錯亂的 3D 合成脈絡，
     是 HUD 偶爾被地圖蓋掉（閃爍）的元兇。 */
  #walk-tilt{position:absolute;inset:0;transform:rotateX(60deg);transform-origin:50% 0}
  #walk-map{position:absolute;left:-30%;top:-60%;width:160%;height:230%;background:#EDE0C4;
    transform-origin:50% 78%;backface-visibility:hidden}
  /* HUD 一律提升成獨立合成層，地圖重繪時不會被捲進去一起重畫/搶繪 */
  .walk-chip,.walk-close,.walk-compass,.walk-op,.walk-hint,.walk-feet,.walk-fog,.walk-sky{
    will-change:transform;transform:translateZ(0)}
  /* 霧帶：從地平線往下鋪一大片，把覆蓋最差、最模糊的遠方地面藏進霧裡，
     只留下圖磚扎實的近—中景。這是「有界近景」設計的視覺收尾。 */
  .walk-fog{position:absolute;left:0;right:0;top:calc(26% - 70px);height:230px;pointer-events:none;z-index:4;
    background:linear-gradient(180deg,rgba(237,224,196,1) 0%,rgba(237,224,196,1) 26%,rgba(237,224,196,.85) 52%,rgba(237,224,196,0) 100%)}
  .walk-chip{position:absolute;font-family:var(--mono);font-size:13px;letter-spacing:.12em;color:#E0A96D;
    background:rgba(25,20,14,.62);border:1px solid rgba(224,169,109,.45);padding:6px 12px;border-radius:3px;z-index:5}
  .walk-era{left:14px;top:calc(env(safe-area-inset-top,0px) + 14px)}
  .walk-close{position:absolute;right:14px;top:calc(env(safe-area-inset-top,0px) + 14px);z-index:6;
    font-family:var(--zh-sans);font-size:13px;letter-spacing:.1em;color:#EDE0C4;background:rgba(25,20,14,.62);
    border:1px solid rgba(224,169,109,.45);padding:7px 13px;border-radius:3px;cursor:pointer}
  .walk-compass{position:absolute;right:18px;top:calc(env(safe-area-inset-top,0px) + 62px);width:46px;height:46px;z-index:5}
  .walk-feet{position:absolute;left:50%;bottom:18%;transform:translateX(-50%);z-index:5;pointer-events:none}
  .walk-feet .ring{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:120px;height:46px;
    border-radius:50%;border:2px solid rgba(193,95,60,.5);
    background:radial-gradient(ellipse,rgba(193,95,60,.16),rgba(193,95,60,0) 70%);
    animation:walk-breathe 2.4s ease-in-out infinite}
  .walk-feet .dot{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:18px;height:18px;
    border-radius:50%;background:var(--vermilion);border:3px solid #fff;box-shadow:0 3px 8px rgba(20,15,8,.5)}
  @keyframes walk-breathe{0%,100%{transform:translate(-50%,-50%) scale(1)}50%{transform:translate(-50%,-50%) scale(1.09)}}
  .walk-hint{position:absolute;left:50%;bottom:calc(env(safe-area-inset-bottom,0px) + 14px);transform:translateX(-50%);
    z-index:5;font-family:var(--mono);font-size:11px;letter-spacing:.14em;color:#cfc4ab;
    background:rgba(25,20,14,.5);padding:5px 12px;border-radius:3px;white-space:nowrap;max-width:92vw;
    overflow:hidden;text-overflow:ellipsis}
  /* 漫遊中的古地圖透明度滑桿：拉低即見現代街道透出（古今疊合的地面） */
  .walk-op{position:absolute;right:14px;bottom:calc(env(safe-area-inset-bottom,0px) + 52px);z-index:6;
    display:flex;align-items:center;gap:8px;background:rgba(25,20,14,.62);
    border:1px solid rgba(224,169,109,.45);border-radius:3px;padding:8px 12px}
  .walk-op .wo-ic{color:#E0A96D;font-size:13px;line-height:1}
  .walk-op input[type=range]{-webkit-appearance:none;appearance:none;width:110px;height:3px;border-radius:2px;
    background:linear-gradient(90deg,rgba(224,169,109,.25),rgba(224,169,109,.8));outline:none}
  .walk-op input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:16px;height:16px;
    border-radius:50%;background:var(--vermilion);border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4);cursor:pointer}
  .walk-op input[type=range]::-moz-range-thumb{width:14px;height:14px;border-radius:50%;
    background:var(--vermilion);border:2px solid #fff;cursor:pointer}
  .walk-op .wo-val{font-family:var(--mono);font-size:11px;letter-spacing:.08em;color:#E0A96D;min-width:34px;text-align:right}
  /* 漫遊頁內的「定位 / 記錄」控制（重用主程式的定位與路徑記錄） */
  .walk-ctrl{position:absolute;left:14px;bottom:calc(env(safe-area-inset-bottom,0px) + 52px);z-index:6;
    display:flex;gap:8px;will-change:transform;transform:translateZ(0)}
  .walk-btn{display:flex;flex-direction:column;align-items:center;gap:2px;min-width:52px;
    background:rgba(25,20,14,.62);border:1px solid rgba(224,169,109,.45);border-radius:6px;padding:7px 10px;
    color:#E0A96D;font-family:var(--zh-sans);cursor:pointer;-webkit-tap-highlight-color:transparent}
  .walk-btn .wb-ic{font-size:15px;line-height:1}
  .walk-btn .wb-t{font-size:11px;letter-spacing:.1em}
  .walk-btn.on{background:rgba(193,95,60,.9);border-color:#E0A96D;color:#fff}
  .walk-btn:disabled{opacity:.4}
  .walk-rec-btn.on{background:rgba(214,73,47,.95)}
  .walk-rec-readout{position:absolute;left:50%;top:calc(env(safe-area-inset-top,0px) + 66px);transform:translateX(-50%) translateZ(0);
    z-index:6;display:flex;align-items:center;gap:8px;background:rgba(25,20,14,.7);border:1px solid rgba(224,169,109,.4);
    border-radius:20px;padding:6px 15px;font-family:var(--mono);font-size:13px;letter-spacing:.1em;color:#EDE0C4;will-change:transform}
  .walk-rec-readout[hidden]{display:none} /* 明確 display 會蓋過 hidden 屬性，需補這條 */
  .walk-rec-readout .wr-dot{width:9px;height:9px;border-radius:50%;background:#e0492f;animation:walk-recblink 1.2s steps(2) infinite}
  @keyframes walk-recblink{0%,49%{opacity:1}50%,100%{opacity:.25}}
  /* 定位/背景定位同意卡必須浮在漫遊(9600)之上，否則按定位時看不到提示 */
  #geo-overlay.show,#bgloc-overlay.show{z-index:9700}
"""
i = html.rindex('</style>')
html = html[:i] + WALK_CSS + html[i:]

# ── 4. walk-mode DOM (overlay before the postcard toast; button in help stack) ──
WALK_HTML = """
<!-- β 街景漫遊：把古地圖鋪成腳下的透視地面（Google 街景式的「走在古地圖上」） -->
<div class="walk-overlay" id="walk-overlay" aria-hidden="true">
  <div class="walk-sky"></div>
  <div class="walk-groundwrap"><div id="walk-tilt"><canvas id="walk-map"></canvas></div></div>
  <div class="walk-fog"></div>
  <div class="walk-chip walk-era" id="walk-era">◷ —</div>
  <button type="button" class="walk-close" id="walk-close">✕ 離開</button>
  <div class="walk-compass"><svg viewBox="0 0 46 46">
    <circle cx="23" cy="23" r="21" fill="rgba(25,20,14,.62)" stroke="rgba(224,169,109,.45)"/>
    <g id="walk-needle"><polygon points="23,7 27,25 23,22 19,25" fill="#C15F3C"/><polygon points="23,39 27,25 23,28 19,25" fill="#ddd2bd"/></g>
    <text x="23" y="14" text-anchor="middle" fill="#E0A96D" font-size="8" font-family="monospace">N</text>
  </svg></div>
  <div class="walk-feet"><div class="ring"></div><div class="dot"></div></div>
  <div class="walk-rec-readout" id="walk-rec-readout" hidden><span class="wr-dot"></span><span id="walk-rec-dist">0 m</span> · <span id="walk-rec-time">0:00</span></div>
  <div class="walk-ctrl" id="walk-ctrl">
    <button type="button" class="walk-btn" id="walk-locate"><span class="wb-ic">◎</span><span class="wb-t">定位</span></button>
    <button type="button" class="walk-btn walk-rec-btn" id="walk-record" disabled><span class="wb-ic">●</span><span class="wb-t">記錄</span></button>
  </div>
  <div class="walk-op"><span class="wo-ic">◐</span><input type="range" id="walk-opacity" min="20" max="100" step="5" value="85" aria-label="古地圖透明度" /><span class="wo-val" id="walk-op-val">85%</span></div>
  <div class="walk-hint" id="walk-hint">—</div>
</div>
"""
html = html.replace('<div class="pc-toast" id="pc-toast"></div>',
                    WALK_HTML + '\n<div class="pc-toast" id="pc-toast"></div>', 1)
html = html.replace(
    '  <button type="button" class="help-fab" id="btn-help"',
    '  <button type="button" class="help-fab" id="walk-fab" aria-label="街景漫遊（β）">'
    '<span style="font-size:17px;font-style:normal">👣</span>'
    '<span class="help-fab-label">漫遊β</span></button>\n'
    '  <button type="button" class="help-fab" id="btn-help"', 1)

# ── 5. walk-mode JS (inside the main script, so it shares map / layer state) ──
WALK_JS = r"""
  // ── β 街景漫遊 walk mode ──────────────────────────────
  // 把目前啟用的歷史圖層（未啟用則預設 1904 臺灣堡圖）以透視角度鋪成
  // 「腳下的地面」：GPS 更新時地圖在腳下捲動、羅盤轉向時地圖跟著旋轉，
  // 體驗上等於「走在古地圖上」。互動全部停用（3D 變形下座標會歪），
  // 純粹是跟著身體移動的視窗。Leaflet 容器加大到 160%×230%，讓遠方
  // （地平線附近）也有圖磚可看。
  (function setupWalkMode() {
    const overlay = document.getElementById('walk-overlay');
    const fab = document.getElementById('walk-fab');
    if (!overlay || !fab) return;
    const mapEl = document.getElementById('walk-map');
    const eraEl = document.getElementById('walk-era');
    const hintEl = document.getElementById('walk-hint');
    const needle = document.getElementById('walk-needle');
    let active = false, rafId = null, pollId = null;
    let heading = 0, targetHeading = 0, pos = null, targetPos = null;
    let anchorRatio = 0.78; // 使用者錨點在地面容器內的高度比例（sizeGround 動態算）

    // ── Canvas 圖磚渲染器 ─────────────────────────────
    // 地面不再用 Leaflet：把兩層圖磚（現代底圖＋古地圖）直接畫進單一
    // canvas，3D 傾斜與旋轉只作用在這一張畫布上。架構性優點：
    //  · 單一合成層 → 不再有上百個圖磚 <img> 的 Android 重繪抖動
    //  · 覆蓋自己算 → 永遠滿版，沒有遠方空白 / 旋轉缺角
    //  · 靜止時零重繪；位移超過門檻才重畫一次（約 30 次 drawImage）
    const TILE = 256, WZ_MAX = 16, DPR = Math.min(window.devicePixelRatio || 1, 2);
    let ctx = null, walkDef = null, needsRedraw = false;
    let cw = 0, chh = 0; // canvas CSS 尺寸
    const tileCache = new Map(); // key → {img, ok, fail}
    let tileHolder = null; // 隱藏的 DOM 容器：SW 控制的頁面上，未掛 DOM 的 Image
                           // 不會啟動載入（實測），掛上去就跟 Leaflet 圖磚同路。
    function cacheGet(key, url) {
      let e = tileCache.get(key);
      if (e) return e;
      if (!tileHolder) {
        tileHolder = document.createElement('div');
        tileHolder.style.display = 'none';
        overlay.appendChild(tileHolder);
      }
      e = { img: new Image(), ok: false, fail: false };
      e.img.decoding = 'async';
      e.img.onload = () => { e.ok = true; needsRedraw = true; };
      e.img.onerror = () => { e.fail = true; }; // 中研院缺磚回 HTML → onerror，不重試
      e.img.src = url;
      tileHolder.appendChild(e.img);
      tileCache.set(key, e);
      if (tileCache.size > 360) { // 簡單 FIFO 淘汰，控記憶體
        const it = tileCache.keys();
        for (let i = 0; i < 60; i++) {
          const k = it.next().value;
          if (!k) break;
          const old = tileCache.get(k);
          if (old && old.img) old.img.remove();
          tileCache.delete(k);
        }
      }
      return e;
    }
    const lngToPx = (lng, z) => (lng + 180) / 360 * TILE * Math.pow(2, z);
    const latToPx = (lat, z) => { const r = lat * Math.PI / 180;
      return (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * TILE * Math.pow(2, z); };
    const walkZoom = () => Math.min((walkDef && walkDef.maxNativeZoom) || 15, WZ_MAX);
    function baseURL(z, x, y) {
      const s = 'abcd'[(x + y) % 4], r = DPR > 1 ? '@2x' : '';
      return 'https://' + s + '.basemaps.cartocdn.com/light_nolabels/' + z + '/' + x + '/' + y + r + '.png';
    }
    function histURL(z, x, y) {
      return walkDef.url.replace('{z}', z).replace('{x}', x).replace('{y}', y);
    }
    function drawLayer(z, originX, originY, keyPfx, urlFn, alpha) {
      const tx0 = Math.floor(originX / TILE), ty0 = Math.floor(originY / TILE);
      const tx1 = Math.floor((originX + cw) / TILE), ty1 = Math.floor((originY + chh) / TILE);
      const max = Math.pow(2, z);
      ctx.globalAlpha = alpha;
      for (let tx = tx0; tx <= tx1; tx++) for (let ty = ty0; ty <= ty1; ty++) {
        if (ty < 0 || ty >= max) continue;
        const wx = ((tx % max) + max) % max;
        const e = cacheGet(keyPfx + z + '/' + wx + '/' + ty, urlFn(z, wx, ty));
        if (e.ok) ctx.drawImage(e.img, tx * TILE - originX, ty * TILE - originY, TILE, TILE);
      }
      ctx.globalAlpha = 1;
    }
    function drawGround() {
      if (!ctx || !pos || !walkDef) return;
      const z = walkZoom();
      const originX = lngToPx(pos.lng, z) - cw / 2;
      const originY = latToPx(pos.lat, z) - chh * anchorRatio; // 錨點=你站的位置
      ctx.fillStyle = '#EDE0C4'; ctx.fillRect(0, 0, cw, chh);
      drawLayer(z, originX, originY, 'b/', baseURL, 1);
      drawLayer(z, originX, originY, 'h' + walkDef.id + '/', histURL, walkOpacity);
      needsRedraw = false;
    }

    // ── Safari 關鍵修正：平面尺寸依螢幕動態計算 ────────────
    // rotateX(60°)+perspective(640px) 下，平面上局部 y 超過 d/sin60 ≈ 739px
    // 的部分會跑到「相機後方」：Chromium 會裁掉，iOS Safari 直接把整塊
    // 渲染壞掉（畫面出現黑洞）。所以平面深度必須動態算到「剛好蓋滿畫面
    // 底部」為止，全程保持在相機平面之前。
    const TILT_DEG = 60, PERSP = 640;
    function sizeGround() {
      const wrap = mapEl.parentElement.parentElement; // .walk-groundwrap
      const H = wrap.clientHeight || 1, W = wrap.clientWidth || 1;
      const s = Math.sin(TILT_DEG * Math.PI / 180), c = Math.cos(TILT_DEG * Math.PI / 180);
      const yFor = sy => sy * PERSP / (c * PERSP + sy * s); // 螢幕深度 → 平面局部 y
      // 旋轉覆蓋：平面會繞使用者錨點轉（羅盤），寬度取「錨點到地平線角落」
      // 的距離 ×2 再加餘裕，讓多數轉角下不露出缺角；露出的極端角落由紙色
      // 背景＋霧帶吸收。上限 1600px 控制 GPU 紋理大小（Android 閃爍主因之二）。
      const overhang = 60;                                   // 地平線後方的緩衝（不可見）
      const hPx = Math.min(yFor(H) * 1.18, (PERSP / s) * 0.92) + overhang;
      const yAnchor = yFor(0.76 * H);
      const wPx = Math.min(Math.max(W * 1.7, 2 * Math.hypot(yAnchor, W * 0.55) + 80), 1600);
      cw = Math.round(wPx); chh = Math.round(hPx);
      mapEl.style.width  = cw + 'px';
      mapEl.style.height = chh + 'px';
      mapEl.style.left   = Math.round((W - wPx) / 2) + 'px';
      mapEl.style.top    = (-overhang) + 'px';
      // canvas 背景儲存以 DPR 倍率配置，高 DPI 手機上圖磚才銳利
      mapEl.width = Math.round(cw * DPR); mapEl.height = Math.round(chh * DPR);
      if (!ctx) ctx = mapEl.getContext('2d');
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
      // 錨點（你站的位置）投影在畫面約 76% 高處，和 CSS 的腳印標記對齊
      anchorRatio = (yAnchor + overhang) / hPx;
      mapEl.style.transformOrigin = '50% ' + (anchorRatio * 100).toFixed(2) + '%';
      needsRedraw = true;
    }
    window.addEventListener('resize', () => { if (active) { sizeGround(); drawGround(); } });

    // 漫遊中的古地圖透明度：獨立於主地圖記憶（拉低=現代街道透出）。
    const WALK_OP_KEY = 'taiwanOldMaps.walkOpacity';
    let walkOpacity = 0.85;
    try {
      const v = parseFloat(localStorage.getItem(WALK_OP_KEY));
      if (!Number.isNaN(v) && v >= 0.2 && v <= 1) walkOpacity = v;
    } catch {}
    const opSlider = document.getElementById('walk-opacity');
    const opVal = document.getElementById('walk-op-val');
    function applyWalkOpacity(v) {
      walkOpacity = v;
      needsRedraw = true; // 下一幀以新透明度重畫古地圖層
      if (opVal) opVal.textContent = Math.round(v * 100) + '%';
      try { localStorage.setItem(WALK_OP_KEY, String(v)); } catch {}
    }

    function currentDef() {
      return HISTORICAL_MAPS.find(d => d.id === activeId) ||
             HISTORICAL_MAPS.find(d => d.id === 'jm20k_1904') ||
             HISTORICAL_MAPS[0];
    }
    function anchorLL() {
      if (lastUserLatLng) return L.latLng(lastUserLatLng.lat, lastUserLatLng.lng);
      return map.getCenter();
    }
    function ensureMap() {
      const def = currentDef();
      if (!ctx) ctx = mapEl.getContext('2d');
      if (!walkDef || walkDef.id !== def.id) { walkDef = def; needsRedraw = true; }
      eraEl.textContent = '◷ ' + def.year + ' · ' + def.label;
    }
    let lastAppliedHeading = null, lastCenterPx = null;
    function frame() {
      if (targetPos) {
        pos = pos
          ? { lat: pos.lat + (targetPos.lat - pos.lat) * 0.12,
              lng: pos.lng + (targetPos.lng - pos.lng) * 0.12 }
          : targetPos;
        // 像素級死區：平滑後的位置實際位移 ≥1.5px 才標記重畫。
        // 收斂後完全不重畫 —— canvas 靜止時是一張死圖，先天無抖動。
        const z = walkZoom();
        const px = { x: lngToPx(pos.lng, z), y: latToPx(pos.lat, z) };
        if (!lastCenterPx || Math.abs(px.x - lastCenterPx.x) + Math.abs(px.y - lastCenterPx.y) >= 1.5) {
          lastCenterPx = px;
          needsRedraw = true;
        }
      }
      if (needsRedraw) drawGround(); // 位置變了 / 圖磚到貨 / 透明度變了 → 重畫一次
      const dh = ((targetHeading - heading + 540) % 360) - 180;
      heading = (heading + dh * 0.12 + 360) % 360;
      // 角度變化 <0.1° 就不重寫 transform——連續改寫大型 3D 圖層的
      // transform 是 Android WebView 閃爍的主因之一。
      if (lastAppliedHeading === null || Math.abs(((heading - lastAppliedHeading + 540) % 360) - 180) > 0.1) {
        lastAppliedHeading = heading;
        mapEl.style.transform = 'rotateZ(' + (-heading).toFixed(2) + 'deg)';
        if (needle) needle.setAttribute('transform', 'rotate(' + (-heading).toFixed(1) + ' 23 23)');
      }
      rafId = requestAnimationFrame(frame);
    }
    // 方位來源紀律（Android 災情根因）：deviceorientation 在 Android 上是
    // 「相對」方位（任意參考系），和 deviceorientationabsolute（真羅盤）的
    // 角度完全不同。之前兩個事件都在覆寫 targetHeading，平面就在兩個角度
    // 之間劇烈擺盪 → 畫面瘋狂旋轉閃爍。規則：一旦收過任何「絕對」讀值，
    // 永遠忽略相對讀值；再加 1.5° 死區濾掉羅盤雜訊。
    let haveAbsolute = false;
    function onOrient(e) {
      let h = null;
      if (typeof e.webkitCompassHeading === 'number') {            // iOS 真羅盤
        h = e.webkitCompassHeading; haveAbsolute = true;
      } else if (e.type === 'deviceorientationabsolute' || e.absolute === true) {
        if (typeof e.alpha === 'number') { h = 360 - e.alpha; haveAbsolute = true; }
      } else if (!haveAbsolute && typeof e.alpha === 'number') {
        h = 360 - e.alpha;                                         // 沒絕對來源時的退路
      }
      if (h == null || Number.isNaN(h)) return;
      const dh = ((h - targetHeading + 540) % 360) - 180;
      if (Math.abs(dh) < 1.5) return;                              // 雜訊死區
      targetHeading = h;
    }
    async function enableCompass() {
      try {
        if (typeof DeviceOrientationEvent !== 'undefined' &&
            typeof DeviceOrientationEvent.requestPermission === 'function') {
          const r = await DeviceOrientationEvent.requestPermission();
          if (r !== 'granted') return;
        }
        window.addEventListener('deviceorientationabsolute', onOrient, true);
        window.addEventListener('deviceorientation', onOrient, true);
      } catch {}
    }
    function open() {
      active = true;
      overlay.classList.add('show');
      overlay.setAttribute('aria-hidden', 'false');
      ensureMap();
      requestAnimationFrame(() => {
        sizeGround();
        const ll = anchorLL();
        targetPos = { lat: ll.lat, lng: ll.lng };
        pos = { lat: ll.lat, lng: ll.lng }; // 開場直接落點，不用等平滑收斂
        lastCenterPx = null;
        drawGround();
        if (!rafId) frame();
      });
      enableCompass();
      syncControls();
      pollId = setInterval(() => {
        const ll = anchorLL();
        // GPS 抖動死區：手機 GPS 靜止時仍會每秒跳動數公尺。只有位移
        // ≥ 4 公尺才更新目標點，否則地圖會被雜訊推得一直微幅漂移。
        if (!targetPos || haversine(targetPos, { lat: ll.lat, lng: ll.lng }) >= 4) {
          targetPos = { lat: ll.lat, lng: ll.lng };
        }
        ensureMap(); // 圖層若在主地圖換了年代，跟著換
        syncControls(); // 同步定位/記錄按鈕與讀數
      }, 900);
    }

    // ── 定位 / 記錄：重用主程式的 requestLocate / startRecording ──────
    // 記錄是全域狀態：在漫遊裡開始，離開漫遊仍持續（路徑畫在主地圖上）。
    const locBtn = document.getElementById('walk-locate');
    const recBtn = document.getElementById('walk-record');
    const recReadout = document.getElementById('walk-rec-readout');
    function syncControls() {
      if (locBtn) locBtn.classList.toggle('on', isLocating);
      if (recBtn) {
        recBtn.disabled = !isLocating;
        recBtn.classList.toggle('on', isRecording);
        const t = recBtn.querySelector('.wb-t'); if (t) t.textContent = isRecording ? '停止' : '記錄';
      }
      if (recReadout) {
        recReadout.hidden = !isRecording;
        if (isRecording) {
          const d = document.getElementById('rec-dist'), tm = document.getElementById('rec-time');
          if (d) document.getElementById('walk-rec-dist').textContent = d.textContent;
          if (tm) document.getElementById('walk-rec-time').textContent = tm.textContent;
        }
      }
      hintEl.textContent = isRecording ? '記錄中 · 走動時路徑會沿路記下'
        : lastUserLatLng ? '腳下就是古地圖 · 走動時跟著你捲動'
        : '按「定位」開始，漫遊就會跟著你走。';
    }
    if (locBtn) locBtn.addEventListener('click', async () => {
      try { await requestLocate(); } catch {}
      syncControls(); setTimeout(syncControls, 400);
    });
    if (recBtn) recBtn.addEventListener('click', () => {
      if (isRecording) stopRecording(); else startRecording();
      syncControls();
    });
    function close() {
      active = false;
      overlay.classList.remove('show');
      overlay.setAttribute('aria-hidden', 'true');
      if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
      if (pollId) { clearInterval(pollId); pollId = null; }
      window.removeEventListener('deviceorientationabsolute', onOrient, true);
      window.removeEventListener('deviceorientation', onOrient, true);
    }
    fab.addEventListener('click', open);
    document.getElementById('walk-close').addEventListener('click', close);
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && active) close(); });
    if (opSlider) {
      opSlider.value = String(Math.round(walkOpacity * 100));
      if (opVal) opVal.textContent = Math.round(walkOpacity * 100) + '%';
      opSlider.addEventListener('input', () => applyWalkOpacity(parseInt(opSlider.value, 10) / 100));
    }
  })();
"""
i = html.rindex('</script>')
html = html[:i] + WALK_JS + html[i:]

# ── 6. write output ──
if NATIVE_OUT:
    pathlib.Path(NATIVE_OUT).write_text(html, encoding='utf-8')
    print('native variant (walk mode, root paths) →', NATIVE_OUT)
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
            "const CACHE_VERSION = 'beta9-2026-07-09'; // walk mode: canvas tile renderer (single-layer, rock stable)",
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
