const csvCache = new Map();

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

function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

function displayLabel(value) {
  const labels = {
    no_public_platform_id: "無公開平台 ID / no public id",
    twitch_only: "僅 Twitch / twitch only",
    youtube_and_twitch: "雙平台 / both platforms",
    youtube_only: "僅 YouTube / youtube only",
    active: "活動中 / active",
    graduated: "已畢業 / graduated",
    preparing: "準備中 / preparing",
    unknown: "未知 / unknown",
  };
  return labels[value] ?? value;
}

function maxByCount(rows, key) {
  return displayLabel([...rows].sort((a, b) => Number(b.aggregate_count) - Number(a.aggregate_count))[0][key]);
}

function minByCount(rows, key) {
  return displayLabel([...rows].sort((a, b) => Number(a.aggregate_count) - Number(b.aggregate_count))[0][key]);
}

function sumRows(rows) {
  return rows.reduce((sum, row) => sum + Number(row.aggregate_count), 0);
}

function setExplorer(view, datasets) {
  const copy = {
    platform: {
      heading: "平台欄位覆蓋 / Platform field coverage",
      body: "統計公開欄位是否包含 YouTube、Twitch、兩者皆有或兩者皆無。Counts whether upstream public fields include YouTube, Twitch, both, or neither.",
      rows: datasets.platformRows,
      key: "platform_category",
      factA: "最大類別 / Largest category",
      factB: "最小類別 / Smallest category",
      factC: "隱私規則 / Privacy rule",
      factCValue: "不顯示 ID / No IDs shown",
    },
    status: {
      heading: "公開狀態標籤 / Public status labels",
      body: "聚合上游 Activity 標籤；這不是即時狀態監控。Aggregates upstream Activity labels; this is not a live status monitor.",
      rows: datasets.statusRows,
      key: "public_status_category",
      factA: "最大標籤 / Largest label",
      factB: "最小標籤 / Smallest label",
      factC: "安全說明 / Safety note",
      factCValue: "非即時 / Not real-time",
    },
    coverage: {
      heading: "來源 metadata 覆蓋 / Source metadata coverage",
      body: "按月份摘要 repo snapshot 密度；這描述來源覆蓋，不代表個人活動。Summarizes repository snapshot density, not individual activity.",
      rows: datasets.sourceRows,
      key: "source_category",
      factA: "最新月份 / Latest month",
      factB: "公開列數 / Rows published",
      factC: "隱私規則 / Privacy rule",
      factCValue: "只看 metadata / Metadata only",
    },
  }[view];

  document.querySelector("#explorer-heading").textContent = copy.heading;
  document.querySelector("#explorer-copy").textContent = copy.body;
  document.querySelector("#fact-a-label").textContent = copy.factA;
  document.querySelector("#fact-b-label").textContent = copy.factB;
  document.querySelector("#fact-c-label").textContent = copy.factC;
  document.querySelector("#fact-c").textContent = copy.factCValue;

  if (view === "coverage") {
    const latestMonth = [...new Set(copy.rows.map((row) => row.aggregate_period))].sort().pop();
    document.querySelector("#fact-a").textContent = latestMonth;
    document.querySelector("#fact-b").textContent = formatNumber(copy.rows.length);
  } else {
    document.querySelector("#fact-a").textContent = maxByCount(copy.rows, copy.key);
    document.querySelector("#fact-b").textContent = minByCount(copy.rows, copy.key);
  }
}

function percent(part, total) {
  return `${Math.round((part / total) * 100)}%`;
}

