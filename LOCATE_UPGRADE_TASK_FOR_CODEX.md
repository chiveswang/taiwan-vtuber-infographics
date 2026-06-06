# 工單：「定位你自己」升級為「頻道體檢卡」

> 把定位從「單一快照的排名器」升級成一頁體檢卡：除了現有橫斷面排名，加入**成長動能、生命週期定位、健康總分、相似頻道推薦、作息/事件一句話**。
> 只改 `build_full_dashboard.py`（定位相關函式）。資料已就緒，靠 `id` 串接縱貫三份 JSON。
> 與 `LOCATE_TYPE_TASK_FOR_CODEX.md`（同類型排名）改同一批函式 → **改動合併、勿覆蓋**。

## 資料來源（皆已存在，用 DIR 的 `id` join）
- `DIR.channels[]`：`id, s, v, f, r, rh, nat, g, d`（+ LOCATE_TYPE 後的同類型）。
- `growth.channels[id]`：`subs_now, peak, peak_m, cagr_yr, mom_3m, drawdown, series, d, ac`；另 `growth.lifecycle{x,median,p25,p75,n_by_x}`。
- `events.channels[id].events[]`：`{type,date,title,url,before,after,delta,delta_pct}`。
- `streaming.yt.channels[id]`：`{hours[24],weekday[7],n_streams,first,last,active_weeks,gap_max_days,peak_hour,peak_weekday}`；`streaming.yt.coverage`。
- join 覆蓋率：growth 2,930 / events 1,229 / streaming 2,856（共 3,033）。缺資料的頻道，對應區塊顯示「資料不足」不報錯。

## 前置：建立縱貫百分位陣列
新功能要算「動能贏過幾%」「規律贏過幾%」，需先把這些指標收成排序陣列（類似既有 `arrs()`，但來源是 growth/streaming）：
```
LON = {
  mom:   排序(所有 growth.channels[*].mom_3m，排除 null),
  cagr:  排序(cagr_yr),
  reg:   排序(各頻道「開台規律」值，定義見下),
}
```
- **開台規律 regularity**：`active_weeks / 跨距週數`（跨距 = first→last 的週數，至少 1）。值越高越規律。只對 streaming 有資料者計算。

## 新增/改動內容

### A. 成長維度 KPI（加入 `kpi_loc`，限頻道查詢且有 growth 者）
- **成長動能**：`「近 3 月 {mom_3m>=0?'+':''}{(mom_3m*100).toFixed(1)}%・動能贏過 {pctile(LON.mom,mom_3m)}%」`
- **年化成長**：`cagr_yr` 顯示百分比（可附 `pctile(LON.cagr,…)`）。
- **距高點回落**：`「−{(drawdown*100).toFixed(1)}%」`（drawdown 大時用紅色 `.down`）。
- **生命週期定位**：
  - `m = 出道(d)→最新月份 的月數`；取 `lifecycle.x` 最接近 m 的索引 i。
  - 比 `subs_now` 與 `lifecycle.median[i]`：輸出「出道 {m} 個月，{subs_now>median?'領先':'落後'}典型台V（你 {fmt(subs_now)} / 中位 {fmt(median)}）」。
  - `n_by_x[i]` 太小（如 <20）時加註「同期樣本少，僅參考」。
- **里程碑預測**：
  - 下一級距 `nt`（<1k→1k、<10k→10k、<100k→100k、否則 null）。
  - 月成長率 `gm=(1+mom_3m)**(1/3)-1`；若 `gm>0 && nt`：`months=Math.log(nt/subs_now)/Math.log(1+gm)` → 「以近 3 月速度，約 {ceil(months)} 個月後破 {fmt(nt)}」。
  - `gm<=0`：「近期成長停滯，暫無法預估升級時間」。

### B. 健康總分 + 雷達擴為 8 軸
- 既有雷達 6 軸（訂閱/總觀看/Twitch/近期熱度/爆紅力/黏著度，皆百分位）**新增 2 軸**：
  - **成長動能** = `pctile(LON.mom, mom_3m)`
  - **開台規律** = `pctile(LON.reg, regularity)`
