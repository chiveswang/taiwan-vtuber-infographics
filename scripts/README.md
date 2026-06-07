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
