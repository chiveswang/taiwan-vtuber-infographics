# 工單：縱貫分析（成長軌跡 + 生命週期/存活 + 事件吸粉 + 開台作息）

> 把 dashboard 從「現況快照」升級到「4 年縱貫歷史」。
> 預設範圍：**YouTube 優先**（Twitch 作息留第二版）、**月度精細度**送瀏覽器、**四階段交付**。
> 第一版仍**不涵蓋** SC 金流、即時同接、互動率、剪輯頻道——這些天花板不變，請勿假裝能算。

## 交付物
1. 新腳本 `build_longitudinal.py`：兩次離線抽取 + 三組分析 → 三份 JSON（第 1 部分）。
2. `build_full_dashboard.py`：新增分頁「成長與生命週期」`s_growth`，內含 4 個子視圖（第 2 部分）。
3. `.gitignore`：忽略中間快取（`outputs/longitudinal/`）。

## 執行順序
```
python build_longitudinal.py        # 階段 0：產出三份 JSON（可 --rebuild 強制重抽）
python build_full_dashboard.py      # 階段 1–3：讀 JSON 渲染
```

## 四階段（各自可驗收）
- **階段 0**：`build_longitudinal.py` 抽取 + 三份 JSON（先不接 UI，先驗資料對）。
- **階段 1**：成長軌跡視圖 + 典型生命週期曲線。
- **階段 2**：存活分析 + 事件吸粉。
- **階段 3**：開台作息。

---

# 第 1 部分：`build_longitudinal.py`（階段 0）

## 1.0 共用基礎（重用既有寫法）
- 讀檔清單**直接查 `vtuber_index.sqlite` 的 `files` 表**（已含兩 repo 所有 snapshot 的 `repo, path, kind, snapshot_at`），不必重走 git tree。
- 讀單檔內容：`git -C <repo_path> show HEAD:<path>`（同 `build_locate_directory.py` 的 `show()`）。
- header 正規化 `nh()`、數字轉換 `ii()`、`median()/pctl()`：複製自 `build_locate_directory.py` / `analyze_quarterly_full.py`。
- 兩 repo 路徑：`archive/`、`current/`。
- 輸出最終 JSON 到 `outputs/activity/`（與現有 JSON 同目錄，供 dashboard 內嵌）。中間快取放 `outputs/longitudinal/`（gitignore）。

## 1.1 Pass A — 每日訂閱面板（給軌跡/生命週期/存活/事件）
1. 從 `files` 取 `kind='basic-data'` 的所有 snapshot，依 `date(snapshot_at)` 分組，**每日取最後一筆**（current 與 archive 合併；同日兩 repo 都有時取 current）。預估 ~1,600 個日檔。
2. 逐檔讀 → 取每列 `VTuber ID`、`YouTube Subscriber Count`(用 `ii`)、`YouTube View Count`。累積成 `panel[vid] = {date: subs}`（views 可一併存供延伸）。
3. **schema 穩定**：basic-data 四年欄位不變，無需處理漂移。空值/0 存 `null`。
4. **可續跑**：把 panel 寫成中間快取 `outputs/longitudinal/panel_daily.json`（或 csv）。再次執行若快取存在則直接讀，`--rebuild` 才重抽。

> 記憶體：~4500 頻道 × ~1600 天用 dict 巢狀即可（數百 MB）。若吃緊，分批寫快取。

## 1.2 Pass B — 直播/影片事件（給事件/作息）
1. 從 `files` 取 `kind in ('livestreams','top-videos')` 的 snapshot，**每日取最後一筆**（YT 優先；twitch-livestreams 第一版不做）。
2. 逐檔讀，收集每列 `VTuber ID, Title, Publish Time, URL`(top-videos 另有 `View Count`)。
3. **用 `URL` 去重**（同一場直播/影片會出現在多份 snapshot）→ 得到唯一事件集：每筆 `{vid, title, publish_time, url, view?}`。
4. `publish_time` 為 UTC ISO（`2026-06-06T12:00:00Z`）→ 轉**台灣時間 +8** 後取 hour / weekday / 月份。
5. 中間快取 `outputs/longitudinal/events_raw.json`，同樣可續跑。

## 1.3 分析與輸出

### 輸出 A：`growth.json`（軌跡 + 生命週期）
```jsonc
{
  "generated_at": "...",
  "resolution": "monthly",
  "months": ["2022-03", "...", "2026-06"],     // 全域月份軸
  "channels": {
    "<vid>": {
      "n": "...", "nat":"TW", "g":1, "gn":"團體名", "d":"2022-05-01",
      "grad":"", "ac":"Active",
      "series": [int|null, ...],   // 對齊 months[]；每月取該月最後一個日值
      "subs_now": int, "peak": int, "peak_m": "2025-09",
      "cagr_yr": float,            // (last/first)^(12/月數)-1
      "mom_3m": float,             // 近 3 月成長率
      "drawdown": float            // (peak-now)/peak，衰退指標
    }
  },
  "lifecycle": {                   // 典型生命週期（按出道後月數對齊）
    "x": [0,1,2,...,48],
    "median": [...], "p25":[...], "p75":[...],
    "n_by_x": [...]                // 每個 x 的樣本數（樣本太少的尾段標註）
  }
}
```
- **精細度/體積控管**：`series` 只對「有訂閱且 ≥6 個月歷史」的頻道輸出；其餘只給摘要欄位（省體積）。整體目標 ≤ ~2MB（現有 locate json 442KB，可接受內嵌）。JSON 用緊湊 `separators`。
- lifecycle：所有有 `debut` 的頻道，把每個觀測點換算「出道後第幾個月」，同 x 聚合 median/p25/p75；x 上限取 48 或樣本足夠的範圍。

