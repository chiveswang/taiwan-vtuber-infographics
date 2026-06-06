# 工單：縱貫分析・Twitch 與雙棲比較（YT 工單的下一階段）

> 這是 `LONGITUDINAL_TASK_FOR_CODEX.md`（YouTube 優先版）的**延伸**。
> **前置**：YT 那份工單的 `build_longitudinal.py` 與 `s_growth` 分頁要先落地，本工單在其上擴充——**請複用同一支腳本、同一個分頁**，不要另開。
> 主打：**雙棲比較**（1,525 個頻道同時有 YT 訂閱 + Twitch 追隨）。其餘是把成長/作息補上 Twitch 面。

## 為什麼這階段值得做（數據佐證）
- **雙棲 1,525 個頻道**：同時有 YT 訂閱與 Twitch 追隨 → 跨平台比較有厚實樣本。
- Twitch 追隨來自 basic-data（**Pass A 已在讀那些日檔**，只要多存一個欄位，零額外抓取）。
- twitch-livestreams 降頻到每日 **~1,072 個日檔**（資料 2023-07 起），作息分析可行。
- record 另有 Twitch 近期中位/最高觀看（906 個頻道有值），供熱度對照。

## 誠實的 Twitch 限制（務必標註）
- **Twitch 追隨 ≠ YouTube 訂閱**：追隨是更廉價的訊號，**絕對數不可直接相比**——跨平台一律用**平台內百分位**或**各自成長率**比較，不要把 follower 和 subscriber 畫在同一條絕對量軸上做高低判斷。
- Twitch 直播資料**只回溯到 2023-07**，比 YT 短 → 跨平台時序對齊時，Twitch 線較晚開始。
- Twitch 的 view 欄位語意不確定（VOD 觀看或別的），**不當同接用**。
- **不做 Twitch 事件研究**：3D/初配信/周年是 YouTube 中心的活動，Twitch 標題少見且雜，第一版略過（誠實標示「事件吸粉僅 YouTube」）。

---

# 第 1 部分：擴充 `build_longitudinal.py`（階段 T0）

## 1.1 Twitch 追隨面板（併入 Pass A，零額外抓取）
Pass A 逐日讀 basic-data 時，**多存 `Twitch Follower Count`**（用 `ii`）。每頻道得到 `tw_panel[vid]={date: followers}`。空值/0 存 `null`。

## 1.2 Twitch 開台事件（新增 Pass B-tw）
> ⚠ 已改由 `LONGITUDINAL_STREAMS_STAGED_TASK_FOR_CODEX.md` 的「星期分段累進抽取」統一處理（YT+TW 同機制）。**本節僅供背景說明，實作以該分段工單為準，勿重複另做。** 下方為原始描述。
1. 從 `files` 取 `kind='twitch-livestreams'`，依 `date(snapshot_at)` **每日取最後一筆**（~1,072 日檔）。
2. 逐檔讀 `VTuber ID, Title, Publish Time, URL`；**用 URL 去重**得唯一開台事件。
3. `Publish Time` 同為 UTC ISO（已驗：`2026-06-06T04:03:57Z`）→ 轉**台灣時間 +8**。
4. 中間快取 `outputs/longitudinal/twitch_streams_raw.json`，可續跑。

## 1.3 輸出（擴充既有 JSON + 一份新檔）

### 擴充 `growth.json`：每頻道加 Twitch 欄位
```jsonc
"<vid>": {
  // ...既有 YT 欄位...
  "series_tw":[int|null,...],   // 對齊 months[]，Twitch 追隨月度（每月最後日值）
  "tw_now":int, "tw_cagr_yr":float, "tw_mom_3m":float,
  "tw_peak":int, "tw_drawdown":float
}
```
- 體積：`series_tw` 只對「有 Twitch 追隨且 ≥6 月歷史」者輸出；其餘只給摘要。整體仍控 ≤ ~2.5MB。

### 擴充 `streaming.json`：加入 Twitch 區塊
```jsonc
{
  "yt": { /* 原本 YT 的 channels / industry 內容移到這層，或維持原樣並新增 tw 平行區塊 */ },
  "tw": {
    "channels": { "<vid>": {"hours":[24],"weekday":[7],"n_streams":int,
                            "first":"","last":"","active_weeks":int,"gap_max_days":int,
                            "peak_hour":int,"peak_weekday":int} },
    "industry": {"hours":[24],"weekday":[7],"by_month":{"YYYY-MM":int}}
  }
}
```
> 若不想動 YT 既有結構，可改新增獨立檔 `streaming_tw.json`，dashboard 兩邊都讀。擇一，註明即可。

