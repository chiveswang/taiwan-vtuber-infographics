# Scripts

此資料夾預留給資料驗證與圖表產生腳本。

第一階段不需要大量程式碼。若新增腳本，應優先處理：

- public data schema validation。
- prohibited fields check。
- aggregate-only chart generation。
- source URL 與 last verified 欄位檢查。

## Validate Public Data

```bash
python scripts/validate_public_data.py
```

目前會檢查 `public-index.json` 列出的所有公開 CSV、JSON、SVG、HTML、JavaScript 與 CSS。`site/` 檔案還必須符合 `REVIEWED_SITE_SHA256` 的已審核內容指紋；新增網站檔案或修改 UI copy／payload 時，必須先完成隱私複審再更新指紋。動態或內嵌 JavaScript data payload 不在公開 schema 內，應改用已列入 manifest 且通過值層級驗證的 CSV／JSON。

## Generate Sample Charts

```bash
python scripts/generate_sample_charts.py
```

目前只從 fake aggregate demo data 產生 `charts/exports/sample-content-category-share.svg`。

## Validate Public Index

```bash
python scripts/validate_public_index.py
```

此檢查確認 `data/derived/public-index.json` 的必要欄位存在，且索引內的檔案路徑可找到。

## Generate Real Aggregate Derived Data

```bash
python scripts/generate_real_derived_data.py
```

此腳本從公開上游 repo 讀取資料，但只輸出低風險 aggregate CSV；不保存 raw upstream rows。

注意：上游 repo 可能高頻更新，因此 CI 不會自動執行此腳本。更新真實 derived data 時，請在本地執行、檢查差異，再 commit。

## Import Activity Dashboard Aggregates

```bash
python scripts/import_activity_dashboard_aggregates.py path/to/vtuber_activity_dashboard.html
```

此腳本從既有 `activity/vtuber_activity_dashboard.html` 抽取白名單聚合欄位，只輸出：

- `data/derived/activity-quarterly-summary.csv`
- `data/derived/cohort-quarterly-summary.csv`

不要把來源 HTML、頻道搜尋資料、個人排行、頻道 ID、影片標題、直播 URL 或個別軌跡資料放入本 repo。

匯入器會依公開門檻 10 抑制小樣本創作者 cell，並將 cohort 粗化為單一 `all-settled` 桶。內容項目數與精確最大觀看值不匯入，因為它們不代表不同創作者人數。

## Validate Static Dashboard

```bash
python scripts/validate_static_site.py
```

此檢查確認 `site/` 參照的資料、圖表、CSS 與 JS 檔案存在。