### 輸出 B：`events.json`（事件吸粉）
```jsonc
{
  "generated_at":"...",
  "channels": {
    "<vid>": { "events":[
      {"type":"3d","date":"2024-05-01","title":"...","url":"...",
       "before":int,"after":int,"delta":int,"delta_pct":float}
    ]}
  },
  "by_type": { "3d":{"n":int,"median_delta":int,"median_delta_pct":float}, "anniversary":{...}, ... }
}
```
- **事件偵測**（掃 Pass B 唯一標題）關鍵字：
  ```
  debut:["初配信","初配","出道配信","debut"]
  3d:["3d","3D披露","3d披露","3d お披露目"]
  anniversary:["周年","週年","anniversary","1st","2nd","3rd"]
  birthday:["生日","生誕","誕生日","birthday"]
  outfit:["新衣装","新衣裝","new outfit","お披露目"]
  ```
  同一頻道同 type 在 ±3 天內視為同一事件（去重，取觀看最高那筆代表）。
- **前後訂閱差**：用 Pass A 日面板。`before` = 事件日前 1 天（或最近的前一個日值）；`after` = 事件日後 **14 天**（或最近後值）。`delta=after-before`，`delta_pct=delta/before`。資料邊界外取不到則該事件 `delta=null`。
- `by_type`：對各 type 的非 null delta 取中位數。
- **警語欄位**：在 dashboard 標明「delta 未扣除自然成長，為毛估；事件靠標題比對有雜訊」。

### 輸出 C：`streaming.json`（開台作息，YT）
```jsonc
{
  "generated_at":"...",
  "channels": {
    "<vid>": {
      "hours":[24 個 int],          // 開台時戳 hour 直方圖（台灣時間）
      "weekday":[7 個 int],         // 週一..週日
      "n_streams":int,
      "first":"YYYY-MM-DD","last":"YYYY-MM-DD",
      "active_weeks":int,"gap_max_days":int,   // 頻率 / 最長斷更
      "peak_hour":int,"peak_weekday":int
    }
  },
  "industry": {
    "hours":[24],"weekday":[7],
    "by_month":{"2022-06":int,...},            // 每月開台總數（季節性）
    "hour_by_weekday":[[7][24]]                // 熱圖（選配）
  }
}
```
- 來源 = Pass B 的唯一直播事件（`livestreams`）。`top-videos` 不計入作息（那是熱門影片，非開台）。
- `gap_max_days` = 相鄰兩場直播日期最大間隔；`active_weeks` = 有開台的不重複週數。

---

# 第 2 部分：dashboard 分頁「成長與生命週期」

## 2.0 接點
1. `build_full_dashboard.py` 頂部新增讀檔：`GROW=...growth.json`、`EVT=...events.json`、`STM=...streaming.json`，比照 `__ACT__` 用佔位字串內嵌（**必須內嵌，不可 fetch**——dashboard 走 `file://`，fetch 會被擋）。
2. **TABS** 末尾加 `,["s_growth","成長與生命週期",buildGrowth]`。
3. HTML body 新增 `<section id="s_growth">`，內含**子視圖切換**（4 顆按鈕）+ 4 個子容器。
4. 新增 `function buildGrowth(inclP){…}`。

## 2.1 子視圖結構（單一 section + 內部子 tab）
```html
<section id="s_growth">
  <div class="locbar"><div><b>選一個頻道看它的軌跡（沿用名單）</b><br>
    <input id="gwQ" list="gwList" placeholder="頻道名稱 / UCxxxx"><datalist id="gwList"></datalist>
    <button id="gwFind">套用</button><button id="gwClear" style="background:#2a2f3d">清除</button>
    <div id="gwStatus" class="muted" style="margin-top:6px"></div></div></div>
  <div class="tabs" id="gwSub"></div>   <!-- 4 顆子 tab：軌跡/生命週期/事件/作息 -->
  <div id="gw_traj"></div>
  <div id="gw_life"></div>
  <div id="gw_event"></div>
  <div id="gw_sched"></div>
</section>
```
- 子 tab：`[["gw_traj","成長軌跡"],["gw_life","生命週期&存活"],["gw_event","事件吸粉"],["gw_sched","開台作息"]]`，點擊切換顯示對應容器（同 `.tab.on` 樣式）。
- 頻道選擇器：重用既有 `findChannel`（回傳含 vid 的物件——注意 `DIR.channels` 目前無 vid 欄位；**請在 `build_locate_directory.py` 為每頻道補 `id` 欄位**，或在 growth.json 用 name/y 對應。建議補 `id` 最乾淨）。選定後存 `gwChannel`，各子視圖以它疊圖。

