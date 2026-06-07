# Repo Publishing Plan

本文件是公開 GitHub repo 前的本地檢查清單。不要在本文件填寫外部表單內容或 private account details。

## 建議 repo 名稱

首選：`taiwan-vtuber-infographics`

備選：

- `taiwan-vtuber-data-visuals`
- `vtuber-taiwan-public-insights`
- `taiwan-vtuber-open-visuals`

## 發布前檢查

1. 確認 `git status` 是乾淨的。
2. 執行 `python scripts/validate_public_data.py`。
3. 執行 `python scripts/validate_public_index.py`。
4. 執行 `python scripts/generate_sample_charts.py`。
5. 確認 `data/raw/`、`data/private/`、`data/intermediate/` 不存在或未被 commit。
6. 搜尋 private account details、email、真名、住址、學校、私人帳號等字串。
7. 確認 README 沒有暗示這是個人追蹤資料庫。
8. 確認 `docs/site-integration.md` 仍把順揚宮網站定位為展示端。
9. 確認 `docs/provenance-log.md` 已標記公開衍生資料來源流程，且沒有暴露私有路徑或原始資料檔名。
10. 確認 `docs/product-scope.md` 與本次新增資料產品一致。

## 建立 GitHub repo 後

1. 新增 remote。
2. push `main`。
3. 檢查 GitHub Actions 是否通過。
4. 在 repo description 使用 privacy-conscious / aggregate / data visualization 相關用語。
5. 不要把原始 tracking data 上傳到 GitHub。

## 預期網站消費入口

順揚宮網站之後可優先讀：

- `data/derived/public-index.json`
- `data/derived/*.csv`
- `charts/exports/*.svg`
