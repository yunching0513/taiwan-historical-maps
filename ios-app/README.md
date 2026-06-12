# iOS 上架指南 — 台灣舊地圖散策

用 [Capacitor](https://capacitorjs.com/) 把 PWA 包成原生 iOS App。
網頁內容直接內嵌在 App 裡（不是遠端載入），對 App Store 審查較有利。

## 0. Mac 環境準備（一次性）

```bash
# 1. 從 App Store 安裝 Xcode（免費，檔案很大請耐心）
#    第一次打開 Xcode 時同意授權、安裝 iOS 元件

# 2. 安裝 Homebrew（如果還沒有）→ https://brew.sh

# 3. 安裝 Node.js 與 CocoaPods
brew install node cocoapods
```

## 1. 產生 Xcode 專案（一次性）

```bash
git clone https://github.com/yunching0513/taiwan-historical-maps.git
cd taiwan-historical-maps/ios-app

npm install          # 安裝 Capacitor
npm run sync-www     # 把根目錄的 PWA 複製進 www/
npx cap add ios      # 產生 ios/ 原生專案
npx cap open ios     # 用 Xcode 打開
```

> 之後 `ios/` 資料夾請 commit 進 git（裡面會累積你的設定）。

## 2. Xcode 內必做的設定

打開後左側點 **App** 專案 → **App** target：

### Signing & Capabilities
- **Team**：選你的 Apple Developer 帳號
- **Bundle Identifier**：`io.github.yunching0513.oldmapstroll`（應已自動帶入）

### Info（權限說明文字，沒填會被拒審）
按 + 加入以下 key：

| Key | 建議文字 |
|---|---|
| `NSLocationWhenInUseUsageDescription` | 散策需要你的位置，才能在歷史地圖上顯示所在地、記錄路線與收集明信片。 |
| `NSCameraUsageDescription` | 拍照記錄散策路線上的此刻風景。 |
| `NSPhotoLibraryAddUsageDescription` | 將分享卡片與明信片儲存到你的照片。 |

### App Icon
1. 左側 `App/Assets.xcassets` → `AppIcon`
2. 把 `ios-app/resources/appicon-1024.png` 拖進 1024pt 格子

## 3. 真機測試

iPhone 接上 Mac → Xcode 上方裝置選你的 iPhone → ▶ Run。
確認：地圖、定位、明信片、拍照都正常。

## 4. 上傳到 App Store Connect

1. Xcode 上方裝置選 **Any iOS Device (arm64)**
2. 選單 **Product → Archive**
3. 完成後跳出 Organizer → **Distribute App → App Store Connect → Upload**（一路預設值）

## 5. App Store Connect 填寫商店資訊

到 [appstoreconnect.apple.com](https://appstoreconnect.apple.com)：

1. **我的 App → ＋ → 新增 App**：平台 iOS、名稱「台灣舊地圖散策」、
   主要語言 繁體中文、Bundle ID 選剛才那個、SKU 隨意（如 `oldmapstroll`）
2. **App 資訊**：類別選「旅遊」＋「教育」
3. **定價**：免費
4. **App 隱私權**：
   - 隱私權政策 URL：`https://yunching0513.github.io/taiwan-historical-maps/privacy.html`
   - 資料收集問卷：位置資料只在裝置上使用、不離開手機 → 選「不會收集資料」
5. **版本頁**：
   - 截圖：必須附 6.7 吋（1290×2796）。用 Xcode 模擬器（iPhone 15 Pro Max）
     開 App 按 `Cmd+S` 截圖最快。文案可參考 repo 的 `store-listing.md`
   - 描述／關鍵字：同樣參考 `store-listing.md`
6. **建置版本**：選你剛上傳的 build（上傳後要等幾分鐘處理）
7. **審查備註**（重要，降低 4.2 拒審風險）建議寫：
   > This app is far beyond a website wrapper: it overlays 19 historical
   > maps (1904–2003) of Taiwan on modern streets, records GPS strolls,
   > unlocks vintage postcards via geofencing (visit the physical site
   > within 50 m), and collects prefecture seals. All map data is from
   > Academia Sinica's public tile service; postcard images are public
   > domain (Wikimedia Commons).
8. **提交審查**。首次審查通常 1–3 天

## 6. 之後怎麼更新

```bash
cd taiwan-historical-maps && git pull
cd ios-app
npm run sync-www && npx cap sync ios && npx cap open ios
# Xcode：把 Version/Build 加一 → Product → Archive → Upload → 送審
```

## 常見退件與對策

| 退件理由 | 對策 |
|---|---|
| 4.2 Minimum functionality | 引用上面的審查備註，強調 GPS 散策／地理圍欄收集／離線等原生深度功能 |
| 5.1.1 權限說明不清 | 確認三個 Usage Description 都有具體文字 |
| 截圖與實際不符 | 截圖務必用 App 實畫面，不要只放設計圖 |
