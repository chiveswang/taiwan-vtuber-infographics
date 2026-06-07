# Refresh Policy

本專案的真實 derived data 來自公開上游 repo，但上游資料可能高頻更新。為了避免 CI 因 live upstream drift 而不穩定，GitHub Actions 只驗證已 commit 的 derived data、public index 與 chart outputs。

## Manual Refresh Flow

更新真實 derived data 時：

1. 執行 `python scripts/generate_real_derived_data.py`。
2. 執行 `python scripts/generate_sample_charts.py`。
3. 執行 `python scripts/validate_public_data.py`。
4. 執行 `python scripts/validate_public_index.py`。
5. 檢查 diff 只包含 aggregate counts、metadata counts、chart outputs 或文件更新。
6. 確認沒有 raw rows、names、IDs、channel IDs、URLs as rows、individual timelines。
7. commit and push。

## Why CI Does Not Fetch Live Upstream

Live upstream refresh can change while a pull request or push workflow is running. This is useful for scheduled data work, but bad for deterministic validation.

If automated refresh is added later, it should be a separate scheduled workflow that opens a pull request rather than mutating validation behavior.