> ⚠ 前置：`findChannel` 目前用 name/UC/twitch 比對，但 `growth/events/streaming` 用 `vid` 當 key。請在 `build_locate_directory.py` 的 channel 物件加上 `"id": vid`，讓前端能由選到的頻道拿到 vid 去查三份 JSON。

## 2.2 各子視圖內容（重用 `opts()/seg()/fmt/Chart`）

### 軌跡 `gw_traj`　🟢
- KPI：`subs_now`、`cagr_yr`（年化成長%）、`mom_3m`（近3月動能%）、`drawdown`（距高點回落%）。未選頻道時顯示產業層級（如成長最快 Top 5 清單）。
- 主圖：選定頻道 `series` 折線；疊上**同屆出道中位線**與**全體中位線**（同 months 軸）。
- 警語：早期月份樣本稀疏。

### 生命週期&存活 `gw_life`　🟢
- 圖1 生命週期曲線：x=出道後月數，畫 `lifecycle.median` + p25/p75 帶狀；選定頻道按其 `debut` 對齊疊上去 → 一眼看出「比典型台 V 快還慢」。
- 圖2 存活曲線：用 `growth.json` 的 `d/grad/ac` 在前端算**Kaplan–Meier 近似**——事件=有 `grad` 且 `ac==='Graduated'`，存活時間=debut→grad 月數；右設限=Active（debut→最後資料）。可再拆「團體 vs 個人」「各出道屆」兩條對照。
- 圖3（選配）危險率：各「出道後月數」區間的畢業比例。
- **警語（醒目）**：track-list 為現存記載，**含倖存者偏差**，存活率偏樂觀。

### 事件吸粉 `gw_event`　🟡
- 產業圖：`by_type` 各事件類型的**訂閱淨增中位數**長條（3D / 周年 / 生日 / 初配信 / 新衣裝）——這就是「吸粉密碼」的數據版。
- 選定頻道：列出該頻道 `events` 表（type / 日期 / 標題連結 / delta / delta%）。
- **警語**：delta 為事件後 14 天毛估、未扣自然成長；事件靠標題比對，有漏判誤判，需人工查核。

### 開台作息 `gw_sched`　🟢
- 圖1 開台時段：選定頻道 `hours`(24) 長條 vs 產業 `industry.hours`（正規化%對照），台灣時間；標出 `peak_hour`。
- 圖2 星期分布：`weekday`(7)。
- 圖3 季節性：`industry.by_month` 折線（每月開台總數）。
- KPI：開台場數、最長斷更天數、活躍週數。
- **澄清**：這是「**開台時間**」分布，非「觀看人數最多的時段」——沒有同接資料，無法做觀眾權重。

---

# 第 3 部分：.gitignore
加入：
```
outputs/longitudinal/
```
（中間快取 `panel_daily.json`、`events_raw.json` 不入版控；最終三份 JSON 在 `outputs/activity/`，依現有 `.gitignore` 規則處理。）

---

# 第 4 部分：驗收清單

**階段 0**
- [ ] `build_longitudinal.py` 跑完產出 `growth.json / events.json / streaming.json`，可 `--rebuild`、可續跑（快取存在則跳過抽取）。
- [ ] 抽一個已知頻道，人工核對：月度訂閱序列遞增合理；某 3D/周年事件的 before/after 抓得到；開台時段直方圖非空。
- [ ] `growth.json` ≤ ~2MB（series 僅輸出 ≥6 月歷史的頻道）。

**階段 1**
- [ ] 「成長與生命週期」分頁出現，子 tab 可切換；選頻道後軌跡圖疊同屆/全體中位線；KPI 正確。
- [ ] 生命週期曲線顯示 median/p25/p75，選定頻道按出道對齊疊上。

**階段 2**
- [ ] 存活曲線正確（事件=畢業、設限=Active），可拆團體/個人；醒目標註倖存者偏差。
- [ ] 事件吸粉產業長條 + 選定頻道事件表（連結可點）；標註 delta 為毛估。

**階段 3**
- [ ] 開台時段/星期/季節性三圖；台灣時間；明確澄清「開台時間≠觀看尖峰」。

**通用**
- [ ] 三份 JSON 內嵌（非 fetch），`file://` 開啟無 CORS 問題、無 console error。
- [ ] `build_locate_directory.py` 已為每頻道補 `id` 欄位，前端能由選定頻道查三份 JSON。
- [ ] 重用既有 `findChannel/opts/seg/fmt/Chart` 與既有讀檔/正規化函式，未重造輪子。

> 設計叮囑：proxy 與毛估（黏著度、事件 delta）一律標註限制；倖存者偏差務必醒目。能做的做到位，做不到的（SC/同接/互動率/剪輯）維持誠實，不要硬湊。
