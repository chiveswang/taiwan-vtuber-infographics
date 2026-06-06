# 工單（v2）：dashboard 新增「常見問題」分頁——以實際欄位為本

> 取代舊版。設計原則：**從 CSV 既有欄位出發，能答的給數字（大多綠燈），答不了的壓成頁尾一行小字**。
> 不要為了好看把黃燈升綠燈；也不要把答不了的硬做成大卡片。

**要改兩個檔**：
1. `build_locate_directory.py`：擴充 `DIR`（locate_directory.json）每頻道的欄位 → 第 1 部分。
2. `build_full_dashboard.py`：新增「常見問題」分頁 `s_faq`，放在「內容與組成」右邊 → 第 2 部分。

**完成後**依序執行，並確認新分頁正常：
```
python build_locate_directory.py
python build_full_dashboard.py
```
（HTML 由 script 產生，**勿直接改 .html**）

---

# 第 1 部分：擴充 DIR（`build_locate_directory.py`）

目前每個 channel 物件有：`n,a,y,t,nat,g,d,s,v,f,r,rh`。
新增以下欄位。資料來源 `rec[vid]`（record，**腳本已讀**）、`t`（track-list，已讀）、外加兩份要新讀的最新 snapshot（top-videos、livestreams）。

## 1a. 從 record 取（用既有 `ii()` 轉數字；URL 取原字串）

| 新欄位 | record 欄位名 | 意義 |
|---|---|---|
| `lm` | `YouTube Recent Livestream Median View Count` | 近期直播中位觀看 |
| `vm` | `YouTube Recent Video Median View Count` | 近期投稿影片中位觀看 |
| `lh` | `YouTube Recent Livestream Highest View Count` | 近期直播最高觀看 |
| `vh` | `YouTube Recent Video Highest View Count` | 近期投稿最高觀看 |
| `pop` | `YouTube Recent Total Popularity` | 總熱度（另一種口徑） |
| `lhu` | `YouTube Recent Livestream Highest Viewed URL` | 最熱直播連結 |
| `vhu` | `YouTube Recent Video Highest Viewed URL` | 最熱投稿連結 |
| `thu` | `YouTube Recent Total Highest Viewed URL` | 最熱內容連結（總） |
| `tr` | `Twitch Recent Median View Count` | Twitch 近期中位觀看 |

> 部分頻道這些欄位為空很正常（直播型沒投稿值、反之亦然）。空值存 `null`。

## 1b. 從 track-list 取

| 新欄位 | track-list 欄位名 | 意義 |
|---|---|---|
| `gn` | `Group Name` | 團體名（空字串視為個人勢） |
| `ac` | `Activity` | Active / Graduated / Preparing |

## 1c. 新讀兩份最新 snapshot：top-videos + livestreams（每頻道內容摘要）

在 `current` repo 取**最新一份** `top-videos_*.csv` 與 `livestreams_*.csv`（與 `BD`/`RC` 同月份；可比照現有寫法定常數，或列出 `2026-06/` 下該 kind 最新檔）。各讀一次、依 `VTuber ID` 分組，為每個頻道算：

- `tv`：該頻道 top-videos 中 **View Count 最高的一支**，存 `{"title":…, "vc":<int>, "url":…}`；無則 `null`。
- `cb`：該頻道內容類型桶 = 對「該頻道的 top-videos 標題 + livestreams 標題」跑分類器，存 `{game:n, chat:n, …}`。

**分類器請重用** `analyze_quarterly_full.py` 的 `TITLE_KEYWORDS` 與 `buckets()`（把該段複製進來或 import），確保與「內容與組成」分頁口徑一致：

```python
TITLE_KEYWORDS = {
  "singing":["歌","唱","karaoke","sing","cover"],
  "chat":["雜談","閒聊","聊天","talk","zatsu"],
  "game":["遊戲","game","minecraft","apex","valorant","lol","原神"],
  "asmr":["asmr","助眠"],
  "collab":["合作","連動","collab","feat."],
  "shorts":["shorts","#shorts"],
  "announcement":["公告","告知","重大","初配信","畢業","新衣装","新衣裝"],
}
# buckets(titles): 命中多桶都算，未命中歸 "other"
```

> 抓取量極小：只多讀 2 份最新 snapshot（各約數百 KB），**不碰歷史、不碰 8GB**。

## 1d. 完成後

