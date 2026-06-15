# 公民科學回報後端（Google Sheet + Drive）

讓使用者在 App 內回報「明信片位置更正」或「貢獻老照片」。後端完全跑在你
自己的 Google 帳號上：文字寫進 Google 試算表，照片存進 Drive 資料夾。
免費、資料歸你所有、不需要伺服器。

## 運作方式

```
App（index.html）
   │  使用者按「回報」→ 填表 → 送出
   ▼  POST（text/plain JSON，照片已壓到 ≤1600px）
Google Apps Script Web App（Code.gs 的 doPost）
   ├─ 在試算表新增一列（時間、類型、明信片、說明、座標、署名…）
   └─ 若有照片 → 存到 Drive 資料夾 → 連結寫進該列
```

你只要定期打開試算表審核：採用的位置更正就改 `index.html` 裡 `POSTCARDS`
的 `lat/lng`；採用的老照片就放進 `icons/postcards/`，並在 `source` 欄位
依貢獻者署名致謝。

## 部署步驟（約 5 分鐘）

1. 開一份新的 Google 試算表（sheets.new）。命名隨意，例如「散策回報」。
2. 在該試算表選 **擴充功能 → Apps Script**。
3. 把本資料夾的 `Code.gs` 內容整段貼進去，覆蓋預設的 `myFunction`，存檔。
   - 因為腳本是綁定在這份試算表上的，`SHEET_ID` / `PHOTO_FOLDER_ID`
     都可留空，會自動使用本試算表與雲端硬碟裡的「散策回報照片」資料夾。
4. 點右上 **部署 → 新增部署作業**。
   - 類型選 **網頁應用程式 (Web app)**。
   - 「執行身分」：**我**。
   - 「具有存取權的使用者」：**任何人 (Anyone)**。
   - 按部署，第一次會要求授權（允許存取試算表與雲端硬碟）。
5. 複製產生的 **網頁應用程式網址**（形如
   `https://script.google.com/macros/s/AKfy.../exec`）。
6. 打開 `index.html`，找到：
   ```js
   const REPORT_ENDPOINT = '';
   ```
   把網址貼進去：
   ```js
   const REPORT_ENDPOINT = 'https://script.google.com/macros/s/AKfy.../exec';
   ```
   commit、push，等 GitHub Pages 更新後，App 內明信片卡片就會出現「回報」鈕。

## 測試是否部署成功

- 直接用瀏覽器開那個 `/exec` 網址，應該看到
  `{"ok":true,"service":"taiwan-old-map-stroll report endpoint"}`。
- 在 App 收藏任一明信片 → 打開卡片 → 「回報」→ 填說明 → 送出，
  幾秒後試算表應出現新的一列。

## 注意事項

- **配額**：個人 Google 帳號每天約 20,000 次 doPost、數十分鐘的執行時間，
  對這個用途綽綽有餘。
- **回應讀取**：App 用 `mode:'no-cors'` 送出（Apps Script 不方便處理
  CORS 預檢），所以前端不讀回應、採「樂觀送出」。送不出去（離線）時會先
  存在使用者手機，連上網路後自動補送。
- **照片權限**：預設存成「私人」，只有你看得到。若想公開分享連結，
  把 `Code.gs` 裡 `DriveApp.Access.PRIVATE` 改成 `ANYONE_WITH_LINK`。
- **改版重新部署**：每次改 `Code.gs` 後要「部署 → 管理部署作業 → 編輯
  （鉛筆）→ 版本選『新版本』→ 部署」，網址才會生效；沿用同一個部署
  作業網址就不必再改 `index.html`。
- **隱私／商店申報**：啟用本功能後，App 會「上傳使用者提供的內容（文字、
  選填座標、選填照片與聯絡方式）」。上架 Google Play / App Store 時，記得
  在「資料安全 / App 隱私」中據實申報這項資料蒐集（用途：App 功能；可選擇
  是否與身分連結——預設不要求登入，屬匿名）。建議等商店審核穩定後再把
  `REPORT_ENDPOINT` 填上開啟。