### 新檔 `crossplatform.json`（雙棲比較・本工單主打）
```jsonc
{
  "generated_at":"...",
  "channels": {           // 只收雙棲(兩平台皆有資料)頻道
    "<vid>": {
      "n":"...", "nat":"TW", "d":"出道日",
      "yt_subs":int, "tw_fol":int,
      "yt_pct":float, "tw_pct":float,   // 各自在「該平台全體」的百分位
      "home":"YT"|"TW"|"均衡",          // 由 yt_pct vs tw_pct 判定(差距<10pp 視為均衡)
      "yt_mom":float, "tw_mom":float,   // 近 3 月各平台成長率
      "tilt":"往YT傾斜"|"往Twitch傾斜"|"持平"  // 由 yt_mom vs tw_mom 判定
    }
  },
  "industry": {
    "months":["..."],                   // 對齊 growth.json months
    "active_yt_only":[int,...],         // 各月：僅 YT 活躍頻道數
    "active_tw_only":[int,...],
    "active_dual":[int,...],
    "yt_subs_total":[int,...],          // 月度 YT 訂閱總量
    "tw_fol_total":[int,...],           // 月度 Twitch 追隨總量
    "debut_cohort_platform":{           // 各出道屆的平台選擇(現況快照)
      "2022":{"yt_only":int,"tw_present":int}, "2023":{...}, ...
    }
  }
}
```
- `home`：比 `yt_pct` 與 `tw_pct`（平台內百分位，可比），高者為主場；差距 <10pp 為「均衡」。
- `tilt`：比近 3 月各平台成長率，顯著高的一方為傾斜方向。
- `active_*`：某月「活躍」沿用既有定義（該平台近期有觀看/有追隨資料即可，與 dashboard 既有口徑一致；無法逐月精算時可用追隨/訂閱面板有值近似，並註明）。

---

# 第 2 部分：dashboard（在既有 `s_growth` 分頁擴充）

## 2.1 軌跡子視圖 `gw_traj`：加 Twitch
- 選定頻道時，主圖**雙軸**：左軸 YT 訂閱（`series`）、右軸 Twitch 追隨（`series_tw`），明確標「左右軸不同平台、不可比絕對高低」。
- KPI 加一排 Twitch：`tw_now`、`tw_cagr_yr`、`tw_mom_3m`。

## 2.2 新增子視圖 `gw_cross`「雙棲比較」（主打）
在子 tab 列加 `["gw_cross","雙棲比較"]`。內容：
- **未選頻道（產業）**：
  - 圖1 折線：`active_yt_only / active_tw_only / active_dual` 隨月份 → 平台版圖變化。
  - 圖2 雙軸折線：`yt_subs_total` vs `tw_fol_total`（標註語意不同、僅看趨勢）。
  - 圖3 長條：各出道屆 `debut_cohort_platform`（新世代是否更愛 Twitch）。
- **選定頻道**：KPI 卡——`home`(主場)、`yt_pct`/`tw_pct`（各平台贏過多少%）、`tilt`(正在往哪傾斜)、近 3 月雙平台成長率對照。

## 2.3 作息子視圖 `gw_sched`：加平台切換
- 加一個 YT / Twitch 切換（或並列兩組圖）。Twitch 用 `streaming.json` 的 `tw` 區塊：開台時段(24)、星期(7)、季節性(by_month)。
- 維持澄清：**開台時間 ≠ 觀看尖峰**（無同接）。Twitch 線從 2023-07 起。

## 2.4 讀檔
`build_full_dashboard.py` 內嵌新增的 `crossplatform.json`（與 `streaming_tw.json` 若採獨立檔）。仍**內嵌、不可 fetch**（file://）。

---

# 第 3 部分：驗收清單

**階段 T0**
- [ ] Pass A 多存 Twitch 追隨；新增 Pass B-tw 讀 ~1,072 日檔、URL 去重、轉台灣時間；皆可續跑。
- [ ] `growth.json` 每頻道有 `series_tw` 與 tw 摘要；`streaming` 有 tw 區塊；新檔 `crossplatform.json` 產出。
- [ ] 抽一個已知雙棲頻道人工核對：Twitch 追隨月序合理、開台時段非空、`home/tilt` 判定合理。

**階段 T1**
- [ ] 軌跡圖雙軸顯示 YT 訂閱 + Twitch 追隨，明確標註不可比絕對量。
- [ ] 「雙棲比較」子分頁：產業三圖 + 選定頻道 KPI（主場/百分位/傾斜）正確。

**階段 T2**
- [ ] 作息子視圖可切 YT/Twitch；Twitch 時段/星期/季節性正確；標註 2023-07 起、開台≠觀看尖峰。

**通用**
- [ ] 複用同一支 `build_longitudinal.py` 與同一個 `s_growth` 分頁，未另開重複結構。
- [ ] 跨平台一律用百分位/成長率比較，**未把 follower 與 subscriber 當同量級**。
- [ ] 內嵌（非 fetch），`file://` 無 console error。

> 叮囑：Twitch 追隨與 YT 訂閱語意不同，所有跨平台呈現都要防止「直接比大小」的誤讀；Twitch 事件研究第一版不做並誠實標示；倖存者偏差、開台≠同接的註記延續。