`channels[]` 每筆新增 `lm,vm,lh,vh,pop,lhu,vhu,thu,tr,gn,ac,tv,cb`。其餘（snapshot/source/輸出路徑）不變。

---

# 第 2 部分：FAQ 分頁（`build_full_dashboard.py`）

## 2a. 三個接點

1. **TABS**（約 line 397）末尾加 `,["s_faq","常見問題",buildFaq]`。
2. **HTML body**：`<section id="s_content">…</section>` 之後插入 `<section id="s_faq">`（見 2b）。
3. **JS**：新增 `function buildFaq(inclP){…}`（放 `buildContent` 後）。lazy build / partial 切換已內建，不改 `showTab`/`rebuildAll`。

## 2b. 區塊結構

```html
<section id="s_faq">
  <div class="insight">
    本頁用本專案實際追蹤的欄位回答常見問題。<b>選一個頻道，把每題套到它身上看實際數字</b>；
    產業層級的問題下方一律可作答。本資料源無法回答的（SC 抖內、即時同接、互動率、剪輯灌流）見頁尾說明。
  </div>
  <div class="locbar">
    <div><b>套用到某個頻道（沿用「定位你自己」名單）</b><br>
      <input id="faqQ" list="faqList" placeholder="頻道名稱 / UCxxxx / twitch名稱"><datalist id="faqList"></datalist>
      <button id="faqFind">套用</button><button id="faqClear" style="background:#2a2f3d">清除</button>
      <div id="faqStatus" class="muted" style="margin-top:6px"></div></div>
  </div>
  <h3 style="margin:18px 0 6px">針對這個頻道</h3>
  <div id="faqChan"><p class="muted">未選頻道。上方輸入後按「套用」。</p></div>
  <h3 style="margin:22px 0 6px">產業整體</h3>
  <div id="faqInd"></div>
  <div class="footer" id="faqUnanswerable"></div>
</section>
```

## 2c. 機制（重用現成全域函式，勿重造）

- 重用：`findChannel(q)`、`arrs()`（升冪陣列 `s,v,f,r,rh,eff=v/s,reff=r/s`）、`pctile(arr,v)`、`tierOf(s)`、`fmt`。
- 新增徽章 CSS：
```css
.faq-badge{font-size:11px;padding:2px 9px;border-radius:20px;font-weight:600;white-space:nowrap}
.faq-green{background:rgba(55,217,154,.15);color:var(--green);border:1px solid var(--green)}
.faq-amber{background:rgba(255,180,84,.15);color:var(--amber);border:1px solid var(--amber)}
.faq-card{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:13px 16px;margin-bottom:12px}
.faq-card h4{margin:0;font-size:14.5px}
.faq-line{font-size:13px;color:#cfd6e6;margin:7px 0 0}
.faq-meta{font-size:11.5px;color:var(--muted);margin:5px 0 0}
.faq-card a{color:var(--blue)}
```
- 卡片範本：徽章 + 問題 → `.faq-line` 結論（數字即時算）→ `.faq-meta` 口徑/警語。
- 狀態：`let faqChannel=null;`。`#faqFind`→`findChannel`，找到設 `faqChannel` 並重建 `#faqChan`；找不到 `#faqStatus` 提示。`#faqClear`→清空。`#faqInd` 與 `#faqUnanswerable` 只建一次。
- bucket key→中文：`{game:"遊戲",chat:"雜談",singing:"歌回",shorts:"短影音",asmr:"ASMR",collab:"連動",announcement:"公告",other:"其他"}`。
- 徽章字：green→「可回答」、amber→「部分回答」。

---

# 第 3 部分：卡片文案與計算

`c` = 選定頻道物件。`A=arrs()`。`{}` 內即時算。所有 per-channel 卡片只在 `faqChannel` 存在時渲染進 `#faqChan`。

## 3a. 針對這個頻道（`#faqChan`）

### C1　這個頻道在全台 V 排第幾、屬哪個級距？　🟢
- 結論：`YouTube 訂閱 {fmt(c.s)}，贏過全體 {pctile(A.s,c.s)}%，屬 {tierOf(c.s)} 級距。總觀看 {fmt(c.v)}（贏過 {pctile(A.v,c.v)}%）。`
- 口徑：basic-data 最新 snapshot。

