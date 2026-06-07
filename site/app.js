const csvCache = new Map();
const chartInstances = [];

const palette = {
  accent: "#7c5cff",
  green: "#37d99a",
  amber: "#ffb454",
  blue: "#4aa8ff",
  red: "#ff5a5f",
  purple: "#a970ff",
  pink: "#ff7eb6",
  teal: "#2dd4bf",
  grid: "#2a2f3d",
  text: "#e8eaf0",
  muted: "#9aa3b5",
};

async function loadCsv(path) {
  if (csvCache.has(path)) return csvCache.get(path);
  const response = await fetch(`../${path}`);
  const text = await response.text();
  const rows = parseCsv(text);
  csvCache.set(path, rows);
  return rows;
}

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = splitCsvLine(lines.shift());
  return lines.map((line) => {
    const values = splitCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
  });
}

function splitCsvLine(line) {
  const cells = [];
  let value = "";
  let inQuotes = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && inQuotes && next === '"') {
      value += '"';
      index += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      cells.push(value);
      value = "";
    } else {
      value += char;
    }
  }
  cells.push(value);
  return cells;
}

function numberValue(row, key) {
  const value = Number(row[key]);
  return Number.isFinite(value) ? value : null;
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

function percent(value) {
  return `${Math.round(Number(value) * 1000) / 10}%`;
}

function settledRows(rows) {
  return rows.filter((row) => row.partial !== "true");
}

function latestSettled(rows) {
  return [...settledRows(rows)].sort((a, b) => a.aggregate_period.localeCompare(b.aggregate_period)).pop();
}

function quarterlyLabel(period) {
  const [year, month] = period.split("-");
  const quarter = Math.ceil(Number(month) / 3);
  return `${year}Q${quarter}`;
}

function chartOptions(extra = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { labels: { color: palette.muted, boxWidth: 12 } },
      tooltip: {
        backgroundColor: "#10141d",
        borderColor: palette.grid,
        borderWidth: 1,
        titleColor: "#fff",
        bodyColor: palette.text,
      },
    },
    scales: {
      x: { ticks: { color: palette.muted, maxRotation: 0 }, grid: { color: "transparent" } },
      y: { ticks: { color: palette.muted }, grid: { color: palette.grid } },
    },
    ...extra,
  };
}

function makeChart(id, config) {
  const canvas = document.querySelector(`#${id}`);
  if (!canvas) return;
  chartInstances.push(new Chart(canvas, config));
}

function setTabs() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((item) => item.classList.toggle("on", item === button));
      document.querySelectorAll(".panel-section").forEach((section) => {
        section.classList.toggle("on", section.id === `tab-${button.dataset.tab}`);
      });
      chartInstances.forEach((chart) => chart.resize());
    });
  });
}

function renderKpis(activityRows, cohortRows) {
  const latest = latestSettled(activityRows);
  const latestCohort = latestSettled(cohortRows);
  const cards = [
    {
      label: "最新已結算季度 / Latest settled quarter",
      value: quarterlyLabel(latest.aggregate_period),
      detail: "KPI 避開未結算季度",
    },
    {
      label: "追蹤頻道數 / Tracked channels",
      value: formatNumber(numberValue(latest, "tracked_channels")),
      detail: "只作總量呈現",
    },
    {
      label: "近期活躍 / Recently active",
      value: formatNumber(numberValue(latest, "recently_active_any")),
      detail: `${latest.activation_rate}% activation rate`,
    },
    {
      label: "累積淨活躍世代 / Net active cohort",
      value: formatNumber(numberValue(latestCohort, "cumulative_active")),
      detail: "由出道/畢業聚合重建",
    },
  ];
  document.querySelector("#overview-kpis").innerHTML = cards
    .map(
      (card) => `
        <article class="kpi">
          <span class="l">${card.label}</span>
          <strong class="v">${card.value}</strong>
          <span class="d">${card.detail}</span>
        </article>
      `,
    )
    .join("");
}

