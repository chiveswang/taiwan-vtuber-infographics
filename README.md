# Taiwan VTuber Tracking Data Index

這個資料夾整理 TaiwanVtuberData 的兩個資料來源，供本機用 SQL 查詢，不把大型 CSV 歷史資料整批載入對話上下文。

## 資料來源

- `archive/`: `TaiwanVtuberData/TaiwanVTuberTrackingDataArchive`
- `current/`: `TaiwanVtuberData/TaiwanVtuberTrackingData`

兩個資料夾是本機 clone，已由 `.gitignore` 排除，不納入這個工作樹的版本控制。

## 主要檔案

- `build_index.py`: 重建 `vtuber_index.sqlite`
- `query_examples.sql`: 常用 SQL 範例
- `vtuber_index.sqlite`: 本機 SQLite 索引，已忽略不提交
- `HANDOFF.md`: 這次整理與目前索引狀態

## 重建索引

```powershell
cd "E:\VT計畫\資料分析\TaiwanVTuberTrackingDataIndex"
python build_index.py
```

預設行為：

- Archive repo 只建立完整檔案與快照時間索引。
- Current repo 匯入追蹤名單、排除名單、schema 樣本、每種 CSV 的最新快照。

若需要讀 Archive CSV 內容，先限定月份與類型再擴充腳本；不要直接全量匯入。`--archive-content` 只適合有明確需求且可接受大量下載時使用。

## 查詢

```powershell
Get-Content -Raw query_examples.sql | sqlite3 -header -column vtuber_index.sqlite
```

快速查最新訂閱排名：

```powershell
sqlite3 -header -column vtuber_index.sqlite "SELECT t.display_name, b.youtube_subscriber_count, b.youtube_view_count, b.twitch_follower_count FROM v_track_list t JOIN v_latest_basic_data b ON b.repo=t.repo AND b.vtuber_id=t.id WHERE t.repo='current' ORDER BY COALESCE(b.youtube_subscriber_count,0) DESC LIMIT 20;"
```
