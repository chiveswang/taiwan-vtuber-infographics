# Task: Show Located Channel on 雙棲象限 Scatter Plot

## Problem

In `buildGrowth()` → `renderCross()` (around line 742 of `build_full_dashboard.py`), when a
channel is selected via the growth-section search bar, the function does:

```js
if (x) {
  panel("gw_cross", `...kpiRow(...)...`);
  return;   // ← exits without drawing the scatter plot
}
```

The selected channel only sees a row of KPI chips. The scatter plot showing all dual-platform
channels disappears, so the user cannot see *where* the selected channel sits on the quadrant
relative to others.

## Required fix

Always draw the scatter plot. When a channel is selected, render it as a highlighted point.

### Revised `renderCross()` logic

```js
function renderCross() {
  clearCharts();
  const xData = gwChannel && gwChannel.id ? XPLAT.channels[gwChannel.id] : null;
  const ind = XPLAT.industry, ms = ind.months.filter(m => m <= nowMonth);
  const idx = ms.map(m => ind.months.indexOf(m));

  // KPI row — always show if channel is selected
  const kpiHtml = xData
    ? `<div class="note">Twitch 追隨與 YouTube 訂閱語意不同，跨平台只比較平台內百分位。</div>`
      + kpiRow([["主場", xData.home], ["YT 平台內百分位", xData.yt_pct + "%"],
                ["Twitch 平台內百分位", xData.tw_pct + "%"], ["近期傾斜", xData.tilt],
                ["YT 近3月", pct(xData.yt_mom)], ["Twitch 近3月", pct(xData.tw_mom)]])
    : `<div class="note">未選頻道時顯示產業平台版圖。Twitch 線從 2023-07 起；總量圖僅看趨勢，不比較絕對高低。</div>`;

  panel("gw_cross", kpiHtml + `<div class="grid">
    <div class="card full">
      <h3>雙棲象限：誰在兩個平台都站得住？</h3>
      <p class="desc">每個點是雙棲頻道；X=YouTube 平台內百分位，Y=Twitch 平台內百分位。
        ${xData ? `<b>橘色大點</b>為目前選定頻道（${escHtml(gwChannel.n || gwChannel.id || "")}）。` : ""}
      </p>
      <div class="box tall"><canvas id="gwX4"></canvas></div>
    </div>
    <div class="card"><h3>平台存在型態</h3><div class="box"><canvas id="gwX1"></canvas></div></div>
    <div class="card"><h3>平台總量趨勢</h3><div class="box"><canvas id="gwX2"></canvas></div></div>
    <div class="card full"><h3>出道屆平台選擇</h3><div class="box"><canvas id="gwX3"></canvas></div></div>
  </div>`);

  // scatter — background points
  const pts = Object.entries(XPLAT.channels).map(([id, c]) => ({
    x: c.yt_pct, y: c.tw_pct, n: c.n || id, home: c.home, tilt: c.tilt, id
  })).filter(p => isFinite(p.x) && isFinite(p.y));

  const datasets = [{
    label: "雙棲頻道",
    data: pts,
    backgroundColor: pts.map(p =>
      p.x >= 90 && p.y >= 90 ? C.rate + "cc" :
      p.home === "Twitch" ? C.tw + "99" :
      p.home === "YT" ? C.blue + "99" : C.green + "aa"
    ),
    pointRadius: 4,
    pointHoverRadius: 7
  }];

  // highlight selected channel
  if (xData) {
    datasets.push({
      label: gwChannel.n || gwChannel.id || "選定頻道",
      data: [{ x: xData.yt_pct, y: xData.tw_pct, n: gwChannel.n || gwChannel.id, home: xData.home, tilt: xData.tilt }],
      backgroundColor: C.amber || "#ffb454",
      borderColor: "#fff",
      borderWidth: 2,
      pointRadius: 10,
      pointHoverRadius: 13,
      pointStyle: "star"
    });
  }

  store.gwX4 = new Chart(document.getElementById("gwX4"), {
    type: "scatter",
    data: { datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: !!xData, labels: { color: TICK } },
        tooltip: { callbacks: { label: ctx => `${ctx.raw.n}｜YT ${ctx.raw.x}% / TW ${ctx.raw.y}%｜${ctx.raw.home}｜${ctx.raw.tilt}` } }
      },
      scales: {
        x: { min: 0, max: 100, ticks: { color: TICK, callback: v => v + "%" }, grid: { color: GRID }, title: { display: true, text: "YouTube 平台內百分位", color: TICK } },
        y: { min: 0, max: 100, ticks: { color: TICK, callback: v => v + "%" }, grid: { color: GRID }, title: { display: true, text: "Twitch 平台內百分位", color: TICK } }
      }
    }
  });

  // gwX1, gwX2, gwX3 — unchanged from existing code
  store.gwX1 = new Chart(document.getElementById("gwX1"), { ... }); // same as before
  // etc.
}
```

## Notes

- `C.amber` is not defined in the color constants — add it or use `"#ffb454"` directly.
- The `clearCharts()` call at the top of `renderCross()` already destroys `gwX4`, `gwX1`,
  `gwX2`, `gwX3` — so they must be recreated every time. This is the existing pattern; keep it.
- Use `document.getElementById("gwX4")` (not the bare global `gwX4`) for the same reason as
  the rankBar fix.
- `gwX1`, `gwX2`, `gwX3` code is unchanged — copy it verbatim from the existing else-branch.

## Verification

1. Open dashboard → 成長與生命週期 → 雙棲比較
2. Without selecting a channel: scatter plot appears with all dual-platform channels
3. Select a channel (e.g. type a name in gwQ, click 套用), go to 雙棲比較:
   - KPI row shows YT/TW percentile, home, tilt
   - Scatter plot still shows all background points
   - Selected channel rendered as a distinct large star/marker
4. Clear channel → scatter returns to no-highlight mode