function renderOverview(activityRows) {
  const rows = activityRows.filter((row) => numberValue(row, "tracked_channels"));
  const labels = rows.map((row) => quarterlyLabel(row.aggregate_period));
  makeChart("overview-scale", {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "追蹤頻道 / tracked",
          data: rows.map((row) => numberValue(row, "tracked_channels")),
          borderColor: palette.blue,
          backgroundColor: "rgba(74,168,255,.15)",
          tension: 0.25,
          fill: true,
        },
        {
          label: "近期活躍 / active",
          data: rows.map((row) => numberValue(row, "recently_active_any")),
          borderColor: palette.green,
          backgroundColor: "rgba(55,217,154,.12)",
          tension: 0.25,
          fill: true,
        },
      ],
    },
    options: chartOptions(),
  });

  makeChart("activation-rate", {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "活躍率 / activation rate",
          data: rows.map((row) => numberValue(row, "activation_rate")),
          borderColor: palette.amber,
          backgroundColor: "rgba(255,180,84,.15)",
          tension: 0.25,
          fill: true,
        },
      ],
    },
    options: chartOptions({ scales: { ...chartOptions().scales, y: { ...chartOptions().scales.y, ticks: { color: palette.muted, callback: (value) => `${value}%` } } } }),
  });

  makeChart("platform-mix", {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "YouTube",
          data: rows.map((row) => numberValue(row, "recently_active_yt")),
          borderColor: palette.red,
          backgroundColor: "rgba(255,90,95,.1)",
          tension: 0.25,
        },
        {
          label: "Twitch",
          data: rows.map((row) => numberValue(row, "recently_active_twitch")),
          borderColor: palette.purple,
          backgroundColor: "rgba(169,112,255,.1)",
          tension: 0.25,
        },
      ],
    },
    options: chartOptions(),
  });
}

function renderCohort(cohortRows) {
  const rows = cohortRows;
  const labels = rows.map((row) => quarterlyLabel(row.aggregate_period));
  makeChart("cohort-flow", {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "出道 / debuts", data: rows.map((row) => numberValue(row, "debuts")), backgroundColor: palette.green },
        { label: "畢業 / graduations", data: rows.map((row) => numberValue(row, "graduations")), backgroundColor: palette.red },
      ],
    },
    options: chartOptions(),
  });
  makeChart("cohort-cumulative", {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "累積淨活躍 / cumulative net active",
          data: rows.map((row) => numberValue(row, "cumulative_active")),
          borderColor: palette.blue,
          backgroundColor: "rgba(74,168,255,.15)",
          tension: 0.25,
          fill: true,
        },
      ],
    },
    options: chartOptions(),
  });
  makeChart("cohort-group", {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "個人勢 / indie", data: rows.map((row) => numberValue(row, "debuts_indie")), backgroundColor: palette.teal },
        { label: "團體勢 / group", data: rows.map((row) => numberValue(row, "debuts_group")), backgroundColor: palette.purple },
      ],
    },
    options: chartOptions({ scales: { x: { stacked: true, ticks: { color: palette.muted, maxRotation: 0 }, grid: { color: "transparent" } }, y: { stacked: true, ticks: { color: palette.muted }, grid: { color: palette.grid } } } }),
  });
}

function renderConcentration(activityRows) {
  const rows = activityRows.filter((row) => numberValue(row, "yt_top10_share"));
  const labels = rows.map((row) => quarterlyLabel(row.aggregate_period));
  makeChart("top-share", {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "訂閱 top10 share",
          data: rows.map((row) => Number(row.yt_top10_share) * 100),
          borderColor: palette.amber,
          tension: 0.25,
        },
        {
          label: "觀看 top10 share",
          data: rows.map((row) => Number(row.yt_view_top10_share) * 100),
          borderColor: palette.pink,
          tension: 0.25,
        },
      ],
    },
    options: chartOptions({ scales: { ...chartOptions().scales, y: { ...chartOptions().scales.y, ticks: { color: palette.muted, callback: (value) => `${value}%` } } } }),
  });
  makeChart("tier-pyramid", {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: ">100k", data: rows.map((row) => numberValue(row, "yt_tier_mega")), backgroundColor: palette.pink },
        { label: "10k-100k", data: rows.map((row) => numberValue(row, "yt_tier_large")), backgroundColor: palette.purple },
        { label: "1k-10k", data: rows.map((row) => numberValue(row, "yt_tier_mid")), backgroundColor: palette.blue },
        { label: "<1k", data: rows.map((row) => numberValue(row, "yt_tier_small")), backgroundColor: palette.grid },
      ],
    },
    options: chartOptions({ scales: { x: { stacked: true, ticks: { color: palette.muted, maxRotation: 0 }, grid: { color: "transparent" } }, y: { stacked: true, ticks: { color: palette.muted }, grid: { color: palette.grid } } } }),
  });
}

