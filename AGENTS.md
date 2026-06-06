# Taiwan VTuber Tracking Data Index - AI Entry

## 工作邊界

這是獨立於 W15 說服談判課程 repo 的資料索引工作樹。不要把這裡的 clone、SQLite 或查詢結果搬回 W15。

## 預設策略

- 不把大型 CSV 歷史資料整批載入對話上下文。
- 優先用 `vtuber_index.sqlite` 與 SQL 查詢。
- `archive/` 與 `current/` 是資料來源 clone，保持本機忽略。
- `build_index.py` 與 SQL/文件才是這個工作樹要版本化的內容。

## 目前索引策略

- Archive repo: 只索引檔案樹與快照時間。
- Current repo: 匯入追蹤名單、排除名單、schema 樣本與最新快照資料。
- 需要歷史趨勢時，先定義 repo、kind、月份區間，再定向匯入，不做全量盲抓。

## 驗證指令

```powershell
sqlite3 -header -column vtuber_index.sqlite "SELECT repo, COUNT(*) AS files, SUM(ext='.csv') AS csv_files FROM files GROUP BY repo; SELECT repo, COUNT(*) AS latest_rows FROM latest_rows GROUP BY repo;"
```

## 注意

- Archive repo 體積很大，避免觸發 `git ls-tree -l` 這類需要 blob size 的操作，部分 clone 會因此大量下載 blob。
- PowerShell 不支援 Unix 風格 `< query.sql` 重導向，請用 `Get-Content -Raw query.sql | sqlite3 ...`。
- 查詢結果只摘要輸出；若需要大表，寫成 CSV 或 SQLite view，不要貼滿對話。
