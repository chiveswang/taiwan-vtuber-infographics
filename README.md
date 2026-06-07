# Taiwan VTuber Infographics

Taiwan VTuber Infographics 是一個 privacy-conscious infographic / data visualization project，目標是把台灣 VTuber 生態中可公開、可驗證、低風險的資訊整理成溫和的公開圖表、摘要與衍生資料。

這不是原始 tracking data 公開庫，也不是個人層級追蹤資料庫。公開版本應避免任何可能造成 doxxing、身份推測、即時監控或個人作息分析的資料。

## 專案目標

- 建立可公開的 OSS repo，保存方法論、資料邊界、衍生資料格式與圖表輸出。
- 產出可被網站、文章或簡報引用的 aggregate trends 與 infographic assets。
- 保留 source URL、last verified 與 correction / removal request 流程。
- 讓資料視覺化成果可以被重現、審查與修正。

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

## Repo 結構

- `docs/`: 方法論、資料邊界、資料來源與修正移除流程。
- `data/derived/`: 可公開的衍生資料與聚合資料。
- `data/examples/`: 範例 schema，不放真實敏感資料。
- `charts/`: 圖表說明、輸出圖檔與 notebook 區。
- `scripts/`: 驗證與圖表產生腳本的預留位置。

## 與順揚宮網站的關係

這個 repo 負責公開資料、方法論與圖表素材的建立。順揚宮網站上的遊樂場工具頁面應只引用這裡已通過 privacy review 的公開資料或圖表，不直接讀取任何原始 tracking data。

## Privacy

請見 [PRIVACY.md](PRIVACY.md)。

## License

授權方式待定。若資料、程式碼、圖表需要不同授權，應在正式公開前拆開說明。
