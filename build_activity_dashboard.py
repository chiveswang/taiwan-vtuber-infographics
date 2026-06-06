import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
ACT = ROOT / "outputs" / "activity"

rows = list(csv.DictReader(open(ACT / "quarterly_activity.csv", encoding="utf-8-sig")))
meta = json.loads((ACT / "quarterly_activity.json").read_text(encoding="utf-8"))
snap = {s["quarter"]: s.get("snapshots", {}) for s in meta["series"]}

def i(v):
    try: return int(v)
    except: return None

data = []
for r in rows:
    q = r["quarter"]
    tracked = i(r["tracked_channels"]); active = i(r["recently_active_any"])
    rate = round(active/tracked*100,1) if tracked and active else None
    sd = snap.get(q, {})
    data.append({
        "q": q,
        "partial": r["partial"]=="True",
        "tracked": tracked,
        "active": active,
        "active_yt": i(r["recently_active_yt"]),
        "active_tw": i(r["recently_active_twitch"]),
        "rate": rate,
        "yt_subs": i(r["yt_subs_total"]),
        "tw_followers": i(r["twitch_followers_total"]),
        "yt_live": i(r["yt_live_streams"]),
        "yt_live_hosts": i(r["yt_live_hosts"]),
        "tw_live": i(r["tw_live_streams"]),
        "topvideo_channels": i(r["topvideo_channels"]),
        "snap_basic": (sd.get("basic-data") or {}).get("snapshot_at",""),
        "snap_record": (sd.get("record") or {}).get("snapshot_at",""),
        "snap_yt_live": (sd.get("livestreams") or {}).get("snapshot_at",""),
        "snap_tw_live": (sd.get("twitch-livestreams") or {}).get("snapshot_at",""),
    })

DATA_JSON = json.dumps(data, ensure_ascii=False)
GEN = meta["generated_at"][:10]

HTML = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>台灣 VTuber 產業活躍度・季度演變</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{
  --bg:#0f1117; --panel:#181b24; --panel2:#1f2330; --line:#2a2f3d;
  --txt:#e8eaf0; --muted:#9aa3b5; --accent:#7c5cff; --yt:#ff5a5f; --tw:#a970ff;
  --green:#37d99a; --amber:#ffb454; --blue:#4aa8ff;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);
  font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif;line-height:1.5}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:26px;margin:0 0 4px}
.sub{color:var(--muted);font-size:14px;margin-bottom:4px}
.note{color:var(--amber);font-size:12.5px;background:rgba(255,180,84,.08);
  border:1px solid rgba(255,180,84,.25);border-radius:8px;padding:8px 12px;margin:14px 0 22px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px;margin-bottom:26px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi .label{color:var(--muted);font-size:12px;margin-bottom:6px}
.kpi .val{font-size:24px;font-weight:700}
.kpi .delta{font-size:12px;margin-top:5px}
.up{color:var(--green)} .down{color:var(--yt)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px 10px}
.card h3{margin:0 0 2px;font-size:15px}
.card .desc{color:var(--muted);font-size:12px;margin:0 0 10px}
.full{grid-column:1/-1}
.chartbox{position:relative;height:300px}
.controls{display:flex;align-items:center;gap:10px;margin:6px 0 18px;font-size:13px;color:var(--muted)}
.controls label{cursor:pointer;user-select:none}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:6px}
th,td{padding:6px 8px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:var(--panel)}
thead th{color:var(--muted);font-weight:600;position:sticky;top:0;background:var(--panel)}
.tablewrap{overflow:auto;max-height:430px;border:1px solid var(--line);border-radius:12px}
tr.partial td{color:var(--amber)}
.footer{color:var(--muted);font-size:11.5px;margin-top:24px;border-top:1px solid var(--line);padding-top:14px}
.tag{display:inline-block;font-size:10.5px;padding:1px 7px;border-radius:20px;border:1px solid var(--line);color:var(--muted);margin-left:6px;vertical-align:middle}
</style>
</head>
<body>
<div class="wrap">
  <h1>台灣 VTuber 產業活躍度・季度演變</h1>
  <div class="sub">資料來源 TaiwanVtuberData（archive + current）・每季抓月底結算 snapshot・最新資料 __GEN__</div>
  <div class="note">備註：每季取該季月底（3/6/9/12 月最後一筆）snapshot。<b>2026-06 為進行中季度（資料截至 2026-06-06），未結算</b>，圖表中以虛線標示、表格以橘色標記，僅供參考。直播數為「月底當下同時在線」的瞬時值，受抓取時段影響；早期（2021）僅有 record 資料且筆數稀疏，趨勢以 2022 年後為主。</div>

  <div class="kpis" id="kpis"></div>

  <div class="controls">
    <label><input type="checkbox" id="togglePartial" checked> 顯示未結算季度 (2026-06)</label>
  </div>

  <div class="grid">
    <div class="card"><h3>追蹤頻道數 vs 近期活躍創作者</h3><p class="desc">產業規模（被追蹤的頻道）對比實際近期有產出的創作者數</p><div class="chartbox"><canvas id="c1"></canvas></div></div>
    <div class="card"><h3>活躍率</h3><p class="desc">近期活躍創作者 ÷ 追蹤頻道數（%）。反映名單中真正在活動的比例</p><div class="chartbox"><canvas id="c2"></canvas></div></div>
    <div class="card"><h3>近期活躍創作者・平台組成</h3><p class="desc">近期有觀看數的創作者，依 YouTube / Twitch 分（可重疊）</p><div class="chartbox"><canvas id="c3"></canvas></div></div>
    <div class="card"><h3>月底直播活動（瞬時）</h3><p class="desc">月底 snapshot 當下的 YouTube 開台數/開台人數與 Twitch 在線直播數</p><div class="chartbox"><canvas id="c4"></canvas></div></div>
    <div class="card full"><h3>觀眾基數成長（規模背景）</h3><p class="desc">YouTube 訂閱總數與 Twitch 追隨者總數，作為活躍度的規模對照</p><div class="chartbox" style="height:320px"><canvas id="c5"></canvas></div></div>
  </div>

  <div class="card full" style="margin-top:18px">
    <h3>季度資料表</h3>
    <div class="tablewrap"><table id="tbl"></table></div>
  </div>

  <div class="footer">
    指標定義：<b>追蹤頻道數</b>=basic-data 內有資料的 VTuber 數；<b>近期活躍</b>=record 中「近期中位觀看數&gt;0」（跨 schema 版本對齊 YouTube / Twitch 近期中位觀看欄位）；<b>直播</b>=該月底 livestreams / twitch-livestreams snapshot 的列數與不重複頻道。basic-data 始於 2022-03、YouTube 直播始於 2022-06、Twitch 直播始於 2023-09。產生時間 __GEN__。
  </div>
