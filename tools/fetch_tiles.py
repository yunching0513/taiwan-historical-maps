#!/usr/bin/env python3
"""Fetch a rectangular AOI from Academia Sinica's historical-map tile server
and stitch the tiles into one georeferenced image readable by QGIS.

Default AOI: Tainan old city (Wǔtiáo Gǎng 五條港) on the 1904 Taiwan Daichō 20K, z=17.

Outputs three sidecar files next to each other (ESRI world-file convention):
  out/<layer>_<name>_z<z>.jpg   stitched mosaic
  out/<layer>_<name>_z<z>.jgw   pixel→EPSG:3857 affine transform
  out/<layer>_<name>_z<z>.prj   EPSG:3857 WKT

Install once:
  pip3 install --user pillow

Usage:
  python3 tools/fetch_tiles.py                          # defaults (Tainan, 1904, z=17)
  python3 tools/fetch_tiles.py --layer JM25K_1921-jpg   # other layer
  python3 tools/fetch_tiles.py --bbox 120.65 24.13 120.72 24.17 --name taichung_core
"""

import argparse
import math
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required. Install with: pip3 install --user pillow")

TILE_BASE = "https://gis.sinica.edu.tw/tileserver/file-exists.php?img={layer}-{z}-{x}-{y}"
TILE_SIZE = 256
ORIGIN_SHIFT = 2 * math.pi * 6378137 / 2.0  # 20037508.342789244 — half of equator in EPSG:3857 metres
USER_AGENT = "taiwan-old-maps-fetch/0.1 (research)"

WKT_3857 = (
    'PROJCS["WGS 84 / Pseudo-Mercator",'
    'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
    'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],'
    'PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],'
    'PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],'
    'UNIT["metre",1],AXIS["X",EAST],AXIS["Y",NORTH],AUTHORITY["EPSG","3857"]]'
)


def lonlat_to_tile(lon, lat, z):
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def tile_to_3857_bounds(x, y, z):
    n = 2 ** z
    res = 2 * ORIGIN_SHIFT / n
    xmin = x * res - ORIGIN_SHIFT
    xmax = (x + 1) * res - ORIGIN_SHIFT
    ymax = ORIGIN_SHIFT - y * res
    ymin = ORIGIN_SHIFT - (y + 1) * res
    return xmin, ymin, xmax, ymax


