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

## Generate Real Aggregate Derived Data

```bash
python scripts/generate_real_derived_data.py
```

此腳本從公開上游 repo 讀取資料，但只輸出低風險 aggregate CSV；不保存 raw upstream rows。

注意：上游 repo 可能高頻更新，因此 CI 不會自動執行此腳本。更新真實 derived data 時，請在本地執行、檢查差異，再 commit。
