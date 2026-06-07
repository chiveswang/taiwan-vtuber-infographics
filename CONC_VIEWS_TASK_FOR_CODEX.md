# Task: Add View-Count Concentration to 集中度 Page

## Problem

The `s_conc` (集中度與規模) section currently shows subscriber concentration (`yt_top10_share`) —
前 10 大訂閱 ÷ 全體訂閱. There is no equivalent metric for **total view counts**, so we cannot
answer whether head channels also dominate total viewing attention.

## Changes required

### 1. `analyze_quarterly_full.py` — add `yt_view_top10_share`

In `m_basic()` (around line 80), the function already computes `yt_top10_share` from subscriber
counts. Add an equivalent for YouTube view counts:

```python
# existing
pos = [s for s in subs if s and s > 0]
total = sum(pos)
top10 = sum(sorted(pos, reverse=True)[:10])

# add after the existing block:
views = [ii(r.get("YouTube View Count")) for r in rows]
vpos = [v for v in views if v and v > 0]
vtotal = sum(vpos)
vtop10 = sum(sorted(vpos, reverse=True)[:10])
```

Then add `"yt_view_top10_share": round(vtop10 / vtotal, 4) if vtotal else None,` to the returned
dict alongside `yt_top10_share`.

After editing, regenerate:
```
python analyze_quarterly_full.py
python build_full_dashboard.py
```

### 2. `build_full_dashboard.py` — add chart in `buildConc()`

In `buildConc()` (around line 332), there are four chart cards: `cc1`–`cc4`.
Add a **fifth card** (also `full` width) showing side-by-side the subscriber share and view share
trend, so the audience can see if they diverge:

Add a canvas `cc5` after the existing `cc4` card:

```html
<div class="card full">
  <h3>頭部集中度：訂閱 vs 觀看</h3>
  <p class="desc">前 10 大頻道占全體訂閱 % 與占全體觀看 %；若兩線差距大，代表訂閱/觀看結構不同</p>
  <div class="box tall"><canvas id="cc5"></canvas></div>
</div>
```

In the JS `buildConc()` body, after the existing `cc4` Chart creation, add:

```js
const Dv = getAct(inclP).filter(d => d.yt_view_top10_share != null), Lv = Dv.map(d => d.quarter);
const sv = seg(Dv.map((d,i) => d.partial ? i : -1).filter(i => i >= 0));
new Chart(cc5, {
  type: "line",
  data: {
    labels: Lv,
    datasets: [
      { label: "訂閱 top10 share", data: Dv.map(d => +(d.yt_top10_share * 100).toFixed(1)),
        borderColor: C.rate, tension: .25, segment: sv },
      { label: "觀看 top10 share", data: Dv.map(d => +(d.yt_view_top10_share * 100).toFixed(1)),
        borderColor: C.blue, tension: .25, segment: sv }
    ]
  },
  options: opts({ y: { ticks: { color: TICK, callback: v => v + "%" }, grid: { color: GRID } } })
});
```

Also update the `s_conc` insight text to reference both metrics:

```
頭部集中度（前 10 大訂閱佔比）由 2022Q1 的 44% 一路降到約 14%，觀看數集中度同步比較；同時訂閱中位數由 ~460 升到 ~1,450 → 長尾變厚。
```

### 3. FAQ / report copy (optional, low priority)

If the FAQ card I4 reads "前 10 大佔全體訂閱 X%", append "觀看 X%" alongside it so both
dimensions are visible in a single sentence.

## Verification

1. `python analyze_quarterly_full.py` → verify latest row has `yt_view_top10_share` not None
2. `python build_full_dashboard.py` → no error, JS parse OK
3. Dashboard `s_conc` shows `cc5` with two lines; both are non-trivially different from 0 and 100