def fetch_tile(layer, z, x, y, cache_dir, throttle, retries=3):
    suffix = "png" if "-png" in layer else "jpg"
    cache_path = cache_dir / f"{layer}_{z}_{x}_{y}.{suffix}"
    if cache_path.exists() and cache_path.stat().st_size > 100:
        return cache_path, "cache"

    url = TILE_BASE.format(layer=layer, z=z, x=x, y=y)
    last_err = ""
    for attempt in range(retries):
        time.sleep(throttle)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            if len(data) < 100:
                last_err = f"tiny body ({len(data)} bytes)"
            elif data[:3] == b"\xff\xd8\xff" or data[:8] == b"\x89PNG\r\n\x1a\n":
                cache_path.write_bytes(data)
                return cache_path, "fetched"
            else:
                last_err = f"non-image response (first 8 bytes: {data[:8]!r})"
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}"
            if e.code == 404:
                break  # don't retry genuine 404
        except Exception as e:
            last_err = repr(e)
        time.sleep(0.5 * (attempt + 1))
    return None, f"missing ({last_err})"


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--layer", default="JM20K_1904-jpg",
                    help="Sinica layer ID, e.g. JM20K_1904-jpg, JM25K_1921-jpg, AMCityPlan_1945-png")
    ap.add_argument("--bbox", nargs=4, type=float, metavar=("WEST", "SOUTH", "EAST", "NORTH"),
                    default=[120.155, 22.985, 120.215, 23.015],
                    help="lon/lat bounding box; default ≈ Tainan old city + Anping lagoon")
    ap.add_argument("--zoom", type=int, default=17)
    ap.add_argument("--name", default="tainan_oldcity", help="Output filename stem")
    ap.add_argument("--out", default="out", help="Output directory")
    ap.add_argument("--cache", default=".tile_cache", help="Tile cache directory")
    ap.add_argument("--workers", type=int, default=4, help="Parallel downloads (keep small; be polite)")
    ap.add_argument("--throttle", type=float, default=0.05,
                    help="Seconds to sleep before each request per worker")
    args = ap.parse_args()

    west, south, east, north = args.bbox
    z = args.zoom

    x_nw, y_nw = lonlat_to_tile(west, north, z)
    x_se, y_se = lonlat_to_tile(east, south, z)
    x0, x1 = sorted([x_nw, x_se])
    y0, y1 = sorted([y_nw, y_se])
    nx, ny = x1 - x0 + 1, y1 - y0 + 1
    total = nx * ny

    print(f"Layer: {args.layer}")
    print(f"AOI:   lon {west}–{east}, lat {south}–{north}, zoom {z}")
    print(f"Tiles: x={x0}..{x1}, y={y0}..{y1}  ({nx}×{ny} = {total})")

    cache_dir = Path(args.cache)
    cache_dir.mkdir(parents=True, exist_ok=True)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = {}
    stats = {"cache": 0, "fetched": 0, "missing": 0}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {
            ex.submit(fetch_tile, args.layer, z, x, y, cache_dir, args.throttle): (x, y)
            for x in range(x0, x1 + 1)
            for y in range(y0, y1 + 1)
        }
        done = 0
        for fut in as_completed(futures):
            xy = futures[fut]
            path, status = fut.result()
            done += 1
            if path is None:
                stats["missing"] += 1
            else:
                paths[xy] = path
                stats["cache" if status == "cache" else "fetched"] += 1
            if done % 50 == 0 or done == total:
                print(f"  {done}/{total}  fetched={stats['fetched']}  cache={stats['cache']}  missing={stats['missing']}")

    if not paths:
        sys.exit("ERROR: no tiles fetched — check layer ID, network, and bbox")

    mosaic = Image.new("RGB", (nx * TILE_SIZE, ny * TILE_SIZE), (255, 255, 255))
    for (x, y), p in paths.items():
        try:
            img = Image.open(p).convert("RGB")
            mosaic.paste(img, ((x - x0) * TILE_SIZE, (y - y0) * TILE_SIZE))
        except Exception as e:
            print(f"WARN: failed to open {p}: {e}", file=sys.stderr)

    stem = f"{args.layer.replace('-', '_')}_{args.name}_z{z}"
    jpg_path = out_dir / f"{stem}.jpg"
    mosaic.save(jpg_path, quality=92, optimize=True)
    print(f"Wrote {jpg_path}  ({mosaic.size[0]}×{mosaic.size[1]} px)")

    # World file: the affine that maps a (col, row) pixel CENTER to (x, y) in EPSG:3857.
    # Line order: A (x-pixel size), D (rotation), B (rotation), E (y-pixel size, negative),
    #             C (x of upper-left pixel CENTER), F (y of upper-left pixel CENTER).
    xmin, _, xmax, ymax = tile_to_3857_bounds(x0, y0, z)
    res = (xmax - xmin) / TILE_SIZE
    jgw_path = out_dir / f"{stem}.jgw"
    jgw_path.write_text(f"{res}\n0.0\n0.0\n{-res}\n{xmin + res / 2}\n{ymax - res / 2}\n")
    print(f"Wrote {jgw_path}")

    prj_path = out_dir / f"{stem}.prj"
    prj_path.write_text(WKT_3857 + "\n")
    print(f"Wrote {prj_path}")

    print(f"\nOpen in QGIS: drag {jpg_path} into a project — CRS will resolve via the .prj sidecar.")


if __name__ == "__main__":
    main()
