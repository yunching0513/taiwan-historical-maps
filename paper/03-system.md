# 3. 系統設計與實作 System Design & Implementation

> 以 repo 內真實實作為據，勿杜撰數據。

## 3.1 資料來源與授權
- 中研院 GIS 專題中心歷史圖磚；NLSC 正射影像；CARTO/OSM 底圖
- 明信片影像：Wikimedia Commons 公領域（PD-Japan / PD-Taiwan），逐張查證授權

## 3.2 系統架構
- 純前端 PWA、Leaflet.js 渲染
- Service Worker：app shell 預快取 + 圖磚 LRU 快取（離線可用）
- 資料層解耦（data/postcards.js）— 同一資料餵 PWA / 多通路

## 3.3 互動設計
- 今昔疊圖、透明度調整、對照拉桿（swipe compare）、時光快轉、四代對照
- 地理圍欄明信片收集（50m）、印章、散策路線記錄與分享卡

## 3.4 公民科學回報機制
- 位置更正 / 貢獻老照片 → Google Apps Script；離線排隊重送

## 3.5 多通路發佈
- 網頁（GitHub Pages，即時）/ iOS（Capacitor）/ Android（Capacitor）
