import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const ROOT = process.cwd();
const ACT = path.join(ROOT, "outputs", "activity");
const OUT = path.join(ACT, "taiwan-vtuber-live-briefing.pptx");
const ARTIFACT_TOOL =
  process.env.ARTIFACT_TOOL_MJS ||
  "C:/Users/sweet/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const { Presentation, Slide, PresentationFile } = await import(pathToFileURL(ARTIFACT_TOOL));

const W = 1280;
const H = 720;
const C = {
  bg: "#0f131c",
  panel: "#171d29",
  line: "#2a3140",
  text: "#f4f7fb",
  muted: "#9aa3b5",
  blue: "#4aa8ff",
  green: "#37d99a",
  amber: "#ffb454",
  red: "#ff5a5f",
  purple: "#a970ff",
};

async function readJson(name) {
  return JSON.parse(await fs.readFile(path.join(ACT, name), "utf8"));
}

const [quarterly, cohort, locate, growth, streams, xplat] = await Promise.all([
  readJson("quarterly_activity.json"),
  readJson("quarterly_full.json"),
  readJson("locate_directory.json"),
  readJson("growth.json"),
  readJson("streaming.json"),
  readJson("crossplatform.json"),
]);

const settled = quarterly.series.filter((d) => !d.partial);
const cur = settled.at(-1);
const channels = locate.channels || [];
const byId = Object.fromEntries(channels.filter((c) => c.id).map((c) => [c.id, c]));
const fmt = (n) => (n == null || !Number.isFinite(Number(n)) ? "—" : Number(n).toLocaleString("en-US"));
const pct = (n) => (n == null || !Number.isFinite(Number(n)) ? "—" : `${(Number(n) * 100).toFixed(1)}%`);
const ratioPct = (n) => (n == null || !Number.isFinite(Number(n)) ? "—" : `${Number(n).toFixed(1)}%`);
const strip = (s) => String(s ?? "").replace(/[<>]/g, "");

const topSubs = channels
  .filter((c) => c.s)
  .sort((a, b) => b.s - a.s)
  .slice(0, 8);
const dual = Object.values(xplat.channels || {});
const topDual = dual.filter((x) => x.yt_pct >= 90 && x.tw_pct >= 90).length;
const topDualRows = dual
  .filter((x) => x.yt_pct >= 90 && x.tw_pct >= 90)
  .sort((a, b) => b.yt_pct + b.tw_pct - (a.yt_pct + a.tw_pct))
  .slice(0, 6);
const groups = {};
Object.entries(growth.channels || {}).forEach(([id, g]) => {
  const c = byId[id] || {};
  const gn = String(g.gn || c.gn || "").trim();
  if (!gn) return;
  (groups[gn] ||= []).push({ ...c, ...g, id });
});
function median(values) {
  const rows = values.filter((v) => v != null && Number.isFinite(Number(v))).sort((a, b) => a - b);
  return rows.length ? rows[Math.floor(rows.length / 2)] : null;
}
const agencyStats = Object.entries(groups)
  .map(([gn, members]) => ({
    gn,
    members: members.length,
    total: members.reduce((a, x) => a + (x.subs_now || x.s || 0), 0),
    median: median(members.map((x) => x.subs_now || x.s)),
  }))
  .filter((x) => x.members >= 2 && x.total > 0)
  .sort((a, b) => b.total - a.total)
  .slice(0, 8);
const ytPeakHour = streams.yt.industry.hours.reduce((best, v, i, arr) => (v > arr[best] ? i : best), 0);
const twPeakHour = streams.tw.industry.hours.reduce((best, v, i, arr) => (v > arr[best] ? i : best), 0);
const cohortCurrent = cohort.cohort?.current || cohort.current || {};
const natTop = Object.entries(cohortCurrent.nationality || {})
  .sort((a, b) => b[1] - a[1])
  .slice(0, 3)
  .map(([k, v]) => `${k} ${fmt(v)}`)
  .join("、");

