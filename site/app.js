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

function maxByCount(rows, key) {
  return [...rows].sort((a, b) => Number(b.aggregate_count) - Number(a.aggregate_count))[0][key];
}

function minByCount(rows, key) {
  return [...rows].sort((a, b) => Number(a.aggregate_count) - Number(b.aggregate_count))[0][key];
}

function sumRows(rows) {
  return rows.reduce((sum, row) => sum + Number(row.aggregate_count), 0);
}

function setExplorer(view, datasets) {
  const copy = {
    platform: {
      heading: "Platform field coverage",
      body: "Counts entries by whether upstream public fields include YouTube, Twitch, both, or neither.",
      rows: datasets.platformRows,
      key: "platform_category",
      factA: "Largest category",
      factB: "Smallest category",
      factC: "Privacy rule",
      factCValue: "No IDs shown",
    },
    status: {
      heading: "Public status labels",
      body: "Aggregates upstream Activity labels. This is not a live status monitor.",
      rows: datasets.statusRows,
      key: "public_status_category",
      factA: "Largest label",
      factB: "Smallest label",
      factC: "Safety note",
      factCValue: "Not real-time",
    },
    coverage: {
      heading: "Source metadata coverage",
      body: "Summarizes repository snapshot density by month. This describes source coverage, not individual activity.",
      rows: datasets.sourceRows,
      key: "source_category",
      factA: "Latest month",
      factB: "Rows published",
      factC: "Privacy rule",
      factCValue: "Metadata only",
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
  )} public snapshot metadata records in this month.`;
  document.querySelector("#densest-quarter").textContent = quarterTotals[0][0];
  document.querySelector("#densest-quarter-note").textContent = `${formatNumber(
    quarterTotals[0][1],
  )} source metadata records in the quarter-level aggregate.`;

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
    <tr><td colspan="4">Unable to load public outputs: ${error.message}</td></tr>
  `;
});
