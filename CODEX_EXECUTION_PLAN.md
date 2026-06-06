# Codex 執行清單（縱貫分析後續）

狀態：✅ 完成　⬜ 未開始。共用 `build_longitudinal.py` / `build_locate_directory.py` / `build_full_dashboard.py`，**改動請合併、勿互相覆蓋**。
最後更新：2026-06-06（S2 完成驗證）

---

## ✅ 已完成
- **YT 縱貫第一版**（`LONGITUDINAL_TASK_FOR_CODEX.md`）：`build_longitudinal.py` + growth/events/streaming.json + 「成長與生命週期」分頁。
- **作息資料修正**（`STREAMS_S1_FIX_TASK_FOR_CODEX.md`）：清掉 1970 epoch/空值/未來排程台；新增 `min_age_h < 24h` 排除長掛待機室；星期文案改「未取樣日是低估」；by_month client-side 截到載入當月、最新月標「進行中」。快取每 100 檔落盤可續跑。
- **連結對比**（`UI_LINK_CONTRAST_FIX.md`）：全域連結改亮藍含 `:visited`。
- **作息抽取 S1→S2**：已跑到 `sun,thu,tue,sat`。
  - 驗證 OK：YT 清洗後 206,896 場（過濾待機室 68,702＝raw 24%）、hour8 假峰 8049→97、尖峰 20 時、月份 2022-06→2026-06；未取樣日（一/三/五）已從上萬塌到數百＝外溢消失。TW 1,790 場、尖峰 21 時，同樣乾淨。

---

## ⬜ 待辦

### ① 作息補完 S3→S4（換參數即可，使用者逐段觸發）
同 `LONGITUDINAL_STREAMS_STAGED_TASK_FOR_CODEX.md`，每段重生 `streaming.json`：
- S3：`--streams-weekdays sun,thu,tue,sat,mon,fri`
- S4：`--streams-weekdays all`（完整日級）
- 預期：週一/三/五會用「真實當日開台」自然長出合理柱子（數千級，非現在的數百）。

### ② 定位你自己・團體勢/個人勢排名（小改，可獨立進行）
工單：`LOCATE_TYPE_TASK_FOR_CODEX.md`
- 只改 `build_full_dashboard.py` 定位函式；DIR 的 `g` 現成。
- KPI 加「團體勢/個人勢中排名」；lc4 加「同類型」百分位；思路B 加團體/個人下拉。
- 企業/社團三分不做（資料無標記），留未來選配。

### ②b 定位升級・頻道體檢卡（與 ② 改同批函式，合併勿覆蓋）
工單：`LOCATE_UPGRADE_TASK_FOR_CODEX.md`
- 串 growth/events/streaming（靠 `id`）：成長動能/生命週期定位/回落/里程碑預測、健康總分(0–100)+雷達擴 8 軸、相似頻道推薦、作息/事件一句話。
- 缺縱貫資料的頻道顯示「資料不足」；思路B 數字模式只顯示橫斷面。

### ③ Twitch 縱貫・剩餘（追隨成長 + 雙棲比較）
工單：`LONGITUDINAL_TWITCH_TASK_FOR_CODEX.md`
- Pass A 多存 Twitch 追隨（零額外抓取）；`growth.json` 加 `series_tw` + tw 摘要。
- 新檔 `crossplatform.json`（雙棲 1,525 頻道：主場/百分位/傾斜 + 產業平台版圖）。
- 軌跡圖加 Twitch 雙軸；新增「雙棲比較」子分頁。
- ⚠ Twitch **作息已在 S1–S2 接走**，本項勿重做；跨平台一律用百分位/成長率，不比 follower vs subscriber 絕對量。

### ④ 新分頁・探索與報告（資料現成、全內嵌，可獨立排程）
- **排行榜 `s_rank`**（`RANK_TASK_FOR_CODEX.md`）：訂閱/成長/黏著/爆紅/吸粉事件/出道黑馬/規律…多榜 + 篩選，點名稱跳定位。熱門影片榜待 FAQ 的 `tv`、雙棲榜待 Twitch 的 crossplatform。
- **廠牌生態 `s_agency`**（`AGENCY_TASK_FOR_CODEX.md`）：勢力排名(總訂閱+每人中位)、團體 vs 個人差異、單一團體梯隊/走勢。client-side 聚合 growth。
- **產業報告 `s_report`**（`REPORT_TASK_FOR_CODEX.md`）：8 節自動敘事 + 複製全文，用 ACT/COH/growth/streaming。

### ⑤（選配）頭像/縮圖整合
資料已含頭像（YT 2,903 + Twitch 1,658）與影片縮圖（100%）。`build_locate_directory.py` 順手把頭像 URL 存進 DIR（加 `img`），前端在定位/排名/事件卡渲染，配 `loading="lazy"` + 壞圖 fallback。未開工單，需要再寫。

---

## 共通守則
- 充分利用現有資料：檔案清單查 `vtuber_index.sqlite` files 表、沿用既有日級訂閱快取、能不重抽就不重抽。
- 所有 JSON **內嵌**進 HTML（本機 `file://` 自用，不可 fetch）。公開部署已**暫緩**，維持內嵌。
- proxy/毛估（黏著度、事件 delta）標限制；倖存者偏差、開台≠同接的警語延續。
- 重用既有 `findChannel/arrs/pctile/opts/seg/fmt` 與既有讀檔/正規化函式，勿重造輪子。

---

## 另一條獨立路線（非本清單依賴）
- `FAQ_TASK_FOR_CODEX.md`：常見問題分頁（以欄位為本、大多綠燈），可獨立排程。
