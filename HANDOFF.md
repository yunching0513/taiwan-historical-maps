# 散策 App：交接文件

> 更新：2026-11-12 ｜ 分支：`main` ｜ 正式站 SW `v82-2026-10-16` ｜ β 站 SW `beta10-2026-10-16`
>
> 給接手的 Claude（或人）：這份文件是從一段很長的雲端 session 整理出來的。先讀完「不能踩的雷」再動手。

---

## 這是什麼

「台灣舊地圖散策」：把中研院 19 套歷史地圖（1897–2003）疊在今日街道上的 PWA，搭配 232 張日治時期明信片（走到 50 公尺內自動收進圖鑑）與 1,018 個歷史事件地點。三個平台：

| 平台 | 位置 | 狀態 |
|---|---|---|
| 網頁正式站 | `https://yunching0513.github.io/taiwan-historical-maps/` | GitHub Pages，推 `main` 即上線 |
| 網頁 β 站 | `…/taiwan-historical-maps/beta/` | 多了「街景漫遊」模式 |
| iOS | `ios-app/`（Capacitor），bundle `io.github.yunching0513.oldmapstroll` | 1.3 已送審（含定位修正，**不含** CARTO 金鑰） |
| Android | Capacitor 殼，同 appId，用 `tools/build-android.sh` 打包 | Play 上是 v25，**v29 待上傳** |

## 檔案地圖

- `index.html`：整個 App（約 1 萬行，單檔）。改這裡就是改正式站。
- `sw.js`：Service Worker。**任何改動後都要升 `CACHE_VERSION`**，否則使用者會一直拿到舊快取。
- `data/postcards.js`：明信片資料（232 筆，含座標、出處、作者、授權）。
- `data/histsites.js`：歷史事件（1,018 筆，6 個時代）。資料來源是邱璽民整理的 Google My Maps「台灣歷史地圖」，作者明言歡迎分享，App 內三處標註出處。點開時才載入（1.3MB）。
- `tools/make-beta.py`：**街景漫遊模式的唯一原始碼**。它讀 `index.html`，注入漫遊模式的 CSS/HTML/JS，產生 `beta/`。`--native OUT` 產生給原生 App 內嵌的版本。
- `tools/build-android.sh`：Android AAB 一鍵打包（見下方）。
- `ios-app/sync-www.sh`：把網頁複製進 iOS 專案。
- `sinica-proxy/`：Cloudflare Worker，代理中研院圖磚（`sinica-proxy.jtl0513.workers.dev`）。

## 不能踩的雷

1. **改完 `index.html` 一定要重跑 `python3 tools/make-beta.py`**，否則 β 站和原生 App 會停在舊版。
2. **升版要兩邊都升**：正式站在 `sw.js` 的 `CACHE_VERSION`；β 站的版本字串寫死在 `tools/make-beta.py` 裡（搜 `beta10-`）。十月就踩過：只升了正式站，β 站使用者一直看到浮水印。
3. **不要用 `sed` 改 `make-beta.py` 裡含中文的字串**，曾兩次把字串改壞（未結束的字串常值）。用 Python 的 `str.replace` 或編輯器。
4. **CARTO 底圖要帶 `?key=`**。CARTO 從 2026 年 10 月起免費底圖強制金鑰，沒帶金鑰不會報錯，而是回 HTTP 200 的「API KEY REQUIRED」浮水印圖。金鑰出現在 `index.html` 三處（底圖、淺色標籤、深色標籤）和 `make-beta.py` 一處（漫遊模式底圖）。這是瀏覽器端的公開金鑰，防盜用靠 CARTO 後台的網域限制，不是藏起來。
5. **Android 簽章金鑰不在 repo 裡，也絕對不要放進 repo。** 見下方。
6. 原生 App 裡定位要走 `Capacitor.Plugins.Geolocation`，不能用 `navigator.geolocation`：WKWebView 在 `capacitor://` 來源下即使有權限也會拿不到位置。`index.html` 的 `startLocate()` 已處理，另有 25 秒看門狗避免無限轉圈。

## Android 打包

### 簽章金鑰（最重要）