function addShape(slide, { x, y, w, h, fill = C.panel, line = C.line, geometry = "rect" }) {
  return slide.shapes.add({
    geometry,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: line, width: line === "#00000000" ? 0 : 1 },
  });
}

function addText(slide, text, { x, y, w, h, size = 28, color = C.text, bold = false, align = "left", valign = "top" }) {
  const shape = addShape(slide, { x, y, w, h, fill: "#00000000", line: "#00000000" });
  shape.text = strip(text);
  shape.text.fontSize = size;
  shape.text.color = color;
  shape.text.bold = bold;
  shape.text.typeface = "Microsoft JhengHei";
  shape.text.alignment = align;
  shape.text.verticalAlignment = valign;
  shape.text.insets = { left: 0, right: 0, top: 0, bottom: 0 };
  return shape;
}

function baseSlide(p, eyebrow, title) {
  const slide = new Slide(p, { id: `s${p.slides.count + 1}` });
  p.slides.add(slide);
  addShape(slide, { x: 0, y: 0, w: W, h: H, fill: C.bg, line: "#00000000" });
  addShape(slide, { x: 0, y: 0, w: 10, h: H, fill: C.green, line: "#00000000" });
  addText(slide, eyebrow, { x: 54, y: 34, w: 620, h: 28, size: 16, color: C.green, bold: true });
  addText(slide, title, { x: 54, y: 70, w: 900, h: 72, size: 34, bold: true });
  addText(slide, "Taiwan VTuber Tracking Data Index｜2026-06-07", {
    x: 820,
    y: 664,
    w: 380,
    h: 24,
    size: 12,
    color: C.muted,
    align: "right",
  });
  return slide;
}

function metric(slide, label, value, note, x, y, w = 220, color = C.blue) {
  addShape(slide, { x, y, w, h: 126, fill: "#151b27", line: C.line });
  addText(slide, label, { x: x + 18, y: y + 16, w: w - 36, h: 24, size: 14, color: C.muted, bold: true });
  addText(slide, value, { x: x + 18, y: y + 43, w: w - 36, h: 38, size: 30, color, bold: true });
  addText(slide, note, { x: x + 18, y: y + 86, w: w - 36, h: 28, size: 13, color: C.text });
}

function bullets(slide, rows, x, y, w, size = 22) {
  rows.forEach((row, i) => {
    addShape(slide, { x, y: y + i * 54 + 8, w: 8, h: 8, fill: C.amber, line: "#00000000" });
    addText(slide, row, { x: x + 22, y: y + i * 54, w, h: 44, size, color: C.text });
  });
}

function bars(slide, rows, { x, y, w, h, valueKey, labelKey, color = C.blue, max = null }) {
  const m = max || Math.max(...rows.map((r) => r[valueKey] || 0), 1);
  rows.forEach((r, i) => {
    const yy = y + i * h;
    addText(slide, r[labelKey], { x, y: yy, w: 280, h: 28, size: 16, color: C.text });
    addShape(slide, { x: x + 300, y: yy + 3, w: 620, h: 22, fill: "#222a38", line: "#00000000" });
    addShape(slide, { x: x + 300, y: yy + 3, w: Math.max(4, (620 * (r[valueKey] || 0)) / m), h: 22, fill: color, line: "#00000000" });
    addText(slide, fmt(r[valueKey]), { x: x + 934, y: yy, w: 120, h: 28, size: 15, color: C.muted, align: "right" });
  });
}

