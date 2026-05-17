# 臺灣古今地圖疊圖

> **Live Demo** · [yunching0513.github.io/taiwan-historical-maps](https://yunching0513.github.io/taiwan-historical-maps/)
>
> 快速連結：[臺北](https://yunching0513.github.io/taiwan-historical-maps/?city=taipei) · [臺中](https://yunching0513.github.io/taiwan-historical-maps/?city=taichung) · [臺南](https://yunching0513.github.io/taiwan-historical-maps/?city=tainan) · [高雄](https://yunching0513.github.io/taiwan-historical-maps/?city=kaohsiung)

仿照 [xinyi-water-map](https://github.com/yunching0513/xinyi-water-map) 的歷史圖層功能，做成一個涵蓋全臺 22 個直轄市／縣市的單頁應用。視覺套用《昀慶手拙 · 個人設計風格指導書》——清水混凝土系灰階配朱（vermilion）單一強調色，Noto Serif TC + EB Garamond italic + JetBrains Mono 三套字體。

## 結構

```
taiwan-old-maps/
├── index.html             # 統一版（22 縣市切換）
├── manifest.webmanifest   # PWA 應用程式清單
├── sw.js                  # Service worker（離線快取）
├── icons/                 # 應用程式圖示（SVG + 9 種 PNG 尺寸）
├── taichung/index.html    # → 跳轉至 index.html?city=taichung
└── tainan/index.html      # → 跳轉至 index.html?city=tainan
```

單一 HTML 檔，**無需 build、無需 npm install**。Leaflet 透過 CDN 載入，歷史圖磚直接打中研院 GIS tile server。

## 使用方式

### 本地預覽

直接用瀏覽器打開 `index.html` 即可。若想用本地 HTTP server：

```bash
python3 -m http.server 8000
# 開 http://localhost:8000
```

### 深連結（Deep Link）

可用 query string 直接跳到指定城市：

```
index.html?city=taipei
index.html?city=taichung
index.html?city=tainan
index.html?city=kaohsiung
...
```

切換城市後，網址也會自動更新（不重新整理）。

### 部署

放到任何靜態主機（Vercel / Netlify / GitHub Pages / Cloudflare Pages）皆可：

```bash
npx vercel --prod
```

## 涵蓋城市（22 縣市）

| 區域 | 縣市 |
|------|------|
| 北 North | 臺北、新北、基隆、桃園、新竹市、新竹縣、宜蘭 |
| 中 Central | 苗栗、臺中、彰化、南投、雲林 |
| 南 South | 嘉義市、嘉義縣、臺南、高雄、屏東 |
| 東 East | 花蓮、臺東 |
| 離島 Islands | 澎湖、金門、連江 |

> 金門、連江（馬祖）為離島，中研院全臺尺度圖磚對其覆蓋有限，部分年代可能無資料。應用會自動顯示提示。

## 圖層

19 張全臺尺度歷史圖（中央研究院 GIS 圖磚），依年代分四組：

**日治時期 1904–1944**

| # | 年代 | 名稱 | 來源代號 | maxNativeZoom |
|---|------|------|----------|---------------|
| 01 | 1904 | 臺灣堡圖 | `JM20K_1904` | 17 |
| 02 | 1905 | 十萬分一臺灣圖 | `JM100K_1905` | 14 |
| 03 | 1916 | 蕃地地形圖 | `JM50K_1916` | 15 |
| 04 | 1920 | 五萬分一地形圖（土木局） | `JM50K_1920` | 15 |
| 05 | 1921 | 二萬五千分一地形圖 | `JM25K_1921` | 17 |
| 06 | 1924 | 陸地測量部五萬分一 | `JM50K_1924_new` | 15 |
| 07 | 1944 | 航照修正版地形圖（部分覆蓋） | `JM25K_1944` | 16 |

**美軍時期 1944–1945**

| # | 年代 | 名稱 | 來源代號 | maxNativeZoom |
|---|------|------|----------|---------------|
| 08 | 1944 | 美軍地形圖 25K-A | `AM25K_1944A` | 15 |
| 09 | 1944 | 美軍地形圖 25K-B | `AM25K_1944B` | 15 |
| 10 | 1944 | 美軍地形圖 50K | `AM50K_1944` | 15 |
| 11 | 1945 | 美軍臺灣城市地圖 | `AMCityPlan_1945` | 17 |

**經建版 1950–2003**

| # | 年代 | 名稱 | 來源代號 | maxNativeZoom |
|---|------|------|----------|---------------|
| 12 | 1950 | 經建版地形圖 25K | `TM25K_1950` | 16 |
| 13 | 1956 | 五萬分一地形圖 | `TM50K_1956` | 16 |
| 14 | 1989 | 經建版地形圖（一版） | `TM25K_1989` | 16 |
| 15 | 1993 | 經建版地形圖（二版） | `TM25K_1993` | 15 |
| 16 | 2001 | 經建版地形圖（三版） | `TM25K_2001` | 16 |
| 17 | 2003 | 經建版地形圖（四版） | `TM25K_2003` | 17 |

**衛星影像 1966–1969**

| # | 年代 | 名稱 | 來源代號 | maxNativeZoom |
|---|------|------|----------|---------------|
| 18 | 1966 | CORONA 衛星影像 | `Taiwan_Corona_1966` | 14 |
| 19 | 1969 | CORONA 衛星影像 | `Taiwan_Corona_1969` | 14 |

圖層為單選（同時只顯示一張歷史圖），每張可獨立調整透明度（0%–100%，預設 70%）。被選中的圖層左側出現朱色短條（與設計準則中 section 標題的處理一致）。

> **Zoom**：地圖最大支援 zoom 20。歷史圖層超過 `maxNativeZoom` 時 Leaflet 會自動 upscale（畫質變模糊但圖層持續可見）。1904 / 1921 / 2003 / 1945 城市圖 是原生 zoom 17，可放大到街區級。CORONA 衛星只到 14，適合區域尺度觀察。

## 設計準則對應

| 元素 | 設計準則來源 | 對應 UI |
|------|-------------|---------|
| 背景／面板底色 | `--paper #F1EFE9` / `--paper-2 #EAE8E2` | 控制面板紙色底 |
| 強調色 | `--indigo #C15F3C`（朱 shu） | 啟用圖層左側 3px 條、現役城市標記、滑桿 thumb |
| 標題字體 | Noto Serif TC 600，letter-spacing 0.18em | 「臺灣 古今」、城市名 |
| 內文字體 | Noto Sans TC 300 | 圖層說明、提示 |
| 英文／編號 | EB Garamond italic | "Taiwan · Historical Overlay"、`01`–`04` 編號 |
| 技術細節 | JetBrains Mono | 經緯度、年代、百分比 |
| 質地 | SVG fractal noise，opacity 0.30 | 面板紙紋 |
| 分隔線 | 1px solid `--stone` / 1px dotted `--silver` | 面板邊界、分組之間 |
| Section 標頭裝飾 | 48×3px 朱色短條 | 標題下方裝飾線 |
| Region 分組 | hairline + zh-serif 大字距 | 「北 · 中 · 南 · 東 · 離島」 |

## 安裝成手機 App（PWA）

這是 Progressive Web App，**iOS / Android / 桌面都可以「安裝」當原生 App 用**——全螢幕、自己的桌面圖示、無瀏覽器網址列。

### iOS（Safari）

1. 用 **Safari** 開 [yunching0513.github.io/taiwan-historical-maps](https://yunching0513.github.io/taiwan-historical-maps/)（必須是 Safari，Chrome on iOS 不支援）
2. 點下方分享按鈕 ⬆️
3. 滑下找「加入主畫面 / Add to Home Screen」
4. 命名（預設「古今」）→ 加入

### Android（Chrome）

1. 用 **Chrome** 開網址
2. Chrome 通常會在底部主動跳出「Install App」提示，或點右上角 ⋮ → 安裝應用程式
3. 桌面立刻出現古今 App 圖示

### macOS / Windows 桌面（Chrome / Edge）

1. 開網址
2. 網址列右側會出現「+」安裝圖示，按下後新增到 Dock / 開始功能表

### 安裝後可用什麼？

- ✓ 全螢幕運作，無瀏覽器網址列
- ✓ 自有桌面圖示（古／今 朱印設計）
- ✓ 離線時 UI 仍可載入（圖磚需連線才能取得）
- ✓ Android 長按圖示有 **快速啟動捷徑**：直接跳到臺北／臺中／臺南／高雄
- ✓ GPS 定位、路線記錄、localStorage 路線清單全部正常運作

### 不能做的事（PWA 限制）

- iOS **背景定位無法持續**——記錄路線時必須讓 App 保持在前景，不能切換到其他 App。Android 限制較少但仍建議前景。
- 沒有 App Store 上架（要的話可以接續用 PWABuilder 或 Capacitor 打包）。

## 底圖切換

`01 — BASE` 區段提供兩種底圖選擇：

| 底圖 | 來源 | 涵蓋 | 最大原生 zoom |
|------|------|------|---------------|
| 簡圖 Plain | CartoDB Positron Light | 全球 | 19 |
| 衛星 Satellite | NLSC PHOTO2 通用正射影像 | 全臺（含離島） | 19 |

### 為什麼不用 Google 衛星圖？

Google Maps 的圖磚 URL（`mt0.google.com/vt/...`）雖然技術上可達，但 **直接以 XYZ tile 方式存取違反其服務條款**。正式串接需要 Google Maps JavaScript API + API key + 啟用計費，並使用官方 SDK（不能用 Leaflet 直接拉 tile）。

改用 **NLSC PHOTO2** 是更好的選擇：

- 國土測繪中心是臺灣官方測繪單位，正射影像每年更新
- 全臺涵蓋包括金門、馬祖、澎湖等離島
- 解析度在臺灣境內 **不亞於 Google**，部分都會區更新更頻繁
- 免 API key、免計費、無 ToS 顧慮
- WMTS 標準端點，相容 Leaflet

如果之後真的需要全球範圍的衛星圖（例如出國使用），可以考慮 [Esri World Imagery](https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer)（免 API key、要 attribution）。

## GPS 定位 & 路線記錄

`02 — POSITION` 區段提供兩個功能：

### 定位
- 點「**定位**」啟動 `navigator.geolocation.watchPosition`，瀏覽器會跳出位置權限請求
- 同意後在地圖上顯示朱色脈動標記 + 精準度圈（半透明朱色 fill）
- 狀態卡顯示即時經緯度與 ± m 精準度
- 首次定位成功會自動 fly 到使用者位置（zoom 16）
- 再次點按鈕停止監聽（節省手機電量）

### 路線記錄
- 啟動定位後「**記錄路線**」按鈕才可用
- 點開始記錄後，每個 GPS 更新會被加進軌跡（過濾掉精準度 > 80m 或距上一點 < 3m 的雜訊點）
- 朱色軌跡線即時繪在地圖上（weight 5、圓角）
- 「Recording」狀態卡顯示即時 **距離 / 時間 / 點數**
- 停止後自動存到 `localStorage`（key: `taiwanOldMaps.traces`）

### 已存路線
`03 — TRACES` 區段列出所有記錄：

- 顯示日期、所在城市、總距離、總時間、點數
- 點 row → 在地圖上重新顯示這條軌跡（zoom 自動 fit bounds）
- `GEOJSON` → 下載為標準 GeoJSON Feature（可丟到 [geojson.io](https://geojson.io) / QGIS / Mapbox 等工具）
- `刪除` → 確認後從 localStorage 移除

### 隱私
- 定位資料**完全在你的瀏覽器**，不送到任何伺服器（這個 app 沒有後端）
- 軌跡儲存在 `localStorage`，清掉瀏覽器資料就消失
- HTTPS 或 localhost 才能用 `navigator.geolocation`，部署到任何主機都要用 https
- 想清空所有路線可以在 console 跑 `localStorage.removeItem('taiwanOldMaps.traces')`

## 加入更多圖層

中研院 tile server 還有許多城市專屬的歷史圖。若想加入，在 `HISTORICAL_MAPS` 陣列加一筆：

```js
{
  id: 'tainan1875',
  year: '1875',
  label: '臺灣府城圖',
  en: 'Tainan City Gazetteer',
  url: 'https://gis.sinica.edu.tw/...{z}-{x}-{y}',
},
```

要加新城市則在 `CITIES` 陣列加一筆，指定 `region`（north/central/south/east/island）、`center` 經緯度與初始 `zoom`。

## 致謝

- 歷史圖資：[中央研究院 GIS 專題中心](https://gis.sinica.edu.tw)
- 現代底圖：[CARTO Positron](https://carto.com/) / [OpenStreetMap](https://www.openstreetmap.org/)
- 地圖引擎：[Leaflet](https://leafletjs.com/)
- 結構靈感：[xinyi-water-map](https://github.com/yunching0513/xinyi-water-map)
- 視覺風格：《昀慶手拙 · 個人設計風格指導書》
