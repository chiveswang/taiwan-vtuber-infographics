# Provenance Log

本紀錄只追蹤公開衍生資料與圖表的來源流程，不記錄原始資料內容。

## 2026-06-07 Initial Sample Data

```yaml
source_project: none
source_project_visibility: not-applicable
source_snapshot_date: 2026-06-07
derived_output:
  - data/derived/aggregate-summary.csv
  - data/derived/content-category-trends.csv
  - charts/exports/sample-content-category-share.svg
privacy_review_status: sample-only
raw_data_published: false
notes: Fake aggregate demo data only. No real upstream source data imported.
```

## 2026-06-07 Upstream Source Review

```yaml
source_project:
  - TaiwanVtuberData/TaiwanVtuberTrackingData
  - TaiwanVtuberData/TaiwanVTuberTrackingDataArchive
source_project_visibility: public
source_project_url:
  - https://github.com/TaiwanVtuberData/TaiwanVtuberTrackingData
  - https://github.com/TaiwanVtuberData/TaiwanVTuberTrackingDataArchive
license_reviewed: The Unlicense
attribution_required_by_license: false
derived_output: []
privacy_review_status: source-review-only
raw_data_published: false
notes: GitHub metadata and LICENSE files report The Unlicense. README files did not list additional attribution requirements. This repo should still cite upstream repositories for provenance when real derived aggregate outputs are added.
```

## 2026-06-07 First Real Aggregate Derived Outputs

```yaml
source_project:
  - TaiwanVtuberData/TaiwanVtuberTrackingData
source_project_visibility: public
source_project_url:
  - https://github.com/TaiwanVtuberData/TaiwanVtuberTrackingData
source_snapshot_date: 2026-06-07
derived_output:
  - data/derived/platform-coverage-summary.csv
  - data/derived/source-coverage-summary.csv
  - charts/exports/platform-coverage-summary.svg
privacy_review_status: reviewed
raw_data_published: false
notes: Derived from public upstream track-list field presence and repository file metadata. No names, IDs, channel IDs, URLs as rows, raw tracking rows, or individual sensitive time series are published.
```
