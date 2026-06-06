# Handoff - 2026-06-06

## 為什麼拆出來

原本為了回應 TaiwanVtuberData 查詢需求，先在 W15 說服談判 repo 下建立了 `.codex-data/taiwan-vtuber`。這份資料和 W15 課程專案無直接關係，而且資料量大，適合獨立工作樹。

已搬到：

```text
E:\VT計畫\資料分析\TaiwanVTuberTrackingDataIndex
```

W15 底下的 `.codex-data` 已移除。

## 已完成

- Clone `TaiwanVtuberData/TaiwanVTuberTrackingDataArchive` 到 `archive/`。
- Clone `TaiwanVtuberData/TaiwanVtuberTrackingData` 到 `current/`。
- 建立 `vtuber_index.sqlite`。
- 建立 `build_index.py`，預設只完整索引 Archive 檔案樹，不讀全量 Archive CSV blob。
- 建立 `query_examples.sql`。

## 目前索引內容

- Archive: 83,322 檔，83,314 個 CSV；快照涵蓋約 2021-02 到 2025-12。
- Current: 13,232 檔，13,226 個 CSV；最新快照到 2026-06-06。
- Current 已匯入 `latest_rows`: 7,471 筆。
- Current 追蹤名單匯入: 4,503 筆 VTuber，另有 10 個 section row。

## 後續建議

下一步若要做歷史分析，不要全量匯入 Archive。先選範圍，例如：

- `record`, `2024-01` 到 `2024-12`
- `top-videos`, 最近 6 個月
- 指定 VTuber ID 的跨期追蹤

再擴充 `build_index.py` 加入範圍參數與專用歷史表。

---

# Handoff Update - 2026-06-07 01:40

## 最新狀態

- 最新 commit: `75cc083 Record closeout verification`
- Dashboard 已可重建：`outputs/activity/vtuber_activity_dashboard.html`（ignored）。
- 直播簡報初稿已可重建：`outputs/activity/taiwan-vtuber-live-briefing.pptx`（ignored）。
- 大型資料仍只留本機 ignored：`archive/`, `current/`, `outputs/`, `quarterly_samples/`, `vtuber_index.sqlite`。

## 今日新增重點

- `build_longitudinal.py` 已完成 S4 7/7 作息補完、Twitch 縱貫、雙棲比較資料。
- `build_locate_directory.py` 已加入頭像 URL 欄位 `img`。
- `build_full_dashboard.py` 已加入/強化：
  - `s_rank` 排行榜與橫條榜。
  - `s_agency` 廠牌生態與廠牌梯隊圖。
  - `s_report` 大數字卡與逐章講稿卡。
  - `s_growth` Twitch 軌跡、雙棲象限、作息分頁。
  - `s_locate` 體檢卡、相似頻道、團體/個人排名、黏著度 `r=0` 修正。
- `build_presentation_deck.mjs` 可從現有 generated JSON 產出 10 頁直播 PPTX 初稿。

## 可重跑指令

```powershell
python build_full_dashboard.py
& 'C:\Users\sweet\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' build_presentation_deck.mjs
```

基本驗證：

```powershell
sqlite3 -header -column vtuber_index.sqlite "SELECT repo, COUNT(*) AS files, SUM(ext='.csv') AS csv_files FROM files GROUP BY repo; SELECT repo, COUNT(*) AS latest_rows FROM latest_rows GROUP BY repo;"
```

## 已知待確認

- `crossplatform.json` 目前雙棲定義為「YT 有訂閱且 Twitch 有追隨」，數量 1,945；若要公開使用，需確認是否改成更嚴格定義。
- 簡報目前是可編輯初稿，仍可做正式視覺設計、截圖型圖表與逐頁版面 refinement。
- 本資料源沒有 SC 金流、真實同接、留言/按讚互動率；直播講解需保留 proxy 警語。

## 收工檢查摘要

- SQLite baseline 可查：archive 83,322 files / current 13,232 files / current latest_rows 7,471。
- Dashboard JS parse OK，關鍵 marker 已嵌入：`rankBar`, `gwX4`, `agTier`, `story-grid`, `chapter-grid`。
- PPTX artifact-tool 匯入 OK：10 slides。
- `git ls-files` 未追蹤大型資料、SQLite、PPTX 或 outputs。
- 敏感字樣掃描無命中。