function scatter(slide, rows, { x, y, w, h }) {
  addShape(slide, { x, y, w, h, fill: "#111722", line: C.line });
  addText(slide, "YouTube 百分位", { x: x + w - 150, y: y + h + 10, w: 140, h: 20, size: 12, color: C.muted, align: "right" });
  addText(slide, "Twitch 百分位", { x: x - 6, y: y - 28, w: 150, h: 20, size: 12, color: C.muted });
  [0.5, 0.9].forEach((p) => {
    addShape(slide, { x: x + w * p, y, w: 1, h, fill: C.line, line: "#00000000" });
    addShape(slide, { x, y: y + h * (1 - p), w, h: 1, fill: C.line, line: "#00000000" });
  });
  rows.slice(0, 260).forEach((r) => {
    const px = x + (w * r.yt_pct) / 100;
    const py = y + h - (h * r.tw_pct) / 100;
    const fill = r.yt_pct >= 90 && r.tw_pct >= 90 ? C.amber : r.home === "Twitch" ? C.purple : r.home === "YT" ? C.blue : C.green;
    addShape(slide, { x: px - 3, y: py - 3, w: 6, h: 6, fill, line: "#00000000", geometry: "ellipse" });
  });
}

const p = Presentation.create();

{
  const s = baseSlide(p, "LIVE BRIEFING DRAFT", "台灣 VTuber 產業數據直播簡報");
  addText(s, "從 2022 到 2026：誰活著、誰長大、誰跨平台、誰站上梯隊", {
    x: 54,
    y: 170,
    w: 760,
    h: 60,
    size: 24,
    color: C.muted,
  });
  metric(s, "追蹤台V", fmt(cur.tracked_channels), `近期活躍 ${fmt(cur.recently_active_any)}`, 54, 300, 220, C.green);
  metric(s, "雙棲頻道", fmt(dual.length), `${fmt(topDual)} 個雙平台前 10%`, 300, 300, 220, C.purple);
  metric(s, "前10集中度", `${ratioPct(cur.yt_top10_share * 100)}`, `訂閱中位 ${fmt(cur.yt_subs_median)}`, 546, 300, 220, C.amber);
  metric(s, "開台尖峰", `${ytPeakHour} 時`, "開台時間，不是同接", 792, 300, 220, C.blue);
}

{
  const s = baseSlide(p, "01｜市場規模", "台V不是小圈圈，是一個可量測的長尾市場");
  metric(s, "追蹤頻道", fmt(cur.tracked_channels), "track-list 最新 settled snapshot", 70, 170, 250, C.green);
  metric(s, "近期活躍", fmt(cur.recently_active_any), `活躍率 ${cur.activation_rate}%`, 350, 170, 250, C.blue);
  metric(s, "YT訂閱中位", fmt(cur.yt_subs_median), "長尾市場的中心點", 630, 170, 250, C.amber);
  metric(s, "國籍前三", natTop, "以 current cohort 統計", 910, 170, 250, C.purple);
  bullets(s, ["直播鉤子：不要只看頭部大V，真正的產業形狀在長尾。", "本資料可講規模、活躍、平台、團體，但不能講 SC 金流或真同接。"], 80, 360, 1060, 23);
}

{
  const s = baseSlide(p, "02｜平台分工", "雙棲不是把兩個數字相加，而是看平台內站位");
  metric(s, "雙棲頻道", fmt(dual.length), "YT 有訂閱且 Twitch 有追隨", 70, 170, 260, C.purple);
  metric(s, "雙前10%", fmt(topDual), "兩平台都站進前段班", 360, 170, 260, C.amber);
  scatter(s, dual, { x: 690, y: 155, w: 450, h: 420 });
  bullets(s, topDualRows.slice(0, 4).map((r) => `${r.n}：YT ${r.yt_pct}% / Twitch ${r.tw_pct}%`), 80, 360, 560, 20);
}

{
  const s = baseSlide(p, "03｜集中與長尾", "大者恆大，但長尾仍是台V產業的主要地形");
  metric(s, "前10大佔比", `${ratioPct(cur.yt_top10_share * 100)}`, "全體訂閱集中度", 70, 170, 280, C.amber);
  metric(s, "訂閱中位", fmt(cur.yt_subs_median), "典型頻道的尺度", 380, 170, 280, C.green);
  bars(s, topSubs, { x: 80, y: 340, w: 1000, h: 38, valueKey: "s", labelKey: "n", color: C.blue });
}

