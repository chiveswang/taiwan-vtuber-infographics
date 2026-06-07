# Taiwan VTuber Infographics

Taiwan VTuber Infographics 是一個 privacy-conscious infographic / data visualization project，目標是把台灣 VTuber 生態中可公開、可驗證、低風險的資訊整理成溫和的公開圖表、摘要與衍生資料。

這不是原始 tracking data 公開庫，也不是個人層級追蹤資料庫。公開版本應避免任何可能造成 doxxing、身份推測、即時監控或個人作息分析的資料。

## 專案目標

- 建立可公開的 OSS repo，保存方法論、資料邊界、衍生資料格式與圖表輸出。
- 產出可被網站、文章或簡報引用的 aggregate trends 與 infographic assets。
- 保留 source URL、last verified 與 correction / removal request 流程。
- 讓資料視覺化成果可以被重現、審查與修正。

完整產品範圍請見 [docs/product-scope.md](docs/product-scope.md)。從 mock data 進入真實 derived data 的計畫請見 [docs/real-data-intake-plan.md](docs/real-data-intake-plan.md)。

## 這個專案會公開什麼

- 聚合後的趨勢資料。
- 公開頻道或官方社群連結。
- 公開來源 URL。
- last verified date。
- 方法論與資料邊界說明。
- 隱私友善的圖表與摘要。

## 這個專案不公開什麼

- 真名、住址、學校、工作地點、私人 email 或電話。
- 中之人推測、未公開身份推測、私人帳號或私人照片。
- 即時追蹤、即時活躍狀態、個人層級敏感時間序列。
- 從其他專案直接複製、尚未做 privacy review 的原始資料。

## 資料原則

本專案採取最小揭露原則。當資料可能增加個人風險時，應優先移除、模糊化、分組或聚合，而不是追求完整性。

## Source Project and Provenance

公開資料可由另一個既有資料專案衍生，但本 repo 只發布經過 privacy review 的 aggregate-only outputs，不發布原始資料或個人層級追蹤資料。

來源標記方式請見 [docs/sources.md](docs/sources.md) 與 [docs/provenance-log.md](docs/provenance-log.md)。

已檢查的公開上游來源候選包含 `TaiwanVtuberData/TaiwanVtuberTrackingData` 與 `TaiwanVtuberData/TaiwanVTuberTrackingDataArchive`。兩者目前採用 The Unlicense；本專案仍會主動標記來源作為 provenance。

## Repo 結構

- `docs/`: 方法論、資料邊界、資料來源與修正移除流程。
- `data/derived/`: 可公開的衍生資料與聚合資料。
- `data/examples/`: 範例 schema，不放真實敏感資料。
- `charts/`: 圖表說明、輸出圖檔與 notebook 區。
- `scripts/`: 驗證與圖表產生腳本的預留位置。

## Public Outputs

目前 repo 只含 sample aggregate data，不含真實追蹤資料。

- `data/derived/public-index.json`: 給網站或工具讀取的公開素材索引。
- `data/derived/aggregate-summary.csv`: 假資料聚合摘要。
- `data/derived/content-category-trends.csv`: 假資料趨勢範例。
- `data/derived/platform-coverage-summary.csv`: 真實上游資料衍生的平台覆蓋聚合摘要，不含名稱、ID 或原始列。
- `data/derived/source-coverage-summary.csv`: 真實上游 repo 檔案中繼資料衍生的來源覆蓋摘要。
- `charts/exports/sample-content-category-share.svg`: 由假資料產出的示範圖表。
- `charts/exports/platform-coverage-summary.svg`: 由真實聚合資料產出的平台覆蓋圖表。

## Local Checks

```bash
python scripts/generate_real_derived_data.py
python scripts/validate_public_data.py
python scripts/validate_public_index.py
python scripts/generate_sample_charts.py
```

`validate_public_data.py` 會檢查公開 CSV 是否缺少 `source_url` / `last_verified`，並擋下禁止欄位。

## 與順揚宮網站的關係

這個 repo 負責公開資料、方法論與圖表素材的建立。順揚宮網站上的遊樂場工具頁面應只引用這裡已通過 privacy review 的公開資料或圖表，不直接讀取任何原始 tracking data。

## Privacy

請見 [PRIVACY.md](PRIVACY.md)。

## License

程式碼使用 MIT License。資料與圖表授權仍需在正式公開前確認，請見 [LICENSE-DATA.md](LICENSE-DATA.md)。
