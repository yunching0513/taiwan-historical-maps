/* Taiwan Historical Maps — service worker
 *
 * Strategy
 * --------
 * - Pre-cache the app shell (HTML, manifest, icons) so the app installs and
 *   launches offline. The shell is the deliverable; everything else (Leaflet
 *   CDN, basemap tiles, historical tiles) is fetched at runtime.
 * - Runtime fetches use a small split policy:
 *     · HTML / manifest        → network-first, fall back to cache, so updates
 *                                ship as soon as the user is online again.
 *     · Leaflet CDN (unpkg)    → cache-first, stable versions; saves bandwidth.
 *     · Tile servers           → cache-first with size cap + LRU eviction. Tile
 *                                content is immutable so caching is safe.
 *     · Everything else        → cache-first, network fallback (icons, etc.).
 * - Bumping CACHE_VERSION invalidates the old cache on the next page load.
 */

const CACHE_VERSION = 'v17-2026-06-13'; // Resilient geolocation (transient errors no longer abort)
const SHELL_CACHE = `tw-historical-shell-${CACHE_VERSION}`;
const RUNTIME_CACHE = `tw-historical-runtime-${CACHE_VERSION}`;
const TILE_CACHE = `tw-historical-tiles-${CACHE_VERSION}`;
// Pinned cache holds user-downloaded offline packs. Version-independent so
// upgrades don't blow them away. LRU eviction never touches this bucket.
const PINNED_CACHE = 'tw-historical-pinned';

// Roughly 100–150 MB at typical tile sizes (30–100 KB each). LRU evicts
// oldest tiles when the cap is exceeded.
const TILE_CACHE_MAX = 1200;
const TILE_CACHE_TRIM_TARGET = 900; // trim down to this after eviction

const SHELL_URLS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon.svg',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-180.png',
];

const TILE_HOST_PATTERNS = [
  /^https:\/\/sinica-proxy\.jtl0513\.workers\.dev\//,  // Cloudflare proxy (備援)
  /^https:\/\/gis\.sinica\.edu\.tw\//,                 // 中研院直連 (fallback)
  /^https:\/\/wmts\.nlsc\.gov\.tw\//,
  /^https:\/\/[a-d]\.basemaps\.cartocdn\.com\//,
  /^https:\/\/[a-c]\.tile\.openstreetmap\.org\//,
  /^https:\/\/server\.arcgisonline\.com\//,
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then(cache => cache.addAll(SHELL_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(k => k !== SHELL_CACHE && k !== RUNTIME_CACHE && k !== TILE_CACHE && k !== PINNED_CACHE)
          .map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Tile servers: cache-first with LRU eviction
  if (TILE_HOST_PATTERNS.some(p => p.test(url.href))) {
    event.respondWith(tileCacheFirst(req));
    return;
  }

  // HTML / manifest: network-first
  const accept = req.headers.get('accept') || '';
  if (req.mode === 'navigate' || accept.includes('text/html') || url.pathname.endsWith('.webmanifest')) {
    event.respondWith(networkFirst(req));
    return;
  }

  // unpkg.com (Leaflet CDN): cache-first
  if (url.hostname === 'unpkg.com' || url.hostname.endsWith('googleapis.com') || url.hostname.endsWith('gstatic.com') || url.hostname === 'cdn.jsdelivr.net') {
    event.respondWith(cacheFirst(req));
    return;
  }

  // Same-origin static assets: cache-first
  if (url.origin === self.location.origin) {
    event.respondWith(cacheFirst(req));
    return;
  }
});

async function networkFirst(req) {
  try {
    const res = await fetch(req);
    if (res && res.status === 200) {
      const clone = res.clone();
      caches.open(SHELL_CACHE).then(c => c.put(req, clone)).catch(() => {});
    }
    return res;
  } catch (err) {
    const cached = await caches.match(req);
    if (cached) return cached;
    if (req.mode === 'navigate') {
      const shell = await caches.match('./index.html');
      if (shell) return shell;
    }
    throw err;
  }
}

async function cacheFirst(req) {
  const cached = await caches.match(req);
  if (cached) return cached;
  try {
    const res = await fetch(req);
    if (res && res.status === 200 && res.type !== 'opaque') {
      const clone = res.clone();
      caches.open(RUNTIME_CACHE).then(c => c.put(req, clone)).catch(() => {});
    }
    return res;
  } catch (err) {
    throw err;
  }
}

// Map tile cache with LRU-ish eviction. We don't store explicit timestamps —
// Cache API returns keys in insertion order, so deleting the first N when
// over cap acts as a simple FIFO. Re-fetching a tile re-adds it at the end,
// approximating LRU well enough for an icon/tile workload.
async function tileCacheFirst(req) {
  // Pinned (offline pack) tiles win — never re-fetched, never evicted.
  const pinned = await caches.open(PINNED_CACHE);
  const pinnedHit = await pinned.match(req);
  if (pinnedHit) return pinnedHit;

  const cache = await caches.open(TILE_CACHE);
  const cached = await cache.match(req);
  if (cached) {
    // Refresh in insertion order so frequently-used tiles drift to the end
    // of the FIFO and survive eviction longer. Don't await the network.
    refreshTile(req, cache).catch(() => {});
    return cached;
  }
  try {
    const res = await fetch(req);
    if (res && res.status === 200 && res.type !== 'opaque') {
      const clone = res.clone();
      // Only cache real tile bytes (Sinica returns 197-byte HTML for missing
      // tiles, ~936 bytes for transparent placeholders).
      try {
        const peek = clone.clone();
        const blob = await peek.blob();
        if (blob.size > 1200) {
          cache.put(req, clone).then(() => maybeEvict(cache)).catch(() => {});
        }
      } catch {}
    }
    return res;
  } catch (err) {
    throw err;
  }
}

async function refreshTile(req, cache) {
  // Touch the cache to move this tile to the end (FIFO refresh).
  // Skip if browser doesn't actually return data — just keep existing entry.
  try {
    const fresh = await fetch(req, { cache: 'force-cache' });
    if (fresh && fresh.status === 200) {
      await cache.delete(req);
      await cache.put(req, fresh);
    }
  } catch {}
}

let evicting = false;
async function maybeEvict(cache) {
  if (evicting) return;
  evicting = true;
  try {
    const keys = await cache.keys();
    if (keys.length > TILE_CACHE_MAX) {
      const toDelete = keys.length - TILE_CACHE_TRIM_TARGET;
      for (let i = 0; i < toDelete; i++) {
        await cache.delete(keys[i]);
      }
    }
  } finally {
    evicting = false;
  }
}