async function init() {
  const indexResponse = await fetch("../data/derived/public-index.json");
  const publicIndex = await indexResponse.json();
  const platformRows = await loadCsv("data/derived/platform-coverage-summary.csv");
  const statusRows = await loadCsv("data/derived/public-status-summary.csv");
  const sourceRows = await loadCsv("data/derived/source-coverage-summary.csv");
  const quarterlyRows = await loadCsv("data/derived/quarterly-ecosystem-coverage.csv");

  const totalEntries = sumRows(platformRows);
  const activeCount = statusRows
    .filter((row) => row.public_status_category === "active")
    .reduce((sum, row) => sum + Number(row.aggregate_count), 0);
  const statusTotal = sumRows(statusRows);
  const latestSourceMonth = [...new Set(sourceRows.map((row) => row.aggregate_period))].sort().pop();
  const quarterTotals = Object.entries(
    quarterlyRows.reduce((acc, row) => {
      acc[row.aggregate_period] = (acc[row.aggregate_period] ?? 0) + Number(row.aggregate_count);
      return acc;
    }, {}),
  ).sort((a, b) => b[1] - a[1]);

  document.querySelector("#total-entries").textContent = formatNumber(totalEntries);
  document.querySelector("#active-share").textContent = `${Math.round((activeCount / statusTotal) * 100)}%`;
  document.querySelector("#dataset-count").textContent = formatNumber(
    publicIndex.datasets.filter((item) => item.status === "real-derived").length,
  );
  document.querySelector("#chart-count").textContent = formatNumber(
    publicIndex.charts.filter((item) => item.status === "real-derived").length,
  );
  document.querySelector("#latest-source-month").textContent = latestSourceMonth;
  document.querySelector("#latest-source-note").textContent = `${formatNumber(
    sourceRows.filter((row) => row.aggregate_period === latestSourceMonth).reduce((sum, row) => sum + Number(row.aggregate_count), 0),
  )} 筆公開 snapshot metadata / public snapshot metadata records in this month.`;
  document.querySelector("#densest-quarter").textContent = quarterTotals[0][0];
  document.querySelector("#densest-quarter-note").textContent = `${formatNumber(
    quarterTotals[0][1],
  )} 筆季度來源 metadata / source metadata records in this quarter-level aggregate.`;

  const leadingPlatform = [...platformRows].sort((a, b) => Number(b.aggregate_count) - Number(a.aggregate_count))[0];
  const leadingStatus = [...statusRows].sort((a, b) => Number(b.aggregate_count) - Number(a.aggregate_count))[0];
  const latestSourceTotal = sourceRows
    .filter((row) => row.aggregate_period === latestSourceMonth)
    .reduce((sum, row) => sum + Number(row.aggregate_count), 0);

  document.querySelector("#platform-signal").textContent = `${displayLabel(leadingPlatform.platform_category)} 領先 / leads`;
  document.querySelector("#platform-signal-note").textContent = `${formatNumber(
    leadingPlatform.aggregate_count,
  )} 筆，占平台覆蓋聚合 ${percent(Number(leadingPlatform.aggregate_count), totalEntries)} / of aggregate platform coverage.`;
  document.querySelector("#status-signal").textContent = `${displayLabel(leadingStatus.public_status_category)} 為主 / dominates`;
  document.querySelector("#status-signal-note").textContent = `${percent(
    Number(leadingStatus.aggregate_count),
    statusTotal,
  )} 的上游公開 Activity 標籤屬於此類 / of upstream public Activity labels.`;
  document.querySelector("#source-signal").textContent = `${latestSourceMonth} 為最新 / is current`;
  document.querySelector("#source-signal-note").textContent = `${formatNumber(
    latestSourceTotal,
  )} 筆來源 metadata 可用於最新月份 / source metadata records in latest month.`;

  const datasets = { platformRows, statusRows, sourceRows };
  setExplorer("platform", datasets);

  document.querySelectorAll(".segment").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".segment").forEach((item) => {
        item.classList.toggle("is-active", item === button);
        item.setAttribute("aria-selected", item === button ? "true" : "false");
      });
      setExplorer(button.dataset.view, datasets);
    });
  });

  const rows = [...publicIndex.datasets, ...publicIndex.charts]
    .filter((item) => item.status === "real-derived")
    .map((item) => `
      <tr>
        <td><strong>${item.title}</strong><br><span>${item.path}</span></td>
        <td>${item.status}</td>
        <td>${item.type}</td>
        <td>${item.privacy_note}</td>
      </tr>
    `)
    .join("");
  document.querySelector("#outputs-table").innerHTML = rows;
}

init().catch((error) => {
  document.querySelector("#outputs-table").innerHTML = `
    <tr><td colspan="4">無法載入公開輸出 / Unable to load public outputs: ${error.message}</td></tr>
  `;
});
