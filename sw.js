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
 *     · Tile servers           → bypass — the SW is too aggressive a cache for
 *                                hundreds of thousands of map tiles, and the
 *                                tile servers handle their own HTTP caching.
 *     · Everything else        → cache-first, network fallback (icons, etc.).
 * - Bumping CACHE_VERSION invalidates the old cache on the next page load.
 */

const CACHE_VERSION = 'v1-2026-05-17';
const SHELL_CACHE = `tw-historical-shell-${CACHE_VERSION}`;
const RUNTIME_CACHE = `tw-historical-runtime-${CACHE_VERSION}`;

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
  /^https:\/\/gis\.sinica\.edu\.tw\//,
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
          .filter(k => k !== SHELL_CACHE && k !== RUNTIME_CACHE)
          .map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Tile servers: bypass SW entirely
  if (TILE_HOST_PATTERNS.some(p => p.test(url.href))) return;

  // HTML / manifest: network-first
  const accept = req.headers.get('accept') || '';
  if (req.mode === 'navigate' || accept.includes('text/html') || url.pathname.endsWith('.webmanifest')) {
    event.respondWith(networkFirst(req));
    return;
  }

  // unpkg.com (Leaflet CDN): cache-first
  if (url.hostname === 'unpkg.com' || url.hostname.endsWith('googleapis.com') || url.hostname.endsWith('gstatic.com')) {
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
    // Last resort: serve the shell index for navigation requests
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