{
  const s = baseSlide(p, "04｜廠牌梯隊", "看總訂閱也要看每人中位，否則會誤讀團體規模");
  metric(s, "可繪製團體", "235", "378 個 group name 中符合條件者", 70, 170, 260, C.green);
  bars(s, agencyStats, { x: 80, y: 310, w: 1000, h: 38, valueKey: "total", labelKey: "gn", color: C.purple });
  bullets(s, ["右上角是總量與單人成績都強的梯隊。", "成員多不必然等於平均強，直播時可接 dashboard 的廠牌梯隊圖。"], 700, 172, 470, 20);
}

{
  const s = baseSlide(p, "05｜成長與生命週期", "第二年撞牆與長期存活要分開講");
  metric(s, "12個月中位", `${growth.lifecycle.median[12]}x`, "相對初始訂閱", 70, 170, 250, C.green);
  metric(s, "12個月p75", `${growth.lifecycle.p75[12]}x`, "上四分位成長", 350, 170, 250, C.amber);
  metric(s, "資料警語", "右設限", "Active 不是永遠存活", 630, 170, 250, C.red);
  bullets(s, ["存活曲線是 proxy：畢業、停更、改名、清單清理會混在一起。", "直播說法要避免把 track-list 消失直接講成自然死亡。", "2023 清單清理與早期出道截斷仍需要保留警語。"], 90, 350, 1000, 22);
}

{
  const s = baseSlide(p, "06｜作息生態", "這能講開台時間，不能冒充觀眾同接");
  metric(s, "YT清洗直播", fmt(streams.yt.cleaned_streams), "7/7 星期覆蓋", 70, 170, 250, C.blue);
  metric(s, "Twitch清洗直播", fmt(streams.tw.cleaned_streams), "Twitch 樣本較少", 350, 170, 250, C.purple);
  metric(s, "YT尖峰", `${ytPeakHour} 時`, "台灣時間", 630, 170, 250, C.green);
  metric(s, "Twitch尖峰", `${twPeakHour} 時`, "台灣時間", 910, 170, 250, C.amber);
  bullets(s, ["已排除 1970、未來排程、長掛待機室等污染。", "最右月份仍可能是進行中，不要拿它和完整月份硬比。"], 90, 360, 1000, 24);
}

{
  const s = baseSlide(p, "07｜定位體檢", "用百分位講位置，比直接比絕對值更適合小V");
  metric(s, "定位頻道", fmt(channels.length), "可用最新 snapshot", 70, 170, 250, C.green);
  metric(s, "頭像整合", fmt(channels.filter((c) => c.img).length), "排行榜/相似頻道可視化", 350, 170, 250, C.blue);
  metric(s, "蕾妮案例", "0.0%", "r=0 黏著度合法顯示", 630, 170, 250, C.amber);
  bullets(s, ["0 不是缺資料：近期中位觀看為 0 時，黏著度就是 0。", "名次改用嚴格大於者計算，不再出現第 n+1/n。", "體檢卡適合直播互動：輸入頻道，看訂閱、Twitch、黏著、爆紅、規律。"], 90, 350, 1000, 22);
}

{
  const s = baseSlide(p, "08｜收尾口徑", "哪些結論可以講，哪些一定要加警語");
  bullets(
    s,
    [
      "可以講：追蹤規模、近期活躍、平台內百分位、團體梯隊、開台時間分布。",
      "要加警語：黏著度是 VOD proxy；開台時間不是同接；事件 delta 未扣自然成長。",
      "待確認：雙棲定義目前是 YT 有訂閱且 Twitch 有追隨，若收嚴會少於 1,945。",
      "下一步：若要正式上台，可從這份初稿再做圖表截圖與逐頁視覺強化。",
    ],
    90,
    170,
    1050,
    25,
  );
}

await fs.mkdir(ACT, { recursive: true });
const pptx = await PresentationFile.exportPptx(p);
await pptx.save(OUT);
console.log(`wrote ${OUT}`);
