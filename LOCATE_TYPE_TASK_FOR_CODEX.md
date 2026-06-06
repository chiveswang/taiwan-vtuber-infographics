# 工單：「定位你自己」新增「依類型（團體勢/個人勢）」比較

> 小範圍增強。只改 `build_full_dashboard.py` 的定位相關函式。DIR 已有 `g` 欄位，零資料成本。

## 背景數據（預期行為的對照）
- 團體勢 764 個：訂閱中位 3,950、p90 46,800、黏著度中位 0.045
- 個人勢 2,139 個：訂閱中位 1,140、p90 9,900、黏著度中位 0.064（個人勢更黏、且最大頻道為個人勢）
- → 「同類型排名」與「全體排名」差異明顯，這正是此功能的價值。

## 資料
`DIR.channels[].g`：1=團體勢（有 Group Name）、0=個人勢。**目前只能二分**。
「企業 vs 社團」三分**做不到**（Group Name 只是字串，389 個團體無商業/社團標記）——若要三分需另維護一份「企業團體清單」，本工單不含，見文末選配。

## 改動點（`build_full_dashboard.py`）

### 1. `locate(o)` 的輸入帶入類型
- 頻道查詢（思路A）：`findChannel` 回傳的 `c` 已有 `c.g`，在呼叫 `locate(...)` 時加入 `g:c.g`。
- 純數字（思路B）：目前無類型。在思路B 區塊加一個選擇（如 `<select id="numType">`：未指定 / 團體勢 / 個人勢），`readNumO()` 一併讀成 `g`（未指定則 `null`）。

### 2. KPI 新增「同類型排名」
在 `locate()` 的 rows 中，當 `o.g!=null && o.s!=null` 時新增一筆：
```
const tArr = DIR.channels.filter(c=>c.g===o.g && c.s!=null).map(c=>c.s).sort((a,b)=>a-b);
const rt = rankIn(tArr, o.s);  // 重用既有 rankIn
rows.push({l:(o.g? "團體勢":"個人勢")+"中排名", v:"第 "+rt.rank+"/"+rt.n, d:"贏過同類型 "+rt.pct+"%"});
```

### 3. `drawLocCharts()` 的 lc4「分組百分位」新增一條「同類型」
lc4 目前有：全體 / 同級距 / 同國籍 / 同屆。新增一條：
```
if(o.g!=null){
  const tsub=DIRDATA.channels.filter(c=>c.g===o.g && c.s!=null).map(c=>c.s).sort((a,b)=>a-b);
  labels.push(o.g? "團體勢":"個人勢"); vals.push(pctile(tsub,o.s)||0);
}
```
（用 `DIRDATA`，與該函式其他分組一致，支援「更新到最新」後重算。）

### 4. （選配）雷達圖旁加一行類型對照文字
KPI 區可加一句靜態對照：「團體勢訂閱中位 3,950 / 個人勢 1,140」讓使用者理解為何兩種排名差很多。可省略。

## 驗收
- [ ] 查詢一個團體勢頻道：KPI 出現「團體勢中排名」、lc4 多一條「團體勢」長條；個人勢同理。
- [ ] 思路B 選「個人勢 + 某訂閱數」也能算出同類型排名。
- [ ] 未指定類型（思路B 預設）時不顯示該項、不報錯。
- [ ] 重用既有 `rankIn/pctile/DIRDATA`，未重造；「更新到最新(GitHub)」後仍正確。

## 選配・未來「企業/社團/個人」三分
若日後要三分：新增 `DATA` 旁一份人工維護 `agency_list.csv`（哪些 Group Name 屬商業企業），在 `build_locate_directory.py` 把 `g` 升級為 `gt`：`enterprise`/`group`/`indie`，前端比較改用 `gt`。本工單暫不做。
