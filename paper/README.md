# 學術寫作工作區 — 台灣舊地圖散策

這個分支（`paper`）專門用來撰寫關於本專案的學術文章，與程式開發（`main`）分流，
互不干擾。程式碼仍在同一個 repo，方便引用真實的系統設計與資料。

## 如何在新的 Claude 頻道使用
1. 在 Claude Code 開一個新的 session / 對話
2. 指向同一個 repo（`yunching0513/taiwan-historical-maps`）、切到 `paper` 分支
3. 告訴它「依 `paper/outline.md` 繼續撰寫」即可，它會看到下方所有素材

## 目錄結構
| 檔案 | 內容 |
|---|---|
| `outline.md` | 全文大綱與章節規劃、投稿目標、待辦 |
| `00-abstract.md` | 中英文摘要（草稿） |
| `01-introduction.md` | 緒論：動機、問題意識、研究問題 |
| `02-literature.md` | 文獻回顧：PPGIS / 歷史 GIS / PWA / 參與式設計 |
| `03-system.md` | 系統設計與實作（可直接引用 repo 真實架構） |
| `04-method.md` | 研究方法：參與式設計三階段 |
| `05-results.md` | 結果與討論 |
| `06-conclusion.md` | 結論與未來工作 |
| `references.md` | 參考文獻清單 |

## 寫作原則（給接手的 Claude）
- 語言：繁體中文為主，附英文摘要（依投稿目標調整）。
- 系統描述以 repo 內**真實實作**為準（Leaflet.js 渲染、Service Worker LRU 圖磚快取、
  232 張地理圍欄明信片、19 套歷史圖磚、中研院 GIS 開放資料、純前端離線優先架構、
  公民科學回報機制等），不杜撰數據。
- 引用需可查證；歷史影像皆為公領域（PD-Japan / PD-Taiwan，Wikimedia Commons）。
- 作者：吳昀慶、張芸翠、朱穎芃。
