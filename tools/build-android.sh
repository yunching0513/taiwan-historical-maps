#!/usr/bin/env bash
# 打包 Android 正式版 AAB（Capacitor 殼 + 內嵌含漫遊模式的網頁）。
#
# 用法（在 repo 根目錄）：
#   export ANDROID_HOME=~/Library/Android/sdk          # Android Studio 的 SDK 路徑
#   export KEYSTORE=~/keys/android-upload-v2.keystore  # 上傳金鑰（指紋 55:6B:6B:42…）
#   export KS_PASS='…'                                 # keystore-pass.txt 裡的密碼
#   VERSION_CODE=29 tools/build-android.sh
#
# 第一次執行會在 ~/cap-android 建立 Capacitor 專案；之後只更新網頁內容與版號。
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${WORK:-$HOME/cap-android}"
: "${ANDROID_HOME:?請先 export ANDROID_HOME（Android Studio 的 SDK 路徑）}"
: "${KEYSTORE:?請先 export KEYSTORE（上傳金鑰檔路徑）}"
: "${KS_PASS:?請先 export KS_PASS（金鑰密碼）}"
: "${VERSION_CODE:?請指定 VERSION_CODE（要比 Play 上最新的大）}"
VERSION_NAME="${VERSION_NAME:-1.2.0}"
KEY_ALIAS="${KEY_ALIAS:-upload}"

if [ ! -d "$WORK/android" ]; then
  echo "▸ 建立 Capacitor 專案於 $WORK"
  mkdir -p "$WORK/www" && cd "$WORK"
  [ -f package.json ] || npm init -y >/dev/null
  npm install @capacitor/core @capacitor/cli @capacitor/android @capacitor/geolocation
  cat > capacitor.config.json <<'EOF'
{
  "appId": "io.github.yunching0513.oldmapstroll",
  "appName": "舊地圖散策",
  "webDir": "www",
  "android": { "allowMixedContent": false }
}
EOF
  touch www/index.html
  npx cap add android

  python3 - "$WORK/android" <<'PY'
import sys, pathlib
root = pathlib.Path(sys.argv[1])
m = root / 'app/src/main/AndroidManifest.xml'
s = m.read_text()
if 'ACCESS_FINE_LOCATION' not in s:
    s = s.replace('<uses-permission android:name="android.permission.INTERNET" />',
        '<uses-permission android:name="android.permission.INTERNET" />\n'
        '    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n'
        '    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />')
    m.write_text(s)
g = root / 'app/build.gradle'
s = g.read_text()
if 'signingConfigs' not in s:
    s = s.replace('buildTypes {\n        release {', '''signingConfigs {
        release {
            storeFile file(System.getenv("OMS_KEYSTORE"))
            storePassword System.getenv("OMS_KS_PASS")
            keyAlias System.getenv("OMS_KEY_ALIAS")
            keyPassword System.getenv("OMS_KS_PASS")
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release''')
    g.write_text(s)
PY

  if python3 -c 'import PIL' 2>/dev/null; then
    python3 - "$REPO" "$WORK/android/app/src/main/res" <<'PY'
import sys, glob, os
from PIL import Image, ImageDraw
repo, res = sys.argv[1], sys.argv[2]
master = Image.open(f'{repo}/ios-app/resources/appicon-1024.png').convert('RGB')
safe = Image.open(f'{repo}/icons/icon-512-maskable.png').convert('RGB')
def circle(im):
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).ellipse((0, 0) + im.size, fill=255)
    out = Image.new('RGBA', im.size); out.paste(im, (0, 0), m); return out
for d in glob.glob(res + '/mipmap-*'):
    if 'anydpi' in d: continue
    for name in ('ic_launcher.png', 'ic_launcher_round.png', 'ic_launcher_foreground.png'):
        p = os.path.join(d, name)
        if not os.path.exists(p): continue
        n = Image.open(p).size[0]
        if name == 'ic_launcher.png':
            master.resize((n, n), Image.LANCZOS).save(p)
        elif name == 'ic_launcher_round.png':
            circle(safe.resize((n, n), Image.LANCZOS)).save(p)
        else:
            fg = Image.new('RGBA', (n, n), (0, 0, 0, 0))
            t = safe.resize((int(n * 0.66),) * 2, Image.LANCZOS)
            fg.paste(t, ((n - t.size[0]) // 2,) * 2)
            fg.save(p)
open(res + '/values/ic_launcher_background.xml', 'w').write(
    '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
    '    <color name="ic_launcher_background">#B0715A</color>\n</resources>\n')
PY
  else
    echo "⚠ 沒有 Pillow，App 圖示維持 Capacitor 預設。先跑：python3 -m pip install pillow，再刪掉 $WORK 重來"
  fi
fi

echo "▸ 同步網頁內容（含漫遊模式）"
cd "$WORK"
rm -rf www && mkdir -p www
cp "$REPO/manifest.webmanifest" "$REPO/sw.js" www/
cp -R "$REPO/icons" www/icons
cp -R "$REPO/data" www/data
python3 "$REPO/tools/make-beta.py" --native www/index.html
npx cap sync android

echo "▸ 版號 $VERSION_CODE / $VERSION_NAME"
sed -i.bak -E "s/versionCode [0-9]+/versionCode $VERSION_CODE/; s/versionName \"[^\"]*\"/versionName \"$VERSION_NAME\"/" android/app/build.gradle
rm -f android/app/build.gradle.bak

echo "▸ 建置 AAB"
cd android
echo "sdk.dir=$ANDROID_HOME" > local.properties
OMS_KEYSTORE="$KEYSTORE" OMS_KS_PASS="$KS_PASS" OMS_KEY_ALIAS="$KEY_ALIAS" ./gradlew bundleRelease

# 檔名維持 ASCII：keytool 等 Java 工具在非 UTF-8 locale 下讀不了中文路徑
OUT="$WORK/oldmapstroll-v$VERSION_CODE.aab"
cp app/build/outputs/bundle/release/app-release.aab "$OUT"
echo
echo "✓ 完成：$OUT"
echo "  簽章指紋（Play 要的是 55:6B:6B:42:D1:76:C8:FF:D7:29:C5:4E:42:E7:3F:7A:8C:5C:E3:CC）："
keytool -printcert -jarfile "$OUT" 2>/dev/null | grep -E 'SHA1:' || echo "  （讀不到指紋，請手動檢查）"
