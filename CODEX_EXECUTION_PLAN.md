# Codex 執行清單（縱貫分析後續）

狀態：✅ 完成　⬜ 未開始。共用 `build_longitudinal.py` / `build_locate_directory.py` / `build_full_dashboard.py`，**改動請合併、勿互相覆蓋**。
最後更新：2026-06-07（S4、Twitch 雙棲、探索分頁完成）

---

## ✅ 已完成
- **YT 縱貫第一版**（`LONGITUDINAL_TASK_FOR_CODEX.md`）：`build_longitudinal.py` + growth/events/streaming.json + 「成長與生命週期」分頁。
- **作息資料修正**（`STREAMS_S1_FIX_TASK_FOR_CODEX.md`）：清掉 1970 epoch/空值/未來排程台；新增 `min_age_h < 24h` 排除長掛待機室；星期文案改「未取樣日是低估」；by_month client-side 截到載入當月、最新月標「進行中」。快取每 100 檔落盤可續跑。
- **連結對比**（`UI_LINK_CONTRAST_FIX.md`）：全域連結改亮藍含 `:visited`。
- **作息抽取 S1→S2**：已跑到 `sun,thu,tue,sat`。
  - 驗證 OK：YT 清洗後 206,896 場（過濾待機室 68,702＝raw 24%）、hour8 假峰 8049→97、尖峰 20 時、月份 2022-06→2026-06；未取樣日（一/三/五）已從上萬塌到數百＝外溢消失。TW 1,790 場、尖峰 21 時，同樣乾淨。
- **作息補完 S3→S4**（`LONGITUDINAL_STREAMS_STAGED_TASK_FOR_CODEX.md`）：已跑 `--streams-weekdays all`，完成 7/7 日級覆蓋。
  - 驗證 OK：YT 1,460 snapshots，清洗後 362,009 場；TW 1,072 snapshots，清洗後 1,851 場；`streaming.json` 已含 `yt/tw` 與完整 coverage。
- **定位升級 + 同類型排名**（`LOCATE_TYPE_TASK_FOR_CODEX.md` + `LOCATE_UPGRADE_TASK_FOR_CODEX.md`）：已合併定位函式。
  - 思路B 可選團體/個人；KPI 與分組百分位新增同類型；體檢卡含健康總分、8 軸雷達、成長/生命週期/里程碑、相似頻道、作息/事件一句話。
  - 已修黏著度 `r=0` 判斷：0 近期觀看視為有效資料，黏著度百分位採嚴格「贏過」口徑，0 會顯示 0.0%。
- **Twitch 縱貫 + 雙棲比較**（`LONGITUDINAL_TWITCH_TASK_FOR_CODEX.md`）：已完成。
  - `growth.json` 新增 `series_tw/tw_now/tw_cagr_yr/tw_mom_3m/tw_peak/tw_drawdown`；新增 `crossplatform.json`；`s_growth` 新增「雙棲比較」，軌跡圖改 YT/Twitch 雙軸並標註不可直接比絕對量。
- **探索與報告分頁**（`RANK_TASK_FOR_CODEX.md` + `AGENCY_TASK_FOR_CODEX.md` + `REPORT_TASK_FOR_CODEX.md`）：已完成可用版。
  - 新增 `s_rank` 排行榜、`s_agency` 廠牌生態、`s_report` 產業報告；榜單/表格可點回定位。

---

## ⬜ 待辦

### ①（選配）頭像/縮圖整合
資料已含頭像（YT 2,903 + Twitch 1,658）與影片縮圖（100%）。`build_locate_directory.py` 順手把頭像 URL 存進 DIR（加 `img`），前端在定位/排名/事件卡渲染，配 `loading="lazy"` + 壞圖 fallback。未開工單，需要再寫。

### ② 圖形與直播講解 polish
- 排行榜目前是表格可用版，可再升級橫條榜、雙棲象限、廠牌梯隊圖、報告頁大數字章節卡。
- 報告頁目前是樣板敘事可複製版，可再做直播展示版。

### ③ 資料口徑待確認
- `crossplatform.json` 目前雙棲定義為「YT 有訂閱且 Twitch 有追隨」，本次資料為 1,945 個，與舊工單預估 1,525 不同；需確認是否要改成更嚴格口徑。
- `s_rank` 的熱門影片榜目前依 `DIR.tv`，若定位資料沒有重生 FAQ v2 欄位會顯示待資料；目前已可用但仍需抽查前端是否符合展示需求。

---

## 共通守則
- 充分利用現有資料：檔案清單查 `vtuber_index.sqlite` files 表、沿用既有日級訂閱快取、能不重抽就不重抽。
- 所有 JSON **內嵌**進 HTML（本機 `file://` 自用，不可 fetch）。公開部署已**暫緩**，維持內嵌。
- proxy/毛估（黏著度、事件 delta）標限制；倖存者偏差、開台≠同接的警語延續。
- 重用既有 `findChannel/arrs/pctile/opts/seg/fmt` 與既有讀檔/正規化函式，勿重造輪子。

---

## 另一條獨立路線（非本清單依賴）
- `FAQ_TASK_FOR_CODEX.md`：常見問題分頁（以欄位為本、大多綠燈），可獨立排程。