- **健康總分（0–100）**：對「該頻道有值的軸」取平均（跳過 null），四捨五入。
  - 顯示為大數字 + 標籤：`≥75 強健`、`50–74 穩健`、`30–49 普通`、`<30 需關注`。
  - 放在體檢卡最上方（醒目卡片）。
- 警語：總分為**相對百分位合成**，非絕對品質；缺軸者以現有軸平均，樣本越少越不穩。

### C. 相似頻道推薦「和你體質最像的台V」
- 特徵向量（用百分位，量綱一致）：`[s_pct, v_pct, f_pct, reff_pct(黏著), rh_pct(爆紅), mom_pct(動能)]`。
- 對每個候選頻道算與目標的**歐氏距離**，只用「雙方都有值」的維度，距離除以使用維度數開根（避免維度數不同失真）。
- 取最近 5 個（排除自己），顯示頭像（若已做頭像整合則加，否則純文字）+ 名稱 + 一句「相近點」（列出差距最小的 2 個維度名稱，如「黏著度、動能相近」）。
- 成本 O(N)，client-side 對 ~3,000 筆即時算可接受。
- 警語：相似基於**數據體質**，非內容題材/風格。

### D. 作息 / 事件 一句話（精簡，完整圖在 s_growth）
- **作息**（streaming.yt.channels[id]）：`「最常 週{peak_weekday} {peak_hour} 點開台・最長斷更 {gap_max_days} 天」`（weekday/hour 轉中文與台灣時間顯示）。附 coverage 註：「作息樣本：{coverage.weekdays}」。
- **事件**（events.channels[id]）：取 `delta` 最大者 → `「最大吸粉事件：{type中文} {date}（+{fmt(delta)} 訂閱）」`；無事件則略過此行。
- 兩者下方放一行連結文字：「看完整成長/作息/事件 → 切到『成長與生命週期』分頁」。

### E. 版面（一頁體檢卡順序）
1. 健康總分大卡（B）
2. KPI grid：既有排名 + A 的成長維度（+ LOCATE_TYPE 的同類型排名）
3. 8 軸雷達（B）
4. 相似頻道推薦（C）
5. 作息/事件 一句話 + 導引連結（D）
6. 既有 lc1（排名曲線）、lc2（級距）、lc4（分組百分位）保留

### F. 思路B（純數字模式）
- 純數字無 `id` → 無 growth/events/streaming。只顯示橫斷面（既有）+ 提示：「輸入數字模式無成長/體檢資料；用頻道查詢可看完整體檢卡」。健康分、相似頻道、A/D 區塊隱藏。

## 驗收
- [ ] 查一個有縱貫資料的頻道：健康總分、8 軸雷達、成長動能/生命週期/回落/里程碑、相似 5 頻道、作息/事件一句話全部出現且數字合理。
- [ ] 缺 growth/streaming/events 的頻道對應區塊顯示「資料不足」，不報錯。
- [ ] 思路B 數字模式只顯示橫斷面 + 提示，不顯示體檢專屬區塊。
- [ ] 「更新到最新(GitHub)」後仍正確（縱貫資料維持內建 snapshot，註明即可）。
- [ ] 重用既有 `findChannel/arrs/pctile/rankIn/tierOf/opts/fmt`，與 LOCATE_TYPE 的改動合併不衝突。

## 警語彙整（寫進對應卡片）
- 健康分=相對百分位合成、非絕對；缺軸以現有軸平均。
- 生命週期/動能含倖存者偏差、早期樣本稀疏。
- 里程碑為線性外推、僅參考。
- 相似頻道=數據體質相近、非內容風格。
- 作息覆蓋度依目前取樣星期（S2：sun/thu/tue/sat），補完中。
- 縱貫資料來自內建 snapshot；「更新到最新」只刷新橫斷面，不更新成長/事件/作息。
