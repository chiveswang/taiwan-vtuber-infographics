# Source Project and Provenance

本專案的公開資料可由另一個既有資料專案衍生而來，但本 repo 不公開原始資料、不公開個人層級追蹤資料，也不公開任何可能造成身份推測或安全風險的來源細節。

## Source Project Boundary

公開文件應標記資料來源層級：

- `source_project`: 產生候選資料的上游專案或資料流程。
- `source_snapshot_date`: 取用候選資料的日期。
- `derived_output`: 本 repo 中公開的衍生資料或圖表。
- `privacy_review_status`: 是否已完成 privacy review。

如果上游專案本身不是公開 repo，請不要在公開文件中放入：

- 私有 repo URL。
- 本機路徑。
- 原始資料檔名。
- 任何可連回私人資料庫、token、帳號或未公開資料的細節。

## Recommended Public Wording

可使用：

> Derived from an upstream source project and transformed into aggregate-only public outputs after privacy review.

不建議使用：

> Raw tracking data exported from ...

> Complete personal activity records from ...

> Individual-level VTuber tracking database ...

## Provenance Template

每次導入公開資料前，建議建立一筆 provenance note：

```yaml
source_project: upstream-source-project
source_project_visibility: private-or-internal
source_snapshot_date: YYYY-MM-DD
derived_output:
  - data/derived/example.csv
  - charts/exports/example.svg
privacy_review_status: reviewed
raw_data_published: false
notes: Aggregate-only output. No raw tracking data, private identity information, or individual sensitive time series included.
```

## First Public Repo State

目前 repo 只包含 sample aggregate data。尚未導入任何真實上游資料。

## Upstream Repositories Reviewed

以下上游 repo 是公開資料來源候選。它們目前採用 The Unlicense，README 未列出額外 attribution 要求。雖然授權沒有強制要求標記，本專案仍應主動標記來源 repo，作為 provenance 與公開透明度的一部分。

- current: [TaiwanVtuberData/TaiwanVtuberTrackingData](https://github.com/TaiwanVtuberData/TaiwanVtuberTrackingData)
- archive: [TaiwanVtuberData/TaiwanVTuberTrackingDataArchive](https://github.com/TaiwanVtuberData/TaiwanVTuberTrackingDataArchive)

Public attribution wording:

> Aggregate outputs may be derived from public upstream repositories maintained under TaiwanVtuberData, including the current and archive Taiwan VTuber tracking data repositories. This project republishes only privacy-reviewed aggregate or derived outputs, not raw tracking data.
