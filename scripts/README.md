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

目前檢查範圍是 `data/derived/**/*.csv`。

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
