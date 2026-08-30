# Data, Chart, and Site License Policy

本專案自 2026-08-31 起採用以下正式授權組合：

| 範圍 | SPDX identifier | 授權 |
| --- | --- | --- |
| 程式碼、腳本與 workflow | `MIT` | repo 根目錄 `LICENSE` 中的 MIT License |
| `data/derived/` | `CC-BY-4.0` | Creative Commons Attribution 4.0 International |
| `charts/exports/` | `CC-BY-4.0` | Creative Commons Attribution 4.0 International |
| `site/` 的文字、版面內容與公開網站素材 | `CC-BY-4.0` | Creative Commons Attribution 4.0 International |

若檔案本身、`data/derived/public-index.json` 或本文件有更明確的授權標記，依較具體的標記為準。第三方素材與上游資料仍保留其原始授權，不因被本 repo 引用而改變。

## Attribution

再利用 CC BY 4.0 內容時，請標示：

> Taiwan VTuber Infographics contributors, `https://github.com/chiveswang/taiwan-vtuber-infographics`, CC BY 4.0.

若成果來自 `real-derived` dataset 或 chart，建議在 attribution 中保留 `data/derived/public-index.json` 的 `source_url`、`provenance` 或 `source_dataset` 資訊，以維持上游來源鏈。這是 provenance 實作指引，不是上游 The Unlicense 的法定要求，也不增加 CC BY 4.0 以外的授權限制。

完整 CC BY 4.0 條款：<https://creativecommons.org/licenses/by/4.0/legalcode>

## Privacy and Safety Boundary

CC BY 4.0 處理著作權授權，不代表本專案同意重新識別、doxxing、身份推測或以聚合資料反向追蹤個人。維護者仍會依 `PRIVACY.md`、publication gate 與 correction/removal 流程決定本 repo 未來發布什麼內容。

已合法取得的 CC BY 4.0 授權不能因後續 correction、removal 或 opt-out 而追溯撤回；本專案能做的是停止後續散布、修正目前版本並清楚記錄更正。

## Upstream Data License Notes

已檢查的公開上游資料 repo：

- [TaiwanVtuberData/TaiwanVtuberTrackingData](https://github.com/TaiwanVtuberData/TaiwanVtuberTrackingData): The Unlicense。
- [TaiwanVtuberData/TaiwanVTuberTrackingDataArchive](https://github.com/TaiwanVtuberData/TaiwanVTuberTrackingDataArchive): The Unlicense。

The Unlicense 通常不要求 attribution。即使如此，本專案仍應在資料來源與 provenance 文件中標記上游 repo，避免讓公開衍生資料看起來像無來源資料。