### C2　主戰場是 YouTube 還 Twitch？是否雙棲？　🟢
- 邏輯：`hasYT=c.s!=null; hasTW=c.f!=null`。雙棲=兩者皆有。主場：比 `pctile(A.s,c.s)` 與 `pctile(A.f,c.f)`，較高者為主場（只有一邊則該邊）。
- 結論：`{雙棲? "雙平台經營": "單平台"}：YouTube 訂閱 {fmt(c.s)}、Twitch 追隨 {fmt(c.f)}。相對全體，{主場платform} 是它的主戰場（YT 贏過 {pctile(A.s,c.s)}%、Twitch 贏過 {pctile(A.f,c.f)}%）。`
- 缺一邊時把該邊寫「—」。

### C3　它是直播型還是投稿型創作者？　🟢
- 邏輯：用 `c.lm`(直播中位) vs `c.vm`(投稿中位)。`lm>vm*1.5`→直播型；`vm>lm*1.5`→投稿型；皆有且相近→均衡；只有一邊→該型；皆無→資料不足那行。
- 結論：`近期直播中位觀看 {fmt(c.lm)}、投稿影片中位 {fmt(c.vm)} → 判定為「{直播型/投稿型/直播投稿均衡}」。`
- 口徑：record 直播/投稿分項中位數。

### C4　它的熱度來自直播還是投稿影片？　🟢
- 邏輯：`c.lh`(直播最高) vs `c.vh`(投稿最高)，較大者為熱度來源。
- 結論：`近期最高觀看——直播 {fmt(c.lh)}、投稿 {fmt(c.vh)}，主要爆點來自{直播/投稿}。`

### C5　它是穩定盤還是偶有爆款？　🟢
- 邏輯：`ratio=c.rh/c.r`（近期最高÷中位）。`ratio>=5`→偶有爆款（落差大）；`ratio<=2`→穩定盤；之間→中等起伏。需 `c.r>0`。
- 結論：`近期最高觀看是中位的 {ratio.toFixed(1)} 倍 → {偶有爆款／穩定盤／起伏中等}。`
- 口徑：record 近期最高 ÷ 近期中位。

### C6　它的黏著度與爆紅力在同儕間如何？　🟡
- 結論：`黏著度（近期中位觀看/訂閱）= {(c.r/c.s).toFixed(3)}，贏過全體 {pctile(A.reff,c.r/c.s)}%；爆紅力（近期最高觀看 {fmt(c.rh)}）贏過 {pctile(A.rh,c.rh)}%。`
- 警語：黏著度是用 VOD 觀看推估，**非真實同接**。

### C7　它最熱的一場直播 / 一支影片是？　🟢
- 結論（給可點擊連結，有才顯示）：
  `最熱直播：<a href="{c.lhu}" target="_blank">觀看 {fmt(c.lh)}</a>；最熱投稿：<a href="{c.vhu}" target="_blank">觀看 {fmt(c.vh)}</a>。`
- 缺 URL 的那項略過。

### C8　它近期都播什麼類型內容？　🟢（新發現）
- 邏輯：`c.cb` 取前 3 大桶（排除空），轉中文 + 佔比。
- 結論：`近期內容以 {桶1中文 X%}、{桶2 Y%}、{桶3 Z%} 為主。`
- 口徑：該頻道 top-videos + livestreams 標題分類（與「內容與組成」同口徑）。
- 圖（選配）：可在此卡放一個小 doughnut 畫 `c.cb`。

### C9　它最熱門的影片是哪支？　🟢（新發現）
- 結論（`c.tv` 存在才顯示）：`最熱影片：<a href="{c.tv.url}" target="_blank">{c.tv.title}</a>（觀看 {fmt(c.tv.vc)}）。`
- 無則：`此 snapshot 沒抓到它的熱門影片。`

### C10　它出道多久、目前狀態、團體還個人？　🟢
- 邏輯：由 `c.d`(出道日) 算距今年資（無則「未記載」）；`c.ac` 狀態；`c.gn` 有值=團體勢。
- 結論：`{c.gn? "團體勢（"+c.gn+"）":"個人勢"}，狀態 {c.ac}，出道 {c.d || "未記載"}（約 {年資} 年）。`

### C11　它同團體還有誰、團體規模如何？　🟢（c.gn 有值才顯示此卡）
- 邏輯：`mates=DIR.channels.filter(x=>x.gn===c.gn)`；團體總訂閱 `sum(s)`；列同團前幾名（依 s 排序，顯示 name+fmt(s)，最多 5 個）。
- 結論：`團體「{c.gn}」共 {mates.length} 位、合計訂閱 {fmt(總和)}。主要成員：{前5名 name(訂閱)}。`