- 原本的上傳金鑰（`B8:01:DC…`）在 2026 年 8 月容器清空時遺失，已向 Play Console 申請重設。
- **新上傳金鑰**：`android-upload-v2.keystore`，alias `upload`，SHA1 `55:6B:6B:42:D1:76:C8:FF:D7:29:C5:4E:42:E7:3F:7A:8C:5C:E3:CC`。
- 金鑰檔和密碼（`keystore-pass.txt`）**只在吳昀慶手上**。請備份兩份（雲端硬碟 + 本機）。再遺失就要再走一次兩個工作天的重設。
- 上傳的 AAB 若被 Play 拒絕「簽署金鑰錯誤」，先確認重設已核准、用的是 v2 金鑰。

### 打包指令

先裝 Android Studio（附 SDK）和 Node。然後在 repo 根目錄：

```bash
export ANDROID_HOME=~/Library/Android/sdk
export KEYSTORE=~/keys/android-upload-v2.keystore
export KS_PASS='（keystore-pass.txt 的內容）'
python3 -m pip install pillow      # 第一次才需要，用來產生 App 圖示
VERSION_CODE=29 tools/build-android.sh
```

產出 `~/cap-android/oldmapstroll-v29.aab`，最後會印出簽章指紋，確認是 `55:6B:6B…` 再上傳。版號只能往上加，Play 上最新是 25，v26–v28 打過但沒上傳。

## iOS 打包（Mac）

```bash
cd ios-app
npm install
npm run sync-www
python3 ../tools/make-beta.py --native www/index.html   # 換成含漫遊模式的版本
npx cap sync ios && npx cap open ios
```

Xcode：
- `App/App/Info.plist` 要有 `NSLocationWhenInUseUsageDescription` 和 `NSLocationAlwaysAndWhenInUseUsageDescription`，沒有的話定位會被 iOS 靜默拒絕（App Store 使用者回報過無限 loading）。這個檔是 Capacitor 生成的，不在 repo 裡，重建 ios 專案要重加。
- General 分頁改 Version / Build → 裝置選 **Any iOS Device** → Product → Archive → Distribute App → App Store Connect。
- 出口合規：只使用標準加密（HTTPS），屬豁免。
- Apple 警告 MinimumOSVersion 14.0 太低：2027 年春天前要改成 15.0（Xcode → App target → General → Minimum Deployments）。

## 待辦（依優先順序）

1. **Android v29 上傳 Play**：含 CARTO 金鑰、定位修正、歷史事件圖層。目前 Play 上的 v25 底圖會出浮水印。
2. **iOS 1.4**：照上方流程重打，送審說明「修正底圖無法顯示的問題」。1.3 一樣有浮水印問題。
3. **CARTO 後台設網域限制**：只允許 `yunching0513.github.io`。金鑰曾貼在對話裡，能重發就重發一組，換掉上述四處。
4. **打賞內購（IAP）**：已規劃、未實作。需要先在 App Store Connect 和 Play Console 建立三個消耗型商品 `tip_coffee_s` / `tip_coffee_m` / `tip_coffee_l`（NT$33 / 90 / 170）。網頁版維持 Ko-fi（`https://ko-fi.com/yunching0513`）。Apple 不允許 App 內導向外部付款，所以原生版要換成 IAP。
5. **街景漫遊升上正式站**：目前只在 β 站和原生 App。做法是讓 `make-beta.py` 的注入也套到根目錄 `index.html`（要防重複注入）。
6. **產品策略分析**：使用者提供了 Step0（問題定義）、Step1（邏輯樹、3C、價值鏈）兩份方法論文件，要求「大改版、讓 App 爆紅」。第一階段理解已提出（核心重構：問題不是產品不好，是從沒被看見），**等使用者確認後**才進第二階段，結果寫進 `docs/`。

## 已完成、可參考的產出

- 實體明信片 12 張組：A6 加 3mm 出血的印刷 PDF、Pinkoi 上架文案（已交付，不在 repo 裡）。
- 授權整理：明信片影像皆為公有領域（PD-Japan 或 PD-Taiwan），出處在 `data/postcards.js` 的 `source` / `author` / `credit`。

## 協作習慣

- 使用者是吳昀慶，繁體中文，台灣用語。累的時候偏好短句、一次只給一件要做的事。
- 只能在使用者本人帳號完成的事（上傳 Play、送審 App Store、建 IAP 商品、CARTO 後台）要給清楚的點擊步驟，卡住就請對方截圖。
