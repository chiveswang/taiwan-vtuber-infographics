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

async function init() {
  const indexResponse = await fetch("../data/derived/public-index.json");
  const publicIndex = await indexResponse.json();
  const platformRows = await loadCsv("data/derived/platform-coverage-summary.csv");
  const statusRows = await loadCsv("data/derived/public-status-summary.csv");

  const totalEntries = platformRows.reduce((sum, row) => sum + Number(row.aggregate_count), 0);
  const activeCount = statusRows
    .filter((row) => row.public_status_category === "active")
    .reduce((sum, row) => sum + Number(row.aggregate_count), 0);
  const statusTotal = statusRows.reduce((sum, row) => sum + Number(row.aggregate_count), 0);

  document.querySelector("#total-entries").textContent = formatNumber(totalEntries);
  document.querySelector("#active-share").textContent = `${Math.round((activeCount / statusTotal) * 100)}%`;
  document.querySelector("#dataset-count").textContent = formatNumber(
    publicIndex.datasets.filter((item) => item.status === "real-derived").length,
  );
  document.querySelector("#chart-count").textContent = formatNumber(
    publicIndex.charts.filter((item) => item.status === "real-derived").length,
  );

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