### C12　它跟同屆/同國籍/同級距比贏過多少人？　🟢
- 可重用「定位你自己」lc4 的分組百分位邏輯（同級距 / 同國籍 / 同屆出道，對 `c.s`）。
- 結論：`同級距贏過 {x}%、同國籍({c.nat})贏過 {y}%、同屆({出道年})贏過 {z}%。`
- 也可在 `.faq-meta` 附「更完整的定位圖見『定位你自己』分頁」。

## 3b. 產業整體（`#faqInd`，永遠顯示）

### I1　台 V 產業在擴張還是成熟？　🟢
- 結論：`出道潮高峰在 {COH 中 debuts 最大的季}（單季 {值} 人），近季已放緩；現存名單 {COH.current.total} 人。產業由擴張轉成熟。`
- meta：詳見「進出場動態」分頁。

### I2　哪種內容當道？短影音崛起了嗎？　🟢
- 結論：取最新已結算季 `topvid_buckets`，算 shorts 佔比與最大類別 → `最新一季熱門影片以 {最大類別中文} 為主，短影音(shorts)佔 {shorts%}。`
- meta：詳見「內容與組成」分頁。

### I3　國籍組成、團體 vs 個人比例？　🟢
- 結論：`現存名單台 {TW}、港 {HK}、馬 {MY} 為前三；團體 {group} : 個人 {indie}。`（取自 `COH.current`）

### I4　頭部集中度與級距金字塔？　🟢
- 結論：取最新季 `yt_top10_share`、`yt_subs_median` → `前 10 大佔全體訂閱 {share%}，訂閱中位數 {median}；長尾變厚、中段墊高。`
- meta：詳見「集中度與規模」「訂閱級距金字塔」分頁。

### I5　某屆出道者現在還活著的比例（畢業率）？　🟢
- 邏輯（用 DIR.channels 即時算）：依 `d` 取出道年分組，每組算 `ac==="Active"` 佔比。輸出近幾屆一行：`2022 屆存活 {x}%、2023 屆 {y}%、2024 屆 {z}%…`
- 警語：track-list 為現存記載，**含倖存者偏差**（早被刪除者未必在列）。

### I6　台 V 是直播型還是投稿型生態？　🟢
- 邏輯（DIR 即時算）：統計 `lm>vm*1.5`（直播型）、`vm>lm*1.5`（投稿型）、其餘（均衡）三類佔比（僅計兩值皆有者）。
- 結論：`在兩項皆有數據的頻道中，直播型 {a}%、投稿型 {b}%、均衡 {c}% → 台 V 以{多數類型}為主。`

## 3c. 頁尾誠實說明（`#faqUnanswerable`，固定文字）

```
本資料源（YouTube / Twitch 公開頻道統計）無法回答以下問題，需另接外部資料源：
・Super Chat 抖內金額與主題關聯 → 需 Playboard 等金流工具
・最高同時觀看數（同接）、黃金收視時段 → 需自建直播同接爬蟲
・工商轉換力（留言/按讚互動率） → 需影片層級互動數據
・精華剪輯（烤肉）對主頻道的灌流 → 需追蹤剪輯頻道清單
```

---

# 第 4 部分：驗收清單

- [ ] `build_locate_directory.py` 重生 `locate_directory.json`，每頻道含新欄位 `lm,vm,lh,vh,pop,lhu,vhu,thu,tr,gn,ac,tv,cb`；分類器與 `analyze_quarterly_full.py` 一致。
- [ ] 「常見問題」分頁在「內容與組成」右邊，樣式一致、可切換。
- [ ] 選頻道後 `#faqChan` 出現 C1–C12（C11 只在有團體時出現），數字皆即時算、非寫死；連結可點。
- [ ] `#faqInd` 永遠顯示 I1–I6；I5/I6 由 DIR 即時計算。
- [ ] 頁尾誠實說明固定顯示。
- [ ] C6 標明「非真實同接」；I5 標明倖存者偏差。
- [ ] 切換「顯示未結算季度」不報錯；`python build_full_dashboard.py` 無 console error。
- [ ] 重用既有 `findChannel`/`arrs`/`pctile`/`tierOf`，未重造輪子。

> 備註：本版多數題目為 🟢/🟡，無 🔴 卡片（答不了的集中在頁尾）。這是刻意設計，請保持誠實——proxy 指標（黏著度）務必標註限制，不要當成精確值。
