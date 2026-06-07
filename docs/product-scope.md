# Product Scope

本文件決定這個 repo 要提供的公開價值與資訊範圍。它不是資料庫規格，也不是網站 UI 規格，而是公開資料視覺化專案的產品邊界。

## Core Value

這個 repo 的核心價值是：

> 將公開上游資料轉換成 privacy-conscious、aggregate-only、可引用、可重現的台灣 VTuber 生態資訊圖表。

它應該讓一般觀眾、創作者、研究者或網站使用者看見「生態趨勢」，而不是追蹤或比較個別 VTuber。

## Target Audiences

- 一般觀眾：快速理解台灣 VTuber 生態的公開趨勢。
- 創作者與社群營運者：觀察內容類型、平台分布與公開活動型態。
- 資料視覺化讀者：取得可重現、低風險的 aggregate data 與 chart assets。
- 順揚宮網站遊樂場：引用公開圖表與 derived datasets，做成互動展示頁。
- OSS reviewers：檢查此 repo 是否有清楚方法論、授權、來源標記與隱私邊界。

## What This Repo Should Provide

### 1. Aggregate Ecosystem Snapshot

回答：

- 公開資料中可見的 VTuber 生態規模大概如何變化？
- 平台分布如何？
- 內容分類大致如何？
- 公開資料來源的更新狀態如何？

可提供：

- monthly aggregate counts。
- platform share。
- content category share。
- source coverage summary。
- last verified coverage。

避免：

- 個人排名。
- 個人級活動量。
- 可反推作息的時間細節。

### 2. Time-Based Public Trends

回答：

- 月份或季度層級的公開趨勢如何變化？
- 哪些內容分類在某段期間較常出現？
- 公開資料是否呈現新出道、休止、畢業等宏觀趨勢？

可提供：

- month / quarter trends。
- debut / inactive / graduation aggregate trends。
- content category trend lines。
- platform trend lines。

避免：

- 個別 VTuber 的時間線。
- 每日、每小時、直播場次級資料。
- 即時狀態。

### 3. Public Source Transparency

回答：

- 圖表從哪些公開上游 repo 或公開來源衍生？
- 哪些資料是 sample，哪些是 real derived output？
- 何時驗證？
- 如何修正或移除？

可提供：

- `public-index.json`。
- provenance log。
- source project notes。
- correction / removal process。

避免：

- 私有本機路徑。
- 原始資料檔名細節。
- 未公開資料來源。

### 4. Website-Ready Infographic Assets

回答：

- 順揚宮網站可以直接使用哪些公開素材？
- 每張圖表對應哪份 derived dataset？
- 這張圖表是否 sample / real / deprecated？

可提供：

- SVG / PNG chart exports。
- CSV / JSON derived datasets。
- chart metadata。
- alt text 或短說明。

避免：

- 網站端直接處理 raw upstream data。
- 網站端重新計算敏感個人資料。

## Proposed First Real Outputs

第一批真實資料導入應從低風險、高價值、容易聚合的項目開始。

### Batch 1: Source and Coverage Overview

資料產品：

- `source-coverage-summary.csv`
- `platform-coverage-summary.csv`

圖表：

- platform share。
- source freshness / last verified distribution。

原因：

- 風險低。
- 不需要個人時間序列。
- 適合驗證來源標記與 public-index 流程。

### Batch 2: Monthly Aggregate Activity Categories

資料產品：

- `monthly-content-category-summary.csv`
- `monthly-public-status-summary.csv`

圖表：

- content category by month。
- public status by month。

原因：

- 有資訊價值。
- 月份聚合可降低隱私風險。
- 適合網站互動圖表。

### Batch 3: Ecosystem Timeline Without Individual Tracking

資料產品：

- `quarterly-ecosystem-summary.csv`

圖表：

- quarterly trend overview。
- debut / inactive / graduation aggregate trend, if source quality is sufficient。

原因：

- 能呈現生態變化。
- 不需要公開個人資料。

## Do Not Build

即使上游資料可以支援，也不應做：

- 個人排行榜。
- 個人活躍時間分析。
- 個人訂閱數或觀看數成長曲線。
- 個人合作網絡圖。
- 即時追蹤 dashboard。
- 中之人、身份、地理位置或私人關係推測。
- 可下載的原始資料鏡像。

## Website Experience Direction

順揚宮網站遊樂場頁面應呈現為「溫和的資料探索工具」，不是監控介面。

建議模組：

- ecosystem snapshot。
- monthly trend explorer。
- platform / content mix。
- source and privacy notes。
- correction / removal link。

不建議模組：

- search individual VTuber activity。
- top performer ranking。
- real-time dashboard。
- individual timeline。

## Success Criteria

這個 repo 達標時應能做到：

- 任何公開資料都能追溯來源流程。
- 網站能透過 `public-index.json` 找到可用素材。
- 每份資料都有 `source_url` 或來源說明與 `last_verified`。
- 每張圖表都有對應 derived dataset。
- 沒有 raw tracking data。
- 沒有個人層級敏感時間序列。
- 外部 reviewer 可以理解本專案為 privacy-conscious data visualization，而不是 tracking database。
