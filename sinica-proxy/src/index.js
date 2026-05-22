/**
 * sinica-proxy — Cloudflare Worker
 *
 * 透明代理中研院歷史圖磚，並以 R2 建立持久快取。
 *
 * 策略：
 *  1. R2 命中 → 直接回傳（即使中研院掛掉也沒事）
 *  2. R2 未命中 → 向中研院取圖磚，成功則寫入 R2 再回傳
 *  3. 中研院掛掉 → 回傳 1×1 透明 PNG，不讓 app 報錯
 */

const SINICA_BASE = 'https://gis.sinica.edu.tw';
const TIMEOUT_MS  = 7000;
const MIN_TILE_BYTES = 1200; // 小於此大小的是 Sinica 的錯誤 HTML，不快取

// 1×1 透明 PNG（fallback 用）
const TRANSPARENT_PNG = Uint8Array.from(
  atob('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='),
  c => c.charCodeAt(0)
);

export default {
  async fetch(request, env) {
    // 只處理 GET
    if (request.method !== 'GET') {
      return new Response('Method Not Allowed', { status: 405 });
    }

    const url   = new URL(request.url);
    const r2Key = url.pathname + url.search;

    // ── 1. R2 快取優先 ────────────────────────────────
    try {
      const cached = await env.TILES.get(r2Key);
      if (cached) {
        return new Response(cached.body, {
          headers: {
            'Content-Type':  'image/png',
            'Cache-Control': 'public, max-age=604800',
            'X-Source':      'r2-cache',
            'Access-Control-Allow-Origin': '*',
          },
        });
      }
    } catch (_) { /* R2 偶爾出錯，繼續嘗試 origin */ }

    // ── 2. 向中研院取圖磚 ─────────────────────────────
    const sinicaUrl = SINICA_BASE + url.pathname + url.search;
    try {
      const res = await Promise.race([
        fetch(sinicaUrl, { headers: { 'Referer': 'https://gis.sinica.edu.tw/' } }),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('timeout')), TIMEOUT_MS)
        ),
      ]);

      if (res.ok) {
        const buf = await res.arrayBuffer();

        // 非空圖磚才存進 R2
        if (buf.byteLength > MIN_TILE_BYTES) {
          env.TILES.put(r2Key, buf.slice(0), {
            httpMetadata: { contentType: 'image/png' },
          }).catch(() => {}); // 非同步寫入，不阻擋回傳
        }

        return new Response(buf, {
          headers: {
            'Content-Type':  'image/png',
            'Cache-Control': 'public, max-age=604800',
            'X-Source':      'sinica-live',
            'Access-Control-Allow-Origin': '*',
          },
        });
      }
    } catch (_) { /* 中研院掛掉，往下走 */ }

    // ── 3. Fallback：透明圖磚 ────────────────────────
    return new Response(TRANSPARENT_PNG, {
      headers: {
        'Content-Type':  'image/png',
        'Cache-Control': 'public, max-age=60',
        'X-Source':      'fallback',
        'Access-Control-Allow-Origin': '*',
      },
    });
  },
};
