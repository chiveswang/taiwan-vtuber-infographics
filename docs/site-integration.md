# Site Integration Notes

這個 repo 是公開資料與圖表素材的來源。順揚宮網站的遊樂場工具頁面是展示端。

## 邊界

- 本 repo 負責 README、PRIVACY、methodology、derived data、charts 與 scripts。
- 順揚宮網站只應讀取已公開、已聚合、已通過 privacy review 的資料。
- 順揚宮網站不應直接讀取另一個專案的原始 tracking data。
- 若網站需要互動圖表，應使用 `data/derived/` 或 `charts/exports/` 的公開產物。
- 順揚宮網站可顯示本 repo 的 provenance 說明，但不應顯示私有上游 repo URL、本機路徑或原始資料檔名。

## 建議資料交換方式

- 靜態 CSV 或 JSON。
- 預先輸出的 PNG / SVG 圖表。
- 版本化的 release artifact。

## 建議讀取入口

- `data/derived/public-index.json`
- `data/derived/*.csv`
- `charts/exports/*.svg`

## 不建議

- 在網站端即時查詢原始追蹤資料。
- 在網站端計算個人層級時間序列。
- 放入個人排名、敏感活動時間或身份推測。
