# Real Data Intake Plan

本文件規劃如何從 mock data 進入第一批真實 derived data。此階段仍不公開 raw upstream data。

## Intake Principles

- 先小批量。
- 先低風險。
- 先聚合。
- 每次導入都更新 provenance log。
- 每次導入都跑 validation。
- 若資料需要人工判斷，先輸出 draft，不直接發布。

## Candidate Inputs From Upstream

上游公開 repo 候選：

- `TaiwanVtuberData/TaiwanVtuberTrackingData`
- `TaiwanVtuberData/TaiwanVTuberTrackingDataArchive`

第一階段只應讀取可被轉成 aggregate summary 的欄位。不要把原始 CSV 複製進本 repo。

## First Intake Questions

導入前先確認：

- 哪些欄位可用來安全產生 platform summary？
- 哪些欄位可用來安全產生 source freshness？
- 哪些欄位可用來安全產生 content category summary？
- 上游資料是否有足夠清楚的 timestamp 可聚合到 month / quarter？
- 是否存在容易誤解或不一致的欄位命名？

## First Real Dataset Targets

### `source-coverage-summary.csv`

目的：說明公開資料來源覆蓋狀況。

建議欄位：

- `aggregate_period`
- `source_project`
- `source_category`
- `aggregate_count`
- `last_verified`
- `notes_for_methodology`

### `platform-coverage-summary.csv`

目的：呈現平台分布，不比較個人。

建議欄位：

- `aggregate_period`
- `platform`
- `aggregate_count`
- `source_project`
- `last_verified`
- `notes_for_methodology`

Status: approved for first real aggregate batch.

### `monthly-content-category-summary.csv`

目的：呈現內容類型趨勢。

建議欄位：

- `aggregate_period`
- `content_category`
- `aggregate_count`
- `source_project`
- `last_verified`
- `notes_for_methodology`

Status: blocked until safe content-category derivation is defined without publishing titles, URLs, or individual timelines.

## Intake Gate

真資料進入 `data/derived/` 前，必須：

- 沒有禁止欄位。
- 沒有個人層級時間序列。
- 沒有 raw upstream rows。
- 有 provenance log。
- 有 publication checklist。
- 有 sample-size review。
- 能通過 `scripts/validate_public_data.py`。
- 能在 `public-index.json` 登記。

## Stop Conditions

遇到以下狀況先停止，不發布：

- 欄位含義不確定。
- 樣本太小，可能反推個人。
- 圖表需要個人名稱才能成立。
- 上游資料品質不足以支撐公開說法。
- 聚合後仍可能造成騷擾、排名或身份推測。
