# 工單：排行榜 / 探索頁（新分頁 `s_rank`）

> 定位是「查自己」，這頁是「看全局誰強」。把累積的 per-channel 指標翻成榜單。
> 只改 `build_full_dashboard.py`，資料用既有 DIR/growth/events/streaming（靠 `id` join），全部內嵌。

## 接點
1. TABS 加 `["s_rank","排行榜",buildRank]`（放在「定位你自己」附近）。
2. body 加 `<section id="s_rank">`：頂部榜單選擇 chip + 篩選列 + `<div id="rankList">`。
3. `function buildRank(){…}`：依選中的榜 + 篩選即時排序渲染。

## 榜單清單（標資料就緒度）
| 榜 | 指標 | 來源 | 就緒 | 過濾門檻(去雜訊) |
|---|---|---|---|---|
| 訂閱 Top | `s` | DIR | ✅ | — |
| 總觀看 Top | `v` | DIR | ✅ | — |
| Twitch 追隨 Top | `f` | DIR | ✅ | — |
| 成長最快 | `mom_3m` | growth | ✅ | subs≥5,000 |
| 年化成長 | `cagr_yr` | growth | ✅ | subs≥5,000 |
| 最黏 | `r/s` | DIR | ✅ | subs≥1,000 且 r 有值 |
| 爆紅力 | `rh` | DIR | ✅ | — |
| 最大吸粉事件 | `delta`(跨頻道展開) | events | ✅ | — |
| 出道黑馬 | 近 N 季出道 + `subs_now` 或 `mom_3m` | growth | ✅ | 出道≤18 個月 |
| 最規律開台 | `active_weeks / 跨距週數` | streaming.yt | ✅ | n_streams≥10 |
| 熱門影片 Top | `tv.vc` | DIR.tv | ⏳ 待 FAQ 工單把 `tv` 寫入 DIR |
| 雙棲最強 | 兩平台百分位和 | crossplatform | ⏳ 待 Twitch 工單 |

> ⏳ 兩榜先放佔位（「待資料」字樣），其餘先上。

## 篩選列（共用，client-side）
- 級距（全部 / >100k / 10k–100k / 1k–10k / <1k）
- 國籍（全部 / TW / HK / MY / …）
- 類型（全部 / 團體勢 / 個人勢，用 `g`）
- 顯示筆數（預設 15，可 30/50）

## 每列呈現
`名次 + （頭像*）+ 名稱 + 指標值 + 級距/國籍 tag + 連結`
- 名稱可點 → **切到「定位你自己」並帶入該頻道**（重用 `findChannel`/`showTab('s_locate')` + 觸發定位），形成「榜上看到→點進去體檢」的動線。
- 「最大吸粉事件」榜每列另顯示事件類型/日期 + 影片連結。
- *頭像：若日後做頭像整合則加，否則純文字。

## 計算備註
- 成長/黏著/規律榜務必套**過濾門檻**，否則小頻道用比率會洗榜（已驗：不過濾會被幾百訂閱的頻道佔據）。
- 「最大吸粉事件」：把 `events.channels[*].events[]` 攤平、取 `delta` 不為 null 者排序（共 ~4,214 筆）。
- 規律 = `active_weeks / max(1, first→last 週數)`，與體檢卡 `LOCATE_UPGRADE` 同定義（若該工單已實作則重用）。

## 驗收
- [ ] 榜單 chip 可切換；篩選即時生效；門檻防小頻道洗榜。
- [ ] 各就緒榜數字合理（如成長最快榜 subs≥5k 後仍是高成長頻道）。
- [ ] 點名稱可跳到定位並載入該頻道。
- [ ] ⏳ 兩榜顯示「待資料」不報錯。
- [ ] 重用 `findChannel/pctile/fmt/tierOf`，全內嵌。

## 警語
- 成長/黏著/規律為比率指標，已用門檻過濾；仍可能受近期波動影響。
- 事件 delta 為事件後毛估、未扣自然成長。
