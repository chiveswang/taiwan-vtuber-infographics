# 工單：S1 作息資料清洗修正（publish_time）

> S1 機制正確（YT 16.5 萬場、晚 8 尖峰；TW 晚 9 尖峰）。只需補一道 publish_time 清洗 + 一處文案修正。

## 問題（僅 YT，TW 乾淨）
1. **空/無效 publish_time → 變 1970-01**：7,274 場。導致時段圖「早上 8 點」假凸起（`1970-01-01T00:00Z`+8=08:00）。
2. **未來排程台**（publish_time > 產生日）：1,086 場（到 2028），尚未開台，不應計入作息。
- 真實資料應為 ~164,967 場、範圍 2022-05→2026-06。

## 修正 1：`build_longitudinal.py` 串流統計前過濾 publish_time
在算 `hours / weekday / by_month / first / last / n_streams` 之前，**丟棄**符合以下任一的串流：
- publish_time 為空、無法解析、或年份 < 2018（含 1970 epoch）。
- publish_time > `generated_at`（或今日）→ 未來排程台。

過濾邏輯建議集中成一個 `valid_publish(dt)` 判斷，YT/TW 共用。重生 `streaming.json`（毋須重抽，直接用既有 `streams_raw.json` / `twitch_streams_raw.json` 快取重算即可）。

驗收：
- [ ] YT `by_month` 範圍變為 ~2022-05→2026-06，無 1970-01、無 >2026-06。
- [ ] YT 時段圖 hour 8 的假凸起消失（從 ~8049 降到 ~800 量級）。
- [ ] `n_streams` 約少 ~8,360（≈4.8%）。

## 修正 3：排除「永久待機室」——「當日新台」過濾（核心）
**問題**：很多頻道開一個長期掛著的 YouTube 待機室（當週表更新處），它會被每份 snapshot 一直撈到。雖然 URL 去重只算一次，但它的 publish_time 是很久以前 → 污染星期/時段分布。**證據**：在只取週日/週四 snapshot 時，星期分布卻出現週五(21,967)、週六(14,888) 等「未取樣日」的大量場次——這些幾乎都是長掛待機室在 Sun/Thu 被撈到、publish 卻在他日。

**過濾規則**：一個串流只在「曾被某份 snapshot 在它 publish 後 **24 小時內**撈到」時才計入作息。
- `age_h = (snapshot_capture_time − publish_time) / 3600`
- 保留條件：該串流所有出現中的 **最小 age_h 落在 `[0, 24)`**（即至少一次是「當日新台」被撈到）。
- 待機室因首次被取樣時已掛多日 → min age ≫ 24h → 剔除。真實開台被撈到時通常 < 數小時 → 保留。馬拉松台 < 24h 也保留。
- 閾值設為可調常數（預設 24h），方便日後微調。

**快取需求**：`streams_raw.json` / `twitch_streams_raw.json` 每筆串流加存 `min_age_h`（讀每份 snapshot 時，用該 snapshot 的 capture 時間更新該 URL 的 min 正值 age）。若現有快取未存，本次重讀一次既有已處理 snapshot 補算即可（檔案清單在 sqlite，量小、快）。
- 之後 S2–S4 累進時，新 snapshot 一併更新 `min_age_h`。

**套用範圍**：`hours / weekday / by_month / n_streams / active_weeks / gap_max_days` 全部以過濾後的串流計算（YT、TW 皆套）。

驗收：
- [ ] 套用後，未取樣星期（如週五/六）的場次大幅下降，星期分布集中回週日/週四（待機室外溢消失）。
- [ ] `by_month` 每月開台數明顯下修且更貼近「真實當日開台」量級。
- [ ] 抽查一個已知長掛待機室 URL：確認被剔除（min age ≫ 24h）。

## 修正 2：`gw_sched` 星期圖文案（觀念，非 bug）
星期分布統計的是串流 **publish_time 的星期**，非 snapshot 星期；跨夜台與鄰近日會外溢，故未取樣的星期**不會是 0、而是被低估**。
- 把原「未覆蓋日標灰/視為 0」的處理改為：
  - 文案：「目前以週日、週四 snapshot 取樣，星期分布偏向這兩日及鄰近日，補完中（讀 `coverage.weekdays`）」。
  - 不要把未取樣星期畫成 0 或灰底「不開台」，以免誤讀；可整張圖加「樣本未滿 7 天」標註。
- 時段圖不受此影響（清洗後即可正常呈現）。

## 修正 4：每月開台數（by_month 季節性圖）截到「載入當天」
**需求**：未來預定台不看（資料層已由修正 1 移除）；圖只呈現到**使用者載入網頁當天**為止。

實作（`build_full_dashboard.py` 的 `gw_sched` 季節性圖 JS，client-side）：
- 取瀏覽器當下月份 `nowMonth`：`new Date()` → `"YYYY-MM"`（瀏覽器 JS 可用 `new Date()`，此限制僅適用於別處的 workflow 腳本，dashboard 不受影響）。
- by_month 只渲染 `key <= nowMonth` 的月份，**丟棄任何未來月份**（防呆，修正 1 後理論上已無）。
- **最新顯示月份標為「進行中」**：該月資料只到今天/產生日，視覺上用虛線或淺色，並標註「（進行中，僅到載入當天）」，沿用既有未結算季的處理風格。
- 同理，其他可能觸及未來的時間軸（成長軌跡 months）也防呆截到 `nowMonth`，避免顯示空的未來點。

驗收：
- [ ] by_month 圖最右端為載入當月，無未來月份；最新月份標為進行中。
- [ ] 換不同日期載入（或改系統時間）時，截斷點隨之改變（client-side 生效）。

## 不動
- 抽取快取、訂閱面板、growth.json、events.json 不動。
- 清洗只影響 `streaming.json` 重算。