function latestScopeRows(contentRows, scope) {
  const rows = settledRows(contentRows.filter((row) => row.content_scope === scope));
  const latest = [...new Set(rows.map((row) => row.aggregate_period))].sort().pop();
  return rows.filter((row) => row.aggregate_period === latest);
}

function categoryShareRows(contentRows, scope, category) {
  const grouped = {};
  settledRows(contentRows.filter((row) => row.content_scope === scope)).forEach((row) => {
    grouped[row.aggregate_period] ??= { total: 0, target: 0 };
    grouped[row.aggregate_period].total += Number(row.aggregate_count);
    if (row.content_category === category) grouped[row.aggregate_period].target += Number(row.aggregate_count);
  });
  return Object.entries(grouped)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([period, values]) => ({ period, share: values.total ? (values.target / values.total) * 100 : 0 }));
}

function renderContent(contentRows) {
  const latestTop = latestScopeRows(contentRows, "top_videos");
  makeChart("top-video-categories", {
    type: "doughnut",
    data: {
      labels: latestTop.map((row) => row.content_category),
      datasets: [
        {
          data: latestTop.map((row) => numberValue(row, "aggregate_count")),
          backgroundColor: [palette.blue, palette.purple, palette.green, palette.amber, palette.red, palette.pink, palette.teal, "#667085"],
          borderColor: "#181b24",
        },
      ],
    },
    options: chartOptions({ scales: {} }),
  });

  const shortsRows = categoryShareRows(contentRows, "top_videos", "shorts");
  makeChart("shorts-trend", {
    type: "line",
    data: {
      labels: shortsRows.map((row) => quarterlyLabel(row.period)),
      datasets: [{ label: "shorts share", data: shortsRows.map((row) => row.share), borderColor: palette.green, backgroundColor: "rgba(55,217,154,.12)", fill: true, tension: 0.25 }],
    },
    options: chartOptions({ scales: { ...chartOptions().scales, y: { ...chartOptions().scales.y, ticks: { color: palette.muted, callback: (value) => `${value}%` } } } }),
  });

  const latestYt = latestScopeRows(contentRows, "youtube_livestreams");
  const latestTw = latestScopeRows(contentRows, "twitch_livestreams");
  const categories = [...new Set([...latestYt, ...latestTw].map((row) => row.content_category))].sort();
  makeChart("livestream-categories", {
    type: "bar",
    data: {
      labels: categories,
      datasets: [
        { label: "YouTube", data: categories.map((category) => Number(latestYt.find((row) => row.content_category === category)?.aggregate_count ?? 0)), backgroundColor: palette.red },
        { label: "Twitch", data: categories.map((category) => Number(latestTw.find((row) => row.content_category === category)?.aggregate_count ?? 0)), backgroundColor: palette.purple },
      ],
    },
    options: chartOptions(),
  });
}

function renderOutputs(publicIndex) {
  const rows = [...publicIndex.datasets, ...publicIndex.charts]
    .filter((item) => item.status === "real-derived")
    .map(
      (item) => `
      <tr>
        <td><strong>${item.title}</strong><br><span>${item.path}</span></td>
        <td>${item.status}</td>
        <td>${item.type}</td>
        <td>${item.privacy_note}</td>
      </tr>
    `,
    )
    .join("");
  document.querySelector("#outputs-table").innerHTML = rows;
}

async function init() {
  Chart.defaults.color = palette.muted;
  Chart.defaults.font.family = '"Noto Sans TC", "PingFang TC", "Microsoft JhengHei", system-ui, sans-serif';

  const indexResponse = await fetch("../data/derived/public-index.json");
  const publicIndex = await indexResponse.json();
  const activityRows = await loadCsv("data/derived/activity-quarterly-summary.csv");
  const cohortRows = await loadCsv("data/derived/cohort-quarterly-summary.csv");
  const contentRows = await loadCsv("data/derived/content-category-quarterly-summary.csv");

  setTabs();
  renderKpis(activityRows, cohortRows);
  renderOverview(activityRows);
  renderCohort(cohortRows);
  renderConcentration(activityRows);
  renderContent(contentRows);
  renderOutputs(publicIndex);
}

init().catch((error) => {
  document.querySelector("#outputs-table").innerHTML = `
    <tr><td colspan="4">無法載入公開輸出 / Unable to load public outputs: ${error.message}</td></tr>
  `;
});
