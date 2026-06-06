# 工單：開台作息——串流改「星期分段累進抽取」（修正 A + 啟動 Twitch 作息 B）

> 修正 YT 作息的月抽失真（A），同時用同一機制做 Twitch 作息（B）。
> 只改 `build_longitudinal.py` 的 **Pass B 串流抽取**；訂閱面板、growth.json、events 的 top-videos 月抽**都不動**。

## 核心問題回顧
`livestreams` / `twitch-livestreams` snapshot 抓的是「**當下正在開的台**」（ephemeral）。原本只取每月最後一份 → 開台時段直方圖被 snapshot 時點系統性帶偏、且嚴重低估。改成**較密的星期抽樣**才準。

## 關鍵設計：累進、去重、可續跑（讓分段補完成立）
- 串流以 **URL 去重**累加 → 每次多抽幾個「星期幾」只會**新增**唯一場次，單調改善。
- 抽取快取改成**累加式**：
  ```jsonc
  // outputs/longitudinal/streams_raw.json（YT）與 twitch_streams_raw.json（TW）
  { "processed_paths":[ ... 已讀過的 snapshot path ... ],
    "streams": { "<url>": {"vid":..,"title":..,"publish_time":..,"view":..} } }
  ```
- 每次執行：算出本階段目標 snapshot（見下），**跳過 processed_paths 已有的**，只讀新檔，merge 進 `streams`，更新 `processed_paths`。→ 分段補完時每段只讀增量。
- 讀完後**每次都重生** `streaming.json`（YT 的 `yt` 區塊 + TW 的 `tw` 區塊）。

## 目標 snapshot 選取
1. 檔案清單**直接查 `vtuber_index.sqlite` files 表**（`kind in ('livestreams','twitch-livestreams')`，已含 `snapshot_at`），不走 git tree。
2. 依 `date(snapshot_at)` 每日取最後一筆為「該日代表 snapshot」。
3. 依該日期的**星期幾**過濾，星期集合由 CLI 控制：
   ```
   python build_longitudinal.py --streams-weekdays sun,thu        # 階段 S1
   ```
   星期值：`mon,tue,wed,thu,fri,sat,sun`；`all`=全 7 天（=完整日級）。
4. **YT 與 Twitch 同步套用**同一星期集合（兩種 kind 各自累加各自的快取）。

## 分段排程（每段只讀增量）
| 階段 | `--streams-weekdays` | 新增星期 | 覆蓋 |
|---|---|---|---|
| S1 | `sun,thu` | 日、四 | 2/7（先上線，時段圖可用） |
| S2 | `sun,thu,tue,sat` | +二、六 | 4/7 |
| S3 | `sun,thu,tue,sat,mon,fri` | +一、五 | 6/7 |
| S4 | `all` | +三 | 7/7＝完整日級 |

> 因為累加去重，S2–S4 只會讀「新星期」的 snapshot；先前已讀的不重讀。隨階段推進，`streaming.json` 自動越來越完整，dashboard 不必改。

## streaming.json 輸出（含覆蓋度標記）
維持既有結構，但每個區塊加 `coverage` 供 dashboard 顯示：
```jsonc
{
  "yt": { "channels":{...}, "industry":{...},
          "coverage":{"weekdays":["sun","thu"],"n_snapshots":int,"n_streams":int} },
  "tw": { "channels":{...}, "industry":{...},
          "coverage":{"weekdays":[...],"n_snapshots":int,"n_streams":int} }
}
```
- per-channel：`hours`(24)、`weekday`(7)、`n_streams`、`first/last`、`active_weeks`、`gap_max_days`、`peak_hour/peak_weekday`。
- industry：`hours`(24)、`weekday`(7)、`by_month`(每月開台數)。
- `publish_time` UTC → **台灣時間 +8** 再取 hour/weekday/月份。

## dashboard（`gw_sched` 作息子視圖）警語隨覆蓋度更新
- 顯示目前覆蓋星期（讀 `coverage.weekdays`）：例「目前樣本：週日、週四（分段補完中）」。
- **時段(hours) 圖**：S1 起就可看（已涵蓋各小時）。
- **星期(weekday) 圖**：標明「未覆蓋的星期為 0，待補完」——覆蓋未滿 7 天時加灰底/註記，避免誤讀成「那天不開台」。
- 維持既有澄清：**開台時間 ≠ 觀看尖峰**（無同接）；Twitch 自 2023-07 起。

## 本次先做
**階段 S1（`--streams-weekdays sun,thu`），YT + Twitch 同時**。產出 `streaming.json` 含 yt/tw 兩區塊與 coverage。之後 S2→S4 由你逐步觸發。

## 驗收（S1）
- [ ] `streams_raw.json` / `twitch_streams_raw.json` 為累加式，含 `processed_paths`；重跑同星期集合不重讀（秒回）。
- [ ] `--streams-weekdays sun,thu` 只讀週日/週四的代表 snapshot；YT 與 TW 各自產出。
- [ ] `streaming.json` 有 `yt`/`tw` 兩區塊 + 各自 `coverage.weekdays=["sun","thu"]`。
- [ ] `gw_sched` 顯示覆蓋星期與「分段補完中」字樣；星期圖標註未覆蓋日；時段圖（台灣時間）合理。
- [ ] 抽一個已知頻道核對：開台時段非空且分布合理；twitch 區塊有值（雙棲頻道）。
- [ ] 訂閱面板 / growth.json / events 未受影響。

## 後續階段（同工單，只換參數）
- S2：`--streams-weekdays sun,thu,tue,sat`
- S3：`--streams-weekdays sun,thu,tue,sat,mon,fri`
- S4：`--streams-weekdays all`
每段跑完重生 `streaming.json`，dashboard 覆蓋字樣自動更新。

> 註：此工單已涵蓋 `LONGITUDINAL_TWITCH_TASK_FOR_CODEX.md` 的 Twitch 作息（Pass B-tw）部分——Twitch 那份剩下的「追隨成長 + 雙棲比較」仍照原工單，但作息改以本工單的分段機制產出，勿重複另做。
