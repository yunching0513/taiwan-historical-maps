#!/usr/bin/env python3
"""把 App 裡每一張歷史圖層，在同一個地點拼成同框的圖，方便逐年讀圖比較。

用法（在 repo 根目錄）：
    python3 tools/map-mosaic.py 25.0423 121.5120            # 臺北城，第 15 級
    python3 tools/map-mosaic.py 22.9970 120.2020 --zoom 16 --out /tmp/tainan

每張圖輸出為 <年份>_<圖層id>.png（3×3 圖磚，768×768），左上角標年份與成功載入的圖磚數。
圖層清單直接讀 index.html 的 HISTORICAL_MAPS，所以新增圖層後不用改這支程式。
需要 Pillow：python3 -m pip install pillow
"""
import argparse, concurrent.futures as cf, io, math, pathlib, re, subprocess, sys

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load_layers():
    s = (ROOT / 'index.html').read_text(encoding='utf-8')
    a = s.index('const HISTORICAL_MAPS = ['); b = s.index('];', a)
    pat = re.compile(r"\{ id: '([^']+)',\s*group: '\w+',\s*year: '(\d+)',\s*label: '([^']+)'.*?url: '([^']+)'", re.S)
    return [dict(id=m[1], year=m[2], label=m[3], url=m[4]) for m in pat.finditer(s[a:b])]


def tile_xy(lat, lng, z):
    n = 2 ** z
    return int((lng + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)


def fetch(url):
    r = subprocess.run(['curl', '-s', '--max-time', '30', url], capture_output=True)
    try:
        return Image.open(io.BytesIO(r.stdout)).convert('RGB')
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('lat', type=float); ap.add_argument('lng', type=float)
    ap.add_argument('--zoom', type=int, default=15)
    ap.add_argument('--out', default='map-mosaics')
    args = ap.parse_args()
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    cx, cy = tile_xy(args.lat, args.lng, args.zoom)
    for d in load_layers():
        with cf.ThreadPoolExecutor(9) as ex:
            jobs = {(dx, dy): ex.submit(fetch, d['url'].replace('{z}', str(args.zoom))
                                        .replace('{x}', str(cx + dx)).replace('{y}', str(cy + dy)))
                    for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        canvas = Image.new('RGB', (768, 768), (230, 230, 230)); ok = 0
        for (dx, dy), job in jobs.items():
            im = job.result()
            if im:
                canvas.paste(im.resize((256, 256)), ((dx + 1) * 256, (dy + 1) * 256)); ok += 1
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, 0, 768, 22), fill=(0, 0, 0))
        draw.text((6, 5), f"{d['year']} {d['id']}  tiles {ok}/9", fill=(255, 255, 0))
        path = out / f"{d['year']}_{d['id']}.png"
        canvas.save(path)
        print(f"{d['year']} {d['id']:16s} {ok}/9 → {path}")


if __name__ == '__main__':
    sys.exit(main())
