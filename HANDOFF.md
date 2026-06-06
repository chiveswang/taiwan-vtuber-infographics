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