</div>

<script>
const RAW = __DATA__;
const fmt = n => n==null ? "—" : n.toLocaleString("en-US");
const COL = {tracked:"#4aa8ff",active:"#37d99a",rate:"#ffb454",yt:"#ff5a5f",tw:"#a970ff",ytlive:"#4aa8ff",twlive:"#a970ff",subs:"#ff5a5f",fol:"#a970ff"};
let charts=[];

function render(includePartial){
  const D = RAW.filter(d=>includePartial || !d.partial);
  const labels = D.map(d=>d.q);
  const partialIdx = D.map((d,k)=>d.partial?k:-1).filter(k=>k>=0);
  charts.forEach(c=>c.destroy()); charts=[];

  // KPIs: compare latest settled (2026-03) vs 4 quarters earlier (2025-03)
  const settled = RAW.filter(d=>!d.partial);
  const cur = settled[settled.length-1];
  const prevYoY = settled[settled.length-5] || settled[0];
  const base22 = RAW.find(d=>d.q==="2022-03");
  function pct(a,b){ if(a==null||b==null||!b) return ""; const x=((a-b)/b*100); return (x>=0?"▲ +":"▼ ")+x.toFixed(1)+"% YoY"; }
  const kpis=[
    {label:"追蹤頻道數", val:fmt(cur.tracked), d:pct(cur.tracked,prevYoY.tracked), q:cur.q},
    {label:"近期活躍創作者", val:fmt(cur.active), d:pct(cur.active,prevYoY.active), q:cur.q},
    {label:"活躍率", val:cur.rate+"%", d:(cur.rate-prevYoY.rate>=0?"▲ +":"▼ ")+(cur.rate-prevYoY.rate).toFixed(1)+" pp YoY", q:cur.q},
    {label:"Twitch 活躍佔比", val:Math.round(cur.active_tw/cur.active*100)+"%", d:"2022Q1 為 "+Math.round(base22.active_tw/base22.active*100)+"%", q:cur.q},
    {label:"月底 YouTube 開台人數", val:fmt(cur.yt_live_hosts), d:pct(cur.yt_live_hosts,prevYoY.yt_live_hosts), q:cur.q},
    {label:"月底 Twitch 在線直播", val:fmt(cur.tw_live), d:pct(cur.tw_live,prevYoY.tw_live), q:cur.q},
  ];
  document.getElementById("kpis").innerHTML = kpis.map(k=>{
    const cls = k.d.startsWith("▲")||k.d.startsWith("▲ +")?"up":(k.d.startsWith("▼")?"down":"");
    return `<div class="kpi"><div class="label">${k.label} <span class="tag">${k.q}</span></div><div class="val">${k.val}</div><div class="delta ${cls}">${k.d}</div></div>`;
  }).join("");

  const gridc="#2a2f3d", tick="#9aa3b5";
  const baseOpts=(extra={})=>({responsive:true,maintainAspectRatio:false,interaction:{mode:"index",intersect:false},
    plugins:{legend:{labels:{color:tick,boxWidth:12,font:{size:11}}},tooltip:{callbacks:{}}},
    scales:Object.assign({x:{ticks:{color:tick,maxRotation:0,autoSkip:true,font:{size:10}},grid:{color:gridc}},
      y:{ticks:{color:tick,font:{size:10}},grid:{color:gridc}}},extra)});
  const dash = ctx => partialIdx.includes(ctx.p1DataIndex)?[5,4]:undefined;
  const seg = {borderDash:c=>dash(c)};

  charts.push(new Chart(c1,{type:"line",data:{labels,datasets:[
    {label:"追蹤頻道數",data:D.map(d=>d.tracked),borderColor:COL.tracked,backgroundColor:COL.tracked+"22",tension:.25,fill:true,segment:seg},
    {label:"近期活躍創作者",data:D.map(d=>d.active),borderColor:COL.active,backgroundColor:COL.active+"22",tension:.25,fill:true,segment:seg}
  ]},options:baseOpts()}));

  charts.push(new Chart(c2,{type:"line",data:{labels,datasets:[
    {label:"活躍率 %",data:D.map(d=>d.rate),borderColor:COL.rate,backgroundColor:COL.rate+"22",tension:.25,fill:true,segment:seg}
  ]},options:baseOpts({y:{ticks:{color:tick,callback:v=>v+"%"},grid:{color:gridc},suggestedMin:50,suggestedMax:90}})}));

  charts.push(new Chart(c3,{type:"line",data:{labels,datasets:[
    {label:"YouTube 近期活躍",data:D.map(d=>d.active_yt),borderColor:COL.yt,backgroundColor:COL.yt+"22",tension:.25,segment:seg},
    {label:"Twitch 近期活躍",data:D.map(d=>d.active_tw),borderColor:COL.tw,backgroundColor:COL.tw+"22",tension:.25,segment:seg}
  ]},options:baseOpts()}));

  charts.push(new Chart(c4,{type:"line",data:{labels,datasets:[
    {label:"YouTube 開台數",data:D.map(d=>d.yt_live),borderColor:COL.ytlive,tension:.25,segment:seg},
    {label:"YouTube 開台人數",data:D.map(d=>d.yt_live_hosts),borderColor:COL.green,borderDash:[3,3],tension:.25},
    {label:"Twitch 在線直播",data:D.map(d=>d.tw_live),borderColor:COL.twlive,tension:.25,segment:seg}
  ]},options:baseOpts()}));

  charts.push(new Chart(c5,{type:"line",data:{labels,datasets:[
    {label:"YouTube 訂閱總數",data:D.map(d=>d.yt_subs),borderColor:COL.subs,backgroundColor:COL.subs+"18",tension:.25,fill:true,yAxisID:"y",segment:seg},
    {label:"Twitch 追隨者總數",data:D.map(d=>d.tw_followers),borderColor:COL.fol,backgroundColor:COL.fol+"18",tension:.25,fill:true,yAxisID:"y",segment:seg}
  ]},options:baseOpts({y:{ticks:{color:tick,callback:v=>(v/1e6)+"M"},grid:{color:gridc}}})}));

  // table
  const cols=[["q","季度"],["tracked","追蹤頻道"],["active","近期活躍"],["rate","活躍率%"],["active_yt","YT活躍"],["active_tw","Twitch活躍"],["yt_live","YT開台"],["yt_live_hosts","YT開台人數"],["tw_live","Twitch直播"],["yt_subs","YT訂閱總數"],["tw_followers","Twitch追隨總數"]];
  let html="<thead><tr>"+cols.map(c=>`<th>${c[1]}</th>`).join("")+"</tr></thead><tbody>";
  RAW.forEach(d=>{ if(!includePartial&&d.partial)return;
    html+=`<tr class="${d.partial?'partial':''}">`+cols.map(c=>{
      let v=d[c[0]]; if(c[0]==="q")return `<td>${v}${d.partial?' *':''}</td>`;
      if(c[0]==="rate")return `<td>${v==null?'—':v+'%'}</td>`;
      return `<td>${fmt(v)}</td>`;}).join("")+"</tr>";
  });
  html+="</tbody>";
  document.getElementById("tbl").innerHTML=html;
}
render(true);
document.getElementById("togglePartial").addEventListener("change",e=>render(e.target.checked));
</script>
</body>
</html>"""

HTML = HTML.replace("__DATA__", DATA_JSON).replace("__GEN__", GEN)
out = ACT / "vtuber_activity_dashboard.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out, len(HTML), "bytes")
