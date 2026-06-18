# 散策 App — Session 交接文件

> 產生日期：2026-06-18  
> 分支：`claude/busy-johnson-mrlpmo`（已合併至 `main`，SW v58）

---

## 本 Session 完成的工作

### 1. Android 底部面板手勢修復
- **問題**：底部 bottom-sheet 的「往下滑把手」無法收合面板
- **修法**：在 `sheet-handle` 上加 `touchstart` / `touchend` 事件偵測，滑動 > 28px 才觸發收合/展開，避免誤觸
- **影響範圍**：`index.html`（主 App）、`demo/japan-tokyo.html`（關東頁）

### 2. Android 開啟面板閃爍修復
- **問題**：底部面板展開時有「閃一下」的視覺問題
- **根因**：`max-height` 動畫在 Android WebView 渲染時機不一致
- **修法**：改用 `transform: translateY()` 做 GPU 合成動畫；初始狀態用 `.no-anim` class 防止開場動畫觸發

### 3. 明信片每日抽卡功能
- **規則**：4 小時冷卻、每日最多 3 次
- **儲存**：`taiwanOldMaps.pcDraws`（localStorage，JSON 時間戳陣列）
- **邏輯**：`drawStatus()` / `loadDrawLog()` / `persistDrawLog()`
- **UI**：`#pc-draw-btn`，顯示冷卻倒數或剩餘次數

### 4. 音效系統擴充
新增以下音效（全部 Web Audio API 合成，無音訊檔）：
| 音效 | 時機 |
|---|---|
| `sfx.page()` | 城市切換、圖層切換 |
| `sfx.rare()` | 抽到從未見過的新明信片 |
| `sfx.tap()` | 面板展開 |
| `sfx.draw()` | 抽卡動畫中（ambient） |
| `sfx.ready()` | 冷卻結束（ambient） |

設定 UI 位於頁尾：開關按鈕、精簡模式（ambient 音靜音）、音量滑桿  
LocalStorage 鍵：`taiwanOldMaps.sound` / `taiwanOldMaps.soundVol` / `taiwanOldMaps.soundMinimal`

### 5. iOS App Store 退件修復（Guideline 2.5.4）
- **退件原因**：`UIBackgroundModes` 包含 `bluetooth-peripheral`（Capacitor 預設注入，App 根本未使用）
- **修法路徑**：
  1. `PlistBuddy -c "Delete :UIBackgroundModes"` 移除整個陣列
  2. 確認 App 有裝 `@capacitor-community/background-geolocation`（真的需要背景定位）
  3. 還原 `UIBackgroundModes: [location]`（只保留 location，拿掉 bluetooth）
  4. 同步移除 `NSLocationAlwaysUsageDescription` 與 `NSLocationAlwaysAndWhenInUseUsageDescription` 中誤導性的「永遠允許」描述 → 最終只保留 `WhenInUse` 版本（並回寫正確說明）
  5. Build number 升至 5，Archive + Upload
- **審查備註已提交**（Resolution Center 回覆 + Review Notes）
- **Xcode 專案位置（本機 Mac）**：`~/taiwan-historical-maps-app/ios/App/`

### 6. 時光快轉功能強化
- **速度選擇**：快（1.2s）/ 中（4s）/ 慢（6s），記住偏好，預設「中」  
  LocalStorage 鍵：`taiwanOldMaps.tlSpeed`
- **年代勾選預設全不選**：使用者自己決定要播哪些年代
- **螢幕錄影提示**：說明用手機內建螢幕錄影儲存影片（canvas 污染問題導致無法做瀏覽器端影片匯出）

### 7. 明信片改大區分組收合
- **前**：22 個縣市各一個收合夾（層次過多）
- **後**：北部 / 中部 / 南部 / 東部 / 離島 5 大區收合，區內保留縣市小標題
- **資料變更**：`POSTCARD_CITIES` 每個城市加入 `region` 欄位；新增 `POSTCARD_REGIONS` 陣列
- **持久化**：`taiwanOldMaps.postcardOpenRegions`（舊的 `postcardOpenCities` 保留在備份清單但已不使用）

---

## 目前程式狀態

| 項目 | 狀態 |
|---|---|
| Service Worker | v58 |
| 主分支 | `main`（已部署，GitHub Pages） |
| 開發分支 | `claude/busy-johnson-mrlpmo` |
| iOS App | Build 5 已上傳，等待 Apple 重審 |
| Android App | Play Console 有一個空草稿 release（可 Discard，不影響線上版） |

---

## 待辦 / 未完成事項

### iOS App Store
- [ ] 等待 Apple 重審結果（email 通知）
- 核准 → 填版本說明、截圖，發布
- 再退件 → 把退件訊息貼出來，重新分析

### Google Play
- [ ] 進 Play Console 把空草稿 release Discard（不影響線上，但整潔）

---

## 下一步開發方向（後續 Session）

### 即時 PPGIS 後端（已確認方向）
- **目標**：從「非同步人工審核閉環」升級為「多使用者即時知識共創」
- **技術選型**：Supabase（PostgreSQL + PostGIS + Realtime）
- **功能範疇**：
  - 使用者勘誤上傳（位置修正、歷史詮釋補充）
  - 多源交叉驗證流程（研究者審核介面）
  - 審核通過後即時推送至所有用戶端
- **備選方案**：擴展現有 Cloudflare Workers + D1（最少改動，但實時能力弱）

### 其他候選功能
- 桌機版影片匯出按鈕（需 Cloudflare proxy 開 CORS + `MediaRecorder`，僅桌機可用）
- 明信片勘誤上傳 UI（先做前端表單，後端待 Supabase 就緒）

---

## 學術論文進度

投稿研討會，已收到審查意見，修訂摘要已完成：

**審查意見對應：**
1. ✅ 正面評價，無需回應
2. ✅ 補充非同步審核閉環機制說明
3. ✅ 補充多源交叉驗證與來源標注說明
4. ✅ 補充「接近觸發 vs. 主動填報」差異，強化步行核心 PPGIS 框架原創性
5. ✅ 錯字「函蓋」→「涵蓋」（請在原始 Word 檔確認全文）

**修訂摘要**：已在對話中產生，請複製至 Word 檔提交。

---

## 關鍵技術備忘

```
// 底部面板狀態（行動版）
panelEl.classList.toggle('peek', true/false)  // peek = 收合

// 時光快轉速度
TL_DWELL = { fast: 1200, mid: 3400, slow: 6000 }  // ms
localStorage: 'taiwanOldMaps.tlSpeed'

// 抽卡規則
DRAW_COOLDOWN_MS = 4 * 60 * 60 * 1000
DRAW_MAX_PER_DAY = 3
localStorage: 'taiwanOldMaps.pcDraws'

// iOS Xcode 專案
~/taiwan-historical-maps-app/ios/App/App/Info.plist
目前 UIBackgroundModes = [location]（無 bluetooth-peripheral）
Build = 5, Version = 1.0
```
