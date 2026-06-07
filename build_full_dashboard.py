import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
ACT = ROOT / "outputs" / "activity"
d = json.loads((ACT/"quarterly_full.json").read_text(encoding="utf-8"))
GEN = d["generated_at"][:10]
ACT_JSON = json.dumps(d["activity"], ensure_ascii=False)
COH_JSON = json.dumps(d["cohort"], ensure_ascii=False)
CONC_JSON = json.dumps(d.get("concentration", {}), ensure_ascii=False)
DIR_JSON = (ACT/"locate_directory.json").read_text(encoding="utf-8")
GROW_JSON = (ACT/"growth.json").read_text(encoding="utf-8")
EVT_JSON = (ACT/"events.json").read_text(encoding="utf-8")
stm_data = json.loads((ACT/"streaming.json").read_text(encoding="utf-8"))
if stm_data.get("note"):
    stm_data["note"] = "直播樣本已去除重複網址，並排除長時間待機室。"
STM_JSON = json.dumps(stm_data, ensure_ascii=False)
XPLAT_JSON = (ACT/"crossplatform.json").read_text(encoding="utf-8")

HTML = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>台灣 VTuber 產業活躍度・季度整合儀表板</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{--bg:#0f1117;--panel:#181b24;--line:#2a2f3d;--txt:#e8eaf0;--muted:#9aa3b5;
--accent:#7c5cff;--green:#37d99a;--amber:#ffb454;--blue:#4aa8ff;--red:#ff5a5f;--purple:#a970ff;--pink:#ff7eb6;--teal:#2dd4bf;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif;line-height:1.5}
a, a:link, a:visited{color:var(--blue);text-decoration:none}
a:hover{color:#7cc4ff;text-decoration:underline}
.wrap{max-width:1200px;margin:0 auto;padding:26px 20px 70px}
h1{font-size:25px;margin:0 0 3px}
.sub{color:var(--muted);font-size:13.5px}
.note{color:var(--amber);font-size:12px;background:rgba(255,180,84,.08);border:1px solid rgba(255,180,84,.22);border-radius:8px;padding:8px 12px;margin:13px 0 18px}
.tabs{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 16px}
.tab{background:var(--panel);border:1px solid var(--line);color:var(--muted);padding:8px 14px;border-radius:10px;cursor:pointer;font-size:13.5px}
.tab.on{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
.ctrl{display:flex;gap:14px;align-items:center;font-size:12.5px;color:var(--muted);margin-bottom:14px}
.ctrl label{cursor:pointer}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:11px;margin-bottom:20px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 15px}
.kpi .l{color:var(--muted);font-size:11.5px;margin-bottom:5px}
.kpi .v{font-size:22px;font-weight:700}
.kpi .d{font-size:11.5px;margin-top:4px}
.up{color:var(--green)}.down{color:var(--red)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:840px){.grid{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:15px 17px 9px}
.card h3{margin:0 0 2px;font-size:14.5px}
.card .desc{color:var(--muted);font-size:11.5px;margin:0 0 9px}
.full{grid-column:1/-1}
.box{position:relative;height:300px}
.box.tall{height:330px}
section{display:none}
section.on{display:block}
.tag{display:inline-block;font-size:10px;padding:1px 7px;border-radius:20px;border:1px solid var(--line);color:var(--muted);margin-left:5px}
.footer{color:var(--muted);font-size:11px;margin-top:22px;border-top:1px solid var(--line);padding-top:13px}
.insight{font-size:12.5px;color:#cfd6e6;background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;padding:10px 13px;margin-bottom:14px}
.locbar{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px}
@media(max-width:840px){.locbar{grid-template-columns:1fr}}
.locbar>div{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:12.5px;color:var(--muted)}
.locbar input{background:#0f1117;border:1px solid var(--line);color:var(--txt);border-radius:7px;padding:5px 8px;margin:5px 4px 0 0;font-size:12.5px}
.locbar input[type=number]{width:90px}
.locbar #locQ{width:230px}
.locbar button{background:var(--accent);border:none;color:#fff;border-radius:7px;padding:6px 11px;margin:5px 3px 0 0;cursor:pointer;font-size:12.5px}
.locbar button#locLive{background:#2a2f3d}
.muted{color:var(--muted)}
.faq-badge{font-size:11px;padding:2px 9px;border-radius:20px;font-weight:600;white-space:nowrap}
.faq-green{background:rgba(55,217,154,.15);color:var(--green);border:1px solid var(--green)}
.faq-amber{background:rgba(255,180,84,.15);color:var(--amber);border:1px solid var(--amber)}
.faq-card{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:13px 16px;margin-bottom:12px}
.faq-card h4{margin:0;font-size:14.5px}
.faq-line{font-size:13px;color:#cfd6e6;margin:7px 0 0}
.faq-meta{font-size:11.5px;color:var(--muted);margin:5px 0 0}
.faq-card a{color:var(--blue)}
.table{width:100%;border-collapse:collapse;font-size:12.5px}
.table th,.table td{border-bottom:1px solid var(--line);padding:7px 6px;text-align:left;vertical-align:top}
.table th{color:var(--muted);font-weight:600}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.chip{background:var(--panel);border:1px solid var(--line);color:var(--muted);border-radius:20px;padding:6px 11px;cursor:pointer;font-size:12.5px}
.chip.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.avatar{width:28px;height:28px;border-radius:50%;object-fit:cover;vertical-align:middle;margin-right:7px;background:#2a2f3d;border:1px solid var(--line)}
.story-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:14px 0}
.story-card{background:linear-gradient(180deg,#1d2330,#141923);border:1px solid var(--line);border-radius:8px;padding:16px;min-height:112px}
.story-card .l{color:var(--muted);font-size:12px}
.story-card .v{font-size:28px;font-weight:800;margin:8px 0;color:#fff}
.story-card .d{font-size:12.5px;line-height:1.45;color:var(--text)}
.chapter-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin:14px 0}
.chapter{background:#10141d;border:1px solid var(--line);border-radius:8px;padding:18px;min-height:170px}
.chapter .eyebrow{color:var(--rate);font-size:12px;font-weight:700}
.chapter h3{font-size:20px;margin:7px 0 10px}
.chapter .big{font-size:34px;font-weight:900;color:#fff;margin:8px 0}
.chapter p{color:var(--text);line-height:1.55;margin:0}
@media(max-width:1100px){.story-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:1100px){.chapter-grid{grid-template-columns:1fr}}
@media(max-width:720px){.story-grid{grid-template-columns:1fr}.story-card .v{font-size:24px}.chapter .big{font-size:27px}}
</style></head>
<body><div class="wrap">
<h1>台灣 VTuber 產業活躍度・季度整合儀表板</h1>
<div class="sub">資料來源 TaiwanVtuberData（archive + current）・統一以日曆季月底結算節點・最新資料 __GEN__</div>
<div class="note">所有指標皆以「季月底（3/6/9/12 月最後一份）資料截點」重算，與舊版 deck（取月初）數字會略有差異。<b>2026-06 為進行中季度（截至 2026-06-06），未結算</b>，圖以虛線、KPI 以最新已結算季 2026-03 為準。直播數為月底瞬時值，受抓取時段影響；2021 僅有近期數據且稀疏，趨勢以 2022 後為主。出道/畢業為現存追蹤名單之記載（含倖存者偏差）。</div>

<div class="tabs" id="tabs"></div>
<div class="ctrl"><label><input type="checkbox" id="tp" checked> 顯示未結算季度 2026-06</label></div>

<section id="s_overview">
  <div class="kpis" id="kpi_ov"></div>
  <div class="grid">
    <div class="card"><h3>追蹤頻道數 vs 近期活躍創作者</h3><p class="desc">產業規模對比實際近期有產出的創作者</p><div class="box"><canvas id="ov1"></canvas></div></div>
    <div class="card"><h3>活躍率</h3><p class="desc">近期活躍 ÷ 追蹤頻道（%）</p><div class="box"><canvas id="ov2"></canvas></div></div>
    <div class="card"><h3>近期活躍・平台組成</h3><p class="desc">YouTube / Twitch 近期活躍創作者（可重疊）</p><div class="box"><canvas id="ov3"></canvas></div></div>
    <div class="card"><h3>月底直播活動（瞬時）</h3><p class="desc">YouTube 開台數/人數、Twitch 在線直播</p><div class="box"><canvas id="ov4"></canvas></div></div>
  </div>
</section>

<section id="s_cohort">
  <div class="insight">出道潮在 2021Q3 達頂（單季 271 人），其後逐季放緩；畢業穩定約每季 15–27 人。累積淨活躍持續成長但增速明顯收斂 → 產業由擴張期進入成熟期。</div>
  <div class="kpis" id="kpi_co"></div>
  <div class="grid">
    <div class="card full"><h3>每季出道 vs 畢業</h3><p class="desc">新血進場與退役離場（人/季）</p><div class="box tall"><canvas id="co1"></canvas></div></div>
    <div class="card"><h3>累積淨活躍世代</h3><p class="desc">累積出道 − 累積畢業（由追蹤名單記載重建）</p><div class="box"><canvas id="co2"></canvas></div></div>
    <div class="card"><h3>單季淨增</h3><p class="desc">出道 − 畢業，看成長動能收斂</p><div class="box"><canvas id="co3"></canvas></div></div>
    <div class="card"><h3>出道世代・國籍組成</h3><p class="desc">每季新出道者的國籍佔比</p><div class="box"><canvas id="co4"></canvas></div></div>
    <div class="card"><h3>出道世代・團體 vs 個人</h3><p class="desc">新出道者是否屬於團體/企業勢</p><div class="box"><canvas id="co5"></canvas></div></div>
  </div>
</section>

<section id="s_conc">
  <div class="insight">頭部集中度（前 10 大訂閱佔比）由 2022Q1 的 44% 一路降到約 14%，觀看數集中度同步比較；同時訂閱中位數由 ~460 升到 ~1,450 → 長尾變厚。</div>
  <div class="grid">
    <div class="card"><h3>頭部集中度 top10 share</h3><p class="desc">前 10 大頻道訂閱數 ÷ 全體訂閱數</p><div class="box"><canvas id="cc1"></canvas></div></div>
    <div class="card"><h3>訂閱數 中位數 vs 前 10% 門檻</h3><p class="desc">典型創作者（中位）與前段頻道規模</p><div class="box"><canvas id="cc2"></canvas></div></div>
    <div class="card"><h3>近期觀看前 10% 門檻（熱度天花板）</h3><p class="desc">近期中位觀看的前段頻道門檻</p><div class="box"><canvas id="cc3"></canvas></div></div>
    <div class="card"><h3>熱門影片觀看天花板</h3><p class="desc">當季熱門影片資料的最高單片觀看數</p><div class="box"><canvas id="cc4"></canvas></div></div>
    <div class="card full"><h3>頭部集中度：訂閱 vs 觀看</h3><p class="desc">前 10 大頻道占全體訂閱 % 與占全體觀看 %；若兩線差距大，代表訂閱/觀看結構不同</p><div class="box tall"><canvas id="cc5"></canvas></div></div>
    <div class="card full"><h3>占比排行檢視</h3><p class="desc">切換訂閱、累計觀看或期間觀看數，查看特定頻道或不同前段門檻占全體的比例</p>
      <div class="locbar" style="margin:8px 0 12px">
        <div><b>觀看類型</b><br>
          <select id="concTime"><option value="month">月度</option><option value="quarter">季度</option><option value="year">年度</option></select>
          <select id="concPeriod"></select>
          <select id="concMetric"><option value="s">YouTube 訂閱</option><option value="v">累計觀看</option><option value="pv">期間觀看數</option></select>
          <select id="concScope">
            <option value="top10">前 10 名</option>
            <option value="top1">前 1%</option><option value="top5">前 5%</option><option value="top10p">前 10%</option>
            <option value="top20">前 20%</option><option value="top30">前 30%</option><option value="top40">前 40%</option><option value="top50">前 50%</option>
            <option value="channel">特定頻道</option>
          </select>
        </div>
        <div><b>特定頻道</b><br>
          <input id="concQ" list="concList" placeholder="頻道名稱 / UCxxxx / Twitch 名稱"><datalist id="concList"></datalist>
          <button id="concApply">套用</button><span id="concStatus" class="muted"></span>
        </div>
      </div>
      <div id="concSummary" class="kpis"></div>
      <div class="box tall"><canvas id="ccShare"></canvas></div>
      <div id="concTable"></div>
      <div class="card full" style="margin-top:14px">
        <h3>存量 vs 本期流量：特異值</h3>
        <p class="desc">X=訂閱數百分位，Y=期間觀看數百分位；只納入 Activity=Active 的頻道，找出沉睡大台、流量黑馬與注意力超配頻道</p>
        <div class="box tall"><canvas id="ccOutlier"></canvas></div>
        <div id="concOutlier"></div>
      </div>
    </div>
  </div>
</section>

<section id="s_pyr">
  <div class="insight">中段（1k–10k、10k–100k）持續變厚是主旋律；破 10 萬訂閱（mega）人數緩增但占比仍低，金字塔底部寬、塔尖薄。</div>
  <div class="grid">
    <div class="card full"><h3>訂閱級距金字塔（人數）</h3><p class="desc">&gt;100k / 10k–100k / 1k–10k / &lt;1k 各階層頻道數</p><div class="box tall"><canvas id="py1"></canvas></div></div>
    <div class="card full"><h3>訂閱級距・佔比</h3><p class="desc">各階層占有訂閱頻道的百分比</p><div class="box tall"><canvas id="py2"></canvas></div></div>
  </div>
</section>

<section id="s_content">
  <div class="insight">短影音（shorts）是近年最大內容變化：在熱門影片中的佔比由幾乎 0 升到約 1/5。直播內容仍以雜談/遊戲/歌回為主幹。</div>
  <div class="grid">
    <div class="card"><h3>熱門影片・內容類型組成</h3><p class="desc">熱門影片資料的標題分類佔比（shorts 暴衝）</p><div class="box tall"><canvas id="ct1"></canvas></div></div>
    <div class="card"><h3>YouTube 直播・內容類型組成</h3><p class="desc">月底開台標題分類佔比</p><div class="box tall"><canvas id="ct2"></canvas></div></div>
    <div class="card"><h3>國籍組成（現況）</h3><p class="desc">追蹤名單全體國籍分布</p><div class="box"><canvas id="ct3"></canvas></div></div>
    <div class="card"><h3>團體 vs 個人 / 活動狀態（現況）</h3><p class="desc">所屬團體與 Active/Graduated/Preparing</p><div class="box"><canvas id="ct4"></canvas></div></div>
  </div>
</section>

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

<section id="s_growth">
  <div class="insight">本頁把四年追蹤資料壓成月度縱貫視角：看頻道成長軌跡、出道後生命週期、標題事件後 14 天吸粉毛估，以及 YouTube 開台作息樣本。所有估算指標都保留限制說明。</div>
  <div class="locbar"><div><b>選一個頻道看它的軌跡（沿用名單）</b><br>
    <input id="gwQ" list="gwList" placeholder="頻道名稱 / UCxxxx"><datalist id="gwList"></datalist>
    <button id="gwFind">套用</button><button id="gwClear" style="background:#2a2f3d">清除</button>
    <div id="gwStatus" class="muted" style="margin-top:6px"></div></div></div>
  <div class="tabs" id="gwSub"></div>
  <div id="gw_traj"></div>
  <div id="gw_life"></div>
  <div id="gw_event"></div>
  <div id="gw_cross"></div>
  <div id="gw_sched"></div>
</section>

<section id="s_rank">
  <div class="insight">排行榜把 per-channel 指標翻成可探索的榜單。比率榜已加門檻過濾，避免小頻道用極端比例洗榜；點名稱可跳到「定位你自己」看體檢卡。</div>
  <div class="chips" id="rankChips"></div>
  <div class="locbar"><div><b>篩選</b><br>
    級距 <select id="rankTier"><option value="">全部</option><option>&gt;100k</option><option>10k–100k</option><option>1k–10k</option><option>&lt;1k</option></select>
    國籍 <select id="rankNat"><option value="">全部</option></select>
    類型 <select id="rankType"><option value="">全部</option><option value="1">團體勢</option><option value="0">個人勢</option></select>
    筆數 <select id="rankN"><option>15</option><option>30</option><option>50</option></select>
  </div></div>
  <div id="rankList"></div>
</section>

<section id="s_agency">
  <div class="insight">用 Group Name 聚合到團體層級。Group Name 是字串，含 1 人「團」或掛名團；因此同時看總訂閱與每人中位，避免只看總量誤讀。</div>
  <div class="locbar"><div><b>選團體 deep-dive</b><br><input id="agQ" list="agList" placeholder="團體名稱"><datalist id="agList"></datalist><button id="agFind">套用</button><div id="agStatus" class="muted" style="margin-top:6px"></div></div>
  <div><b>勢力表排序</b><br><select id="agSort"><option value="total">總訂閱</option><option value="median">每人中位</option><option value="members">成員數</option></select></div></div>
  <div id="agKpi"></div>
  <div class="grid"><div class="card full"><h3>廠牌勢力排名</h3><div id="agTable"></div></div>
  <div class="card full"><h3>廠牌梯隊圖</h3><p class="desc">X=總訂閱，Y=每人成員中位數，點大小=成員數；右上是總量與單人成績都強的團體。</p><div class="box tall"><canvas id="agTier"></canvas></div></div>
  <div class="card"><h3>團體 vs 個人</h3><div class="box"><canvas id="agCmp"></canvas></div></div>
  <div class="card"><h3>團體規模分布</h3><div class="box"><canvas id="agSize"></canvas></div></div>
  <div class="card full"><h3>單一團體 deep-dive</h3><div id="agDeep"></div></div></div>
</section>

<section id="s_report">
  <div class="insight">自動把各分頁關鍵數字串成一篇年度產業報告。數字即時由內嵌資料生成，可複製全文。</div>
  <div class="locbar"><div><b>年度</b><br><select id="repYear"></select><button id="repCopy">複製全文</button><span id="repStatus" class="muted"></span></div></div>
  <div id="reportBody"></div>
  <details class="footer"><summary>資料說明與警語</summary>數字為自動從資料生成；追蹤名單含倖存者偏差。黏著度、事件淨增長、作息皆為估算指標或取樣統計。本資料源不含 SC 金流、即時同接、互動率、剪輯頻道。</details>
</section>

<section id="s_locate">
  <div class="insight">輸入你的頻道（YouTube 頻道ID UCxxxx / Twitch 名稱 / 直接打名稱搜尋）或純數字，看你落在全體台V分布的哪個位置。預設用內建最新資料截點（__GEN__）；按「更新到最新」會直接從公開 GitHub 抓即時數據（不需金鑰，失敗會自動退回內建）。</div>
  <div class="locbar">
    <div><b>思路A・頻道查詢（對追蹤名單）</b><br>
      <input id="locQ" list="locList" placeholder="頻道名稱 / UCxxxx / twitch名稱"><datalist id="locList"></datalist>
      <button id="locFind">定位</button><button id="locLive">更新到最新(GitHub)</button>
      <div id="locStatus" class="muted" style="margin-top:6px"></div></div>
    <div><b>思路B・純數字</b><br>
      YT訂閱 <input id="numSubs" type="number" min="0">　Twitch追隨 <input id="numFol" type="number" min="0"><br>
      近期中位觀看 <input id="numRec" type="number" min="0">　出道年 <input id="numDebut" type="number" min="2018" max="2026" placeholder="如2022" style="width:90px">
      類型 <select id="numType"><option value="">未指定</option><option value="1">團體勢</option><option value="0">個人勢</option></select> <button id="numGo">定位</button></div>
  </div>
  <div id="locHealth"></div>
  <div id="locSimilar"></div>
  <div id="locBrief"></div>
  <div class="kpis" id="kpi_loc"></div>
  <div class="grid">
    <div class="card"><h3>多指標雷達（百分位）</h3><p class="desc">訂閱/累計觀看/Twitch/近期熱度/爆紅力/黏著度/成長動能/開台規律，越外圈越強</p><div class="box tall"><canvas id="lc3"></canvas></div></div>
    <div class="card"><h3>你的訂閱級距</h3><p class="desc">綠色為你所在的級距</p><div class="box tall"><canvas id="lc2"></canvas></div></div>
    <div class="card full"><h3>你在訂閱排名曲線的位置</h3><p class="desc">全體台V訂閱由高到低（log），綠色菱形是你</p><div class="box tall"><canvas id="lc1"></canvas></div></div>
    <div class="card full"><h3>分組百分位（訂閱）</h3><p class="desc">在不同比較圈裡你贏過多少％：全體 / 同級距 / 同國籍 / 同屆出道</p><div class="box"><canvas id="lc4"></canvas></div></div>
  </div>
</section>
<div class="footer" id="ft"></div>
</div>

<script>
const ACT = __ACT__;
const COH = __COH__;
const CONC = __CONC__;
const DIR = __DIR__;
const GROW = __GROW__;
const EVT = __EVT__;
const STM = __STM__;
const XPLAT = __XPLAT__;
const fmt = n => n==null?"—":n.toLocaleString("en-US");
const C = {tracked:"#4aa8ff",active:"#37d99a",rate:"#ffb454",amber:"#ffb454",yt:"#ff5a5f",tw:"#a970ff",green:"#37d99a",
  debut:"#37d99a",grad:"#ff5a5f",cum:"#7c5cff",blue:"#4aa8ff"};
const BUCKETS=["game","chat","singing","shorts","asmr","collab","announcement","other"];
const BCOL={game:"#4aa8ff",chat:"#37d99a",singing:"#ff7eb6",shorts:"#ffb454",asmr:"#a970ff",collab:"#2dd4bf",announcement:"#ff5a5f",other:"#5b6377"};
const NAT=["TW","HK","MY","JP","OTHER"]; const NCOL={TW:"#4aa8ff",HK:"#ff5a5f",MY:"#ffb454",JP:"#a970ff",OTHER:"#5b6377"};
const TICK="#9aa3b5", GRID="#2a2f3d";
let store={}; let built={};

function opts(extra={},stacked=false,pct=false){
  return {responsive:true,maintainAspectRatio:false,interaction:{mode:"index",intersect:false},
    plugins:{legend:{labels:{color:TICK,boxWidth:11,font:{size:10.5}}},
      tooltip:{callbacks: pct?{label:c=>c.dataset.label+": "+c.parsed.y.toFixed(1)+"%"}:{}}},
    scales:Object.assign({x:{stacked,ticks:{color:TICK,maxRotation:0,autoSkip:true,font:{size:9.5}},grid:{color:GRID}},
      y:{stacked,ticks:{color:TICK,font:{size:9.5},callback:pct?(v=>v+"%"):undefined},grid:{color:GRID},max:pct?100:undefined}},extra)};
}
function seg(partialIdx){return {borderDash:c=>partialIdx.includes(c.p1DataIndex)?[5,4]:undefined};}
function pctStack(rows,key){ // rows: array with buckets dict at row[key]
  return rows.map(r=>{const b=r[key]||{};const tot=Object.values(b).reduce((a,x)=>a+x,0)||1;
    const o={}; BUCKETS.forEach(k=>o[k]=+(((b[k]||0)/tot*100).toFixed(1))); return o;});
}

function getAct(inclP){return ACT.filter(d=>inclP||!d.partial);}
function getCoh(inclP){return COH.series.filter(d=>inclP||!d.partial);}

function kpis(el,arr){document.getElementById(el).innerHTML=arr.map(k=>{
  const cls=k.d&&k.d[0]==="▲"?"up":(k.d&&k.d[0]==="▼"?"down":"");
  return `<div class="kpi"><div class="l">${k.l} <span class="tag">${k.q||''}</span></div><div class="v">${k.v}</div><div class="d ${cls}">${k.d||''}</div></div>`;}).join("");}
function yoy(a,b){if(a==null||b==null||!b)return"";const x=(a-b)/b*100;return (x>=0?"▲ +":"▼ ")+x.toFixed(1)+"% YoY";}

function buildOverview(inclP){
  const D=getAct(inclP),L=D.map(d=>d.quarter),P=D.map((d,i)=>d.partial?i:-1).filter(i=>i>=0);
  const settled=ACT.filter(d=>!d.partial),cur=settled[settled.length-1],pv=settled[settled.length-5];
  kpis("kpi_ov",[
    {l:"追蹤頻道數",v:fmt(cur.tracked_channels),d:yoy(cur.tracked_channels,pv.tracked_channels),q:cur.quarter},
    {l:"近期活躍創作者",v:fmt(cur.recently_active_any),d:yoy(cur.recently_active_any,pv.recently_active_any),q:cur.quarter},
    {l:"活躍率",v:cur.activation_rate+"%",d:(cur.activation_rate-pv.activation_rate>=0?"▲ +":"▼ ")+(cur.activation_rate-pv.activation_rate).toFixed(1)+" pp",q:cur.quarter},
    {l:"Twitch 活躍佔比",v:Math.round(cur.recently_active_twitch/cur.recently_active_any*100)+"%",d:"YT "+Math.round(cur.recently_active_yt/cur.recently_active_any*100)+"%",q:cur.quarter},
    {l:"月底 YT 開台人數",v:fmt(cur.yt_live_hosts),d:yoy(cur.yt_live_hosts,pv.yt_live_hosts),q:cur.quarter},
    {l:"月底 Twitch 直播",v:fmt(cur.tw_live_streams),d:yoy(cur.tw_live_streams,pv.tw_live_streams),q:cur.quarter},
  ]);
  const s=seg(P);
  new Chart(ov1,{type:"line",data:{labels:L,datasets:[
    {label:"追蹤頻道",data:D.map(d=>d.tracked_channels),borderColor:C.tracked,backgroundColor:C.tracked+"22",fill:true,tension:.25,segment:s},
    {label:"近期活躍",data:D.map(d=>d.recently_active_any),borderColor:C.active,backgroundColor:C.active+"22",fill:true,tension:.25,segment:s}]},options:opts()});
  new Chart(ov2,{type:"line",data:{labels:L,datasets:[{label:"活躍率%",data:D.map(d=>d.activation_rate),borderColor:C.rate,backgroundColor:C.rate+"22",fill:true,tension:.25,segment:s}]},options:opts({y:{ticks:{color:TICK,callback:v=>v+"%"},grid:{color:GRID},suggestedMin:55,suggestedMax:80}})});
  new Chart(ov3,{type:"line",data:{labels:L,datasets:[
    {label:"YouTube",data:D.map(d=>d.recently_active_yt),borderColor:C.yt,tension:.25,segment:s},
    {label:"Twitch",data:D.map(d=>d.recently_active_twitch),borderColor:C.tw,tension:.25,segment:s}]},options:opts()});
  new Chart(ov4,{type:"line",data:{labels:L,datasets:[
    {label:"YT 開台數",data:D.map(d=>d.yt_live_streams),borderColor:C.blue,tension:.25,segment:s},
    {label:"YT 開台人數",data:D.map(d=>d.yt_live_hosts),borderColor:C.green,borderDash:[3,3],tension:.25},
    {label:"Twitch 直播",data:D.map(d=>d.tw_live_streams),borderColor:C.tw,tension:.25,segment:s}]},options:opts()});
}

function buildCohort(inclP){
  const D=getCoh(inclP),L=D.map(d=>d.quarter),P=D.map((d,i)=>d.partial?i:-1).filter(i=>i>=0);
  const settled=COH.series.filter(d=>!d.partial),cur=settled[settled.length-1];
  const peak=COH.series.reduce((a,b)=>b.debuts>a.debuts?b:a);
  kpis("kpi_co",[
    {l:"最新季出道",v:fmt(cur.debuts),d:"高峰 "+peak.debuts+" ("+peak.quarter+")",q:cur.quarter},
    {l:"最新季畢業",v:fmt(cur.graduations),q:cur.quarter},
    {l:"累積淨活躍",v:fmt(cur.cumulative_active),q:cur.quarter},
    {l:"現存名單總數",v:fmt(COH.current.total)},
    {l:"Active / Graduated",v:fmt(COH.current.activity.Active)+" / "+fmt(COH.current.activity.Graduated)},
    {l:"團體 : 個人",v:fmt(COH.current.group_split.group)+" : "+fmt(COH.current.group_split.indie)},
  ]);
  const s=seg(P);
  new Chart(co1,{type:"bar",data:{labels:L,datasets:[
    {label:"出道",data:D.map(d=>d.debuts),backgroundColor:C.debut+"cc"},
    {label:"畢業",data:D.map(d=>-d.graduations),backgroundColor:C.grad+"cc"}]},
    options:opts({y:{ticks:{color:TICK,callback:v=>Math.abs(v)},grid:{color:GRID}}})});
  new Chart(co2,{type:"line",data:{labels:L,datasets:[{label:"累積淨活躍",data:D.map(d=>d.cumulative_active),borderColor:C.cum,backgroundColor:C.cum+"22",fill:true,tension:.25,segment:s}]},options:opts()});
  new Chart(co3,{type:"bar",data:{labels:L,datasets:[{label:"單季淨增",data:D.map(d=>d.net),backgroundColor:D.map(d=>d.net>=0?C.green+"cc":C.grad+"cc")}]},options:opts()});
  const natpct=D.map(d=>{const t=Object.values(d.nat||{}).reduce((a,x)=>a+x,0)||1;const o={};NAT.forEach(k=>o[k]=+(((d.nat&&d.nat[k]||0)/t*100).toFixed(1)));return o;});
  new Chart(co4,{type:"bar",data:{labels:L,datasets:NAT.map(k=>({label:k,data:natpct.map(x=>x[k]),backgroundColor:NCOL[k]}))},options:opts({},true,true)});
  const grppct=D.map(d=>{const t=(d.grp&&(d.grp.group||0)+(d.grp.indie||0))||1;return{group:+(((d.grp&&d.grp.group||0)/t*100).toFixed(1)),indie:+(((d.grp&&d.grp.indie||0)/t*100).toFixed(1))};});
  new Chart(co5,{type:"bar",data:{labels:L,datasets:[
    {label:"團體",data:grppct.map(x=>x.group),backgroundColor:C.cum},
    {label:"個人",data:grppct.map(x=>x.indie),backgroundColor:"#5b6377"}]},options:opts({},true,true)});
}

function buildConc(inclP){
  const D=getAct(inclP).filter(d=>d.yt_top10_share!=null),L=D.map(d=>d.quarter),P=D.map((d,i)=>d.partial?i:-1).filter(i=>i>=0);
  const s=seg(P);
  new Chart(cc1,{type:"line",data:{labels:L,datasets:[{label:"top10 share",data:D.map(d=>+(d.yt_top10_share*100).toFixed(1)),borderColor:C.rate,backgroundColor:C.rate+"22",fill:true,tension:.25,segment:s}]},options:opts({y:{ticks:{color:TICK,callback:v=>v+"%"},grid:{color:GRID}}})});
  new Chart(cc2,{type:"line",data:{labels:L,datasets:[
    {label:"訂閱中位數",data:D.map(d=>d.yt_subs_median),borderColor:C.green,tension:.25,segment:s},
    {label:"訂閱前 10% 門檻",data:D.map(d=>d.yt_subs_p90),borderColor:C.blue,tension:.25,segment:s,yAxisID:"y1"}]},
    options:opts({y:{ticks:{color:TICK},grid:{color:GRID}},y1:{position:"right",ticks:{color:TICK},grid:{drawOnChartArea:false}}})});
  new Chart(cc3,{type:"line",data:{labels:L,datasets:[{label:"近期觀看前 10% 門檻",data:D.map(d=>d.recent_yt_p90),borderColor:C.purple||"#a970ff",backgroundColor:"#a970ff22",fill:true,tension:.25,segment:s}]},options:opts()});
  new Chart(cc4,{type:"line",data:{labels:L,datasets:[{label:"最高單片觀看",data:D.map(d=>d.topvid_view_max),borderColor:C.yt,backgroundColor:C.yt+"22",fill:true,tension:.25,segment:s}]},options:opts({y:{ticks:{color:TICK,callback:v=>(v/1e6).toFixed(1)+"M"},grid:{color:GRID}}})});
  const Dv=getAct(inclP).filter(d=>d.yt_view_top10_share!=null),Lv=Dv.map(d=>d.quarter);
  const sv=seg(Dv.map((d,i)=>d.partial?i:-1).filter(i=>i>=0));
  new Chart(cc5,{type:"line",data:{labels:Lv,datasets:[
    {label:"訂閱 top10 share",data:Dv.map(d=>+(d.yt_top10_share*100).toFixed(1)),borderColor:C.rate,tension:.25,segment:sv},
    {label:"觀看 top10 share",data:Dv.map(d=>+(d.yt_view_top10_share*100).toFixed(1)),borderColor:C.blue,tension:.25,segment:sv}]},
    options:opts({y:{ticks:{color:TICK,callback:v=>v+"%"},grid:{color:GRID}}})});
  const timeEl=document.getElementById("concTime"), periodEl=document.getElementById("concPeriod"), metricEl=document.getElementById("concMetric"), scopeEl=document.getElementById("concScope"), qEl=document.getElementById("concQ"), stEl=document.getElementById("concStatus");
  const listEl=document.getElementById("concList"); if(listEl)listEl.innerHTML=DIRDATA.channels.filter(c=>c.n).slice(0,4000).map(c=>`<option value="${escHtml(c.n)}">`).join("");
  const labelOf={s:"YouTube 訂閱",v:"累計觀看",pv:"期間觀看數"}, unitOf={s:"訂閱",v:"累計觀看",pv:"期間觀看數"};
  function periods(){return CONC[timeEl.value]||[];}
  function fillPeriods(){const ps=periods();periodEl.innerHTML=ps.map((p,i)=>`<option value="${i}">${p.label}</option>`).join("");periodEl.value=String(Math.max(0,ps.length-1));}
  function topCount(scope,n){if(scope==="top10")return Math.min(10,n);const p={top1:.01,top5:.05,top10p:.10,top20:.20,top30:.30,top40:.40,top50:.50}[scope]||0;return Math.max(1,Math.ceil(n*p));}
  function pctRank(sorted,v){if(v==null||!isFinite(v)||!sorted.length)return null;let lo=0,hi=sorted.length;while(lo<hi){const m=(lo+hi)>>1;if(sorted[m]<v)lo=m+1;else hi=m;}return +(lo/sorted.length*100).toFixed(1);}
  function renderOutliers(rec){
    if(store.ccOutlier){store.ccOutlier.destroy();store.ccOutlier=null;}
    const rows=(rec.channels||[]).filter(c=>c.id&&c.ac==="Active"&&c.s>0&&c.pv!=null&&isFinite(c.pv));
    const subs=rows.map(c=>c.s).sort((a,b)=>a-b), flows=rows.map(c=>c.pv).sort((a,b)=>a-b);
    const totalS=rows.reduce((a,c)=>a+c.s,0), totalPv=rows.reduce((a,c)=>a+c.pv,0);
    const pts=rows.map(c=>{const sp=pctRank(subs,c.s), fp=pctRank(flows,c.pv), fps=c.pv/c.s, fpv=c.v?c.pv/c.v:null, shareRatio=(totalS&&totalPv)?((c.pv/totalPv)/(c.s/totalS)):null;return Object.assign({},c,{x:sp,y:fp,fps,fpv,shareRatio});}).filter(c=>c.x!=null&&c.y!=null);
    store.ccOutlier=new Chart(document.getElementById("ccOutlier"),{type:"scatter",data:{datasets:[{label:"頻道",data:pts,backgroundColor:pts.map(p=>p.x>=80&&p.y<=20?C.red+"cc":p.x<=50&&p.y>=90?C.green+"cc":p.shareRatio>=3?C.amber+"cc":C.blue+"66"),pointRadius:pts.map(p=>p.x>=80&&p.y<=20||p.x<=50&&p.y>=90||p.shareRatio>=3?6:3),pointHoverRadius:8}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>`${ctx.raw.n}｜訂閱 ${ctx.raw.x}% / 期間觀看 ${ctx.raw.y}%｜期間觀看/訂閱 ${ctx.raw.fps.toFixed(2)}`}}},scales:{x:{min:0,max:100,ticks:{color:TICK,callback:v=>v+"%"},grid:{color:GRID},title:{display:true,text:"訂閱數百分位",color:TICK}},y:{min:0,max:100,ticks:{color:TICK,callback:v=>v+"%"},grid:{color:GRID},title:{display:true,text:"期間觀看數百分位",color:TICK}}}}});
    const sleep=pts.filter(p=>p.x>=80&&p.y<=20).sort((a,b)=>b.s-a.s).slice(0,8);
    const dark=pts.filter(p=>p.x<=50&&p.y>=90).sort((a,b)=>b.pv-a.pv).slice(0,8);
    const over=pts.filter(p=>isFinite(p.shareRatio)).sort((a,b)=>b.shareRatio-a.shareRatio).slice(0,8);
    const block=(title,arr,extra)=>`<div class="faq-card"><h4>${title}</h4><table class="table"><thead><tr><th>頻道</th><th>訂閱</th><th>期間觀看數</th><th>${extra}</th></tr></thead><tbody>${arr.map(c=>`<tr><td>${avatar(c)}${escHtml(c.n||c.id)}</td><td>${fmt(c.s)}</td><td>${fmt(c.pv)}</td><td>${extra==="注意力倍數"?c.shareRatio.toFixed(1)+"x":c.fps.toFixed(2)}</td></tr>`).join("")||'<tr><td colspan="4">目前沒有符合條件的頻道。</td></tr>'}</tbody></table></div>`;
    document.getElementById("concOutlier").innerHTML=`<div class="grid">${block("沉睡大台：訂閱高、期間觀看低",sleep,"期間觀看/訂閱")}${block("流量黑馬：訂閱低、期間觀看高",dark,"期間觀看/訂閱")}${block("注意力超配：期間觀看份額高於訂閱份額",over,"注意力倍數")}</div><div class="footer">特異值只納入 Activity=Active 的頻道；畢業與非活動頻道不列入沉睡/黑馬判斷。期間觀看數以本期累計觀看減前一期累計觀看估算；負向資料校正以 0 處理。</div>`;
  }
  function renderShare(){
    if(store.ccShare){store.ccShare.destroy();store.ccShare=null;}
    const ps=periods(), rec=ps[+periodEl.value]||ps[ps.length-1]||{label:"—",channels:[]};
    const key=metricEl.value, rows=(rec.channels||[]).filter(c=>c.id&&c[key]!=null&&isFinite(c[key])&&c[key]>0).slice().sort((a,b)=>(b[key]||0)-(a[key]||0));
    const total=rows.reduce((a,c)=>a+(c[key]||0),0), scope=scopeEl.value;
    let picked=[], title="", selected=null;
    if(scope==="channel"){
      const found=findChannel(qEl.value);
      selected=found?rows.find(c=>c.id===found.id):null;
      if(selected){picked=[selected];title=selected.n||found.n||found.t||selected.id;stEl.textContent=`已套用：${title}`;}
      else{stEl.textContent="找不到頻道，或此頻道沒有此項資料。";picked=[];title="特定頻道";}
    }else{
      const n=topCount(scope,rows.length);picked=rows.slice(0,n);title=scopeEl.options[scopeEl.selectedIndex].textContent;stEl.textContent="";
    }
    const sum=picked.reduce((a,c)=>a+(c[key]||0),0), share=total?sum/total:null;
    const rank=selected?rows.findIndex(c=>c.id===selected.id)+1:null;
    const floor=picked.length?picked[picked.length-1][key]:null;
    document.getElementById("concSummary").innerHTML=[
      ["時間",rec.label||"—",timeEl.options[timeEl.selectedIndex].textContent],
      ["檢視對象",title||"—",labelOf[key]],
      ["占全體比例",share==null?"—":(share*100).toFixed(2)+"%",`全體 ${fmt(total)}`],
      ["涵蓋頻道",fmt(picked.length),`有${unitOf[key]}資料 ${fmt(rows.length)} 個`],
      [scope==="channel"?"排行":"門檻值",scope==="channel"&&rank>0?`第 ${rank}/${rows.length}`:fmt(floor),unitOf[key]]
    ].map(x=>`<div class="kpi"><div class="l">${x[0]}</div><div class="v">${x[1]}</div><div class="d">${x[2]||""}</div></div>`).join("");
    const bars=(scope==="channel"&&selected?rows.slice(Math.max(0,rank-6),rank+5):picked.slice(0,30)).filter(Boolean);
    store.ccShare=new Chart(document.getElementById("ccShare"),{type:"bar",data:{labels:bars.map(c=>c.n||c.t||c.id),datasets:[{label:labelOf[key],data:bars.map(c=>c[key]),backgroundColor:bars.map(c=>selected&&c.id===selected.id?C.amber:C.blue)}]},options:{responsive:true,maintainAspectRatio:false,indexAxis:"y",plugins:{legend:{display:false}},scales:{x:{ticks:{color:TICK,callback:v=>fmt(v)},grid:{color:GRID}},y:{ticks:{color:TICK,font:{size:11}},grid:{color:GRID}}}}});
    document.getElementById("concTable").innerHTML=`<table class="table"><thead><tr><th>#</th><th>頻道</th><th>${labelOf[key]}</th><th>占全體</th><th>累積占比</th></tr></thead><tbody>${bars.map(c=>{const i=rows.findIndex(x=>x.id===c.id),cum=rows.slice(0,i+1).reduce((a,x)=>a+(x[key]||0),0);return `<tr><td>${i+1}</td><td>${avatar(c)}${escHtml(c.n||c.t||c.id)}</td><td>${fmt(c[key])}</td><td>${total?((c[key]/total)*100).toFixed(3)+"%":"—"}</td><td>${total?((cum/total)*100).toFixed(2)+"%":"—"}</td></tr>`;}).join("")}</tbody></table>`;
    renderOutliers(rec);
  }
  timeEl.addEventListener("change",()=>{fillPeriods();renderShare();});
  [periodEl,metricEl,scopeEl].forEach(el=>el&&el.addEventListener("change",renderShare));
  document.getElementById("concApply").onclick=()=>{scopeEl.value="channel";renderShare();};
  fillPeriods();
  renderShare();
}

function buildPyr(inclP){
  const D=getAct(inclP).filter(d=>d.yt_tier_small!=null),L=D.map(d=>d.quarter);
  const tiers=[["yt_tier_mega",">100k","#ff5a5f"],["yt_tier_large","10k–100k","#ffb454"],["yt_tier_mid","1k–10k","#4aa8ff"],["yt_tier_small","<1k","#5b6377"]];
  new Chart(py1,{type:"bar",data:{labels:L,datasets:tiers.map(t=>({label:t[1],data:D.map(d=>d[t[0]]),backgroundColor:t[2]}))},options:opts({},true)});
  const pct=D.map(d=>{const t=d.yt_tier_mega+d.yt_tier_large+d.yt_tier_mid+d.yt_tier_small||1;return tiers.map(x=>+((d[x[0]]/t*100).toFixed(1)));});
  new Chart(py2,{type:"bar",data:{labels:L,datasets:tiers.map((t,i)=>({label:t[1],data:pct.map(p=>p[i]),backgroundColor:t[2]}))},options:opts({},true,true)});
}

function buildContent(inclP){
  const Dv=getAct(inclP).filter(d=>d.topvid_buckets),Lv=Dv.map(d=>d.quarter);
  const vid=pctStack(Dv,"topvid_buckets");
  new Chart(ct1,{type:"bar",data:{labels:Lv,datasets:BUCKETS.map(k=>({label:k,data:vid.map(x=>x[k]),backgroundColor:BCOL[k]}))},options:opts({},true,true)});
  const Ds=getAct(inclP).filter(d=>d.yt_live_buckets&&Object.keys(d.yt_live_buckets).length),Ls=Ds.map(d=>d.quarter);
  const st=pctStack(Ds,"yt_live_buckets");
  new Chart(ct2,{type:"bar",data:{labels:Ls,datasets:BUCKETS.map(k=>({label:k,data:st.map(x=>x[k]),backgroundColor:BCOL[k]}))},options:opts({},true,true)});
  const nat=COH.current.nationality;const ne=Object.entries(nat).slice(0,7);
  new Chart(ct3,{type:"doughnut",data:{labels:ne.map(e=>e[0]),datasets:[{data:ne.map(e=>e[1]),backgroundColor:["#4aa8ff","#ff5a5f","#ffb454","#a970ff","#37d99a","#2dd4bf","#5b6377"]}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"right",labels:{color:TICK,font:{size:10.5}}}}}});
  const g=COH.current.group_split,a=COH.current.activity;
  new Chart(ct4,{type:"bar",data:{labels:["團體/個人","活動狀態"],datasets:[
    {label:"團體",data:[g.group,0],backgroundColor:C.cum},
    {label:"個人",data:[g.indie,0],backgroundColor:"#5b6377"},
    {label:"Active",data:[0,a.Active],backgroundColor:C.green},
    {label:"Graduated",data:[0,a.Graduated],backgroundColor:C.grad},
    {label:"Preparing",data:[0,a.Preparing||0],backgroundColor:C.rate}]},options:opts({},true)});
}

function buildFaqOld(inclP){
  const bucketZh={game:"遊戲",chat:"雜談",singing:"歌回",shorts:"短影音",asmr:"ASMR",collab:"連動",announcement:"公告",other:"其他"};
  const badgeText={green:"可回答",amber:"部分回答",red:"資料不足"};
  const pct = v => v==null||!isFinite(v) ? "—" : (v*100).toFixed(1)+"%";
  const ratioFmt = v => v==null||!isFinite(v) ? "—" : v.toFixed(3);
  const esc = s => (s==null?"":String(s)).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
  const latestSettled = ACT.filter(d=>!d.partial);
  const cur = latestSettled[latestSettled.length-1] || ACT[ACT.length-1] || {};
  const yoy = latestSettled.length>=5 ? latestSettled[latestSettled.length-5] : null;
  const maxBucket = obj => {
    const entries=Object.entries(obj||{}).filter(([k,v])=>k!=="other"&&v>0).sort((a,b)=>b[1]-a[1]);
    return entries.length ? (bucketZh[entries[0][0]]||entries[0][0]) : "資料不足";
  };
  const share = d => {
    const b=d&&d.yt_live_buckets||{};
    const total=Object.values(b).reduce((a,x)=>a+x,0);
    return total ? (b.collab||0)/total : null;
  };
  const ratios = DIRDATA.channels.filter(c=>c.r!=null&&c.s).map(c=>c.r/c.s).sort((a,b)=>a-b);
  const median = ratios.length ? ratios[Math.floor(ratios.length/2)] : null;
  const p90 = ratios.length ? ratios[Math.floor(ratios.length*0.9)] : null;
  const zombie = DIRDATA.channels.filter(c=>c.s>=50000 && c.r!=null && c.r/c.s<0.01).length;
  const sticky = DIRDATA.channels.filter(c=>c.s>=1000 && c.s<10000 && c.r!=null && c.r/c.s>0.3).length;
  const collabNow = share(cur), collabYoY = yoy ? share(yoy) : null;
  const topVidBucket = maxBucket(cur.topvid_buckets);
  const topLiveBucket = maxBucket(cur.yt_live_buckets);

  const perChannel = {
    q1(c){
      if(c.r==null||!c.s)return "此頻道缺近期觀看或訂閱資料，無法估黏著度。";
      const ratio=c.r/c.s,p=pctile(arrs().reff,ratio),prh=pctile(arrs().rh,c.rh);
      const judge=p>=90?"死忠濃度屬全體前段":p>=50?"黏著度中上":"黏著度偏低，較可能有較多無效訂閱";
      return `近期中位觀看/訂閱 = ${ratio.toFixed(3)}，黏著度贏過全體 ${p??"—"}%；爆紅力(近期最高觀看 ${fmt(c.rh)}) 贏過 ${prh??"—"}%。判讀：${judge}。`;
    },
    q2(){return "此頻道同樣沒有同接 / 留存資料，無法判斷其黃金時段。";},
    q3(){return "本儀表板未存此頻道的逐影片內容分類，給不出它個別的吸粉密碼。";},
    q4(){return "查不到此頻道逐場連動與連動前後的訂閱波動。";},
    q5(){return "查不到此頻道的 Super Chat 金流資料。";},
    q6(c){
      if(!c.v||!c.s)return "無互動率資料；此頻道也缺少可用的累計觀看/訂閱替代指標。";
      const eff=c.v/c.s,pe=pctile(arrs().eff,eff),prh=pctile(arrs().rh,c.rh);
      return `無互動率資料。替代參考：累計觀看/訂閱 = ${Math.round(eff)}（曝光效率贏過 ${pe??"—"}%），爆紅力贏過 ${prh??"—"}%——但這不能取代真正的留言/按讚互動率。`;
    },
    q7(){return "查不到對應此頻道的剪輯頻道數據。";},
    q8(){return "本儀表板未存此頻道的高頻訂閱時序，無法即時偵測它的退訂潮。";}
  };

  const questions=[
    {id:"q1",status:"amber",question:"核心死忠粉絲到底有多少？",
      headline:`用「近期中位觀看數 ÷ 訂閱數」當黏著度代理：全體中位數 ${ratioFmt(median)}、前 10% 達 ${ratioFmt(p90)}。訂閱 5 萬以上卻有 ${zombie} 個頻道的觀看/訂閱低於 1%（疑似殭屍訂閱）；反觀訂閱 1k–10k 卻有 ${sticky} 個頻道黏著度超過 0.3，是被低估的高含金量創作者。`,
      method:"DIR.channels 每頻道 r/s；門檻 0.01 與 0.3 為經驗值。",
      caveat:"這不是真正的「最高同時觀看數（同接）」。本資料源沒有直播即時同接，只能用 VOD 觀看數推估黏著度，結果偏保守。",
      hasChart:true},
    {id:"q2",status:"red",question:"觀眾的作息與黃金收視時段是什麼時候？",
      headline:"答不了。資料裡有每場直播的開台時間，但沒有任何「同時在線人數」與「留存」數據，無法判斷哪個時段最能聚集觀眾。",
      method:"直播資料僅含標題/開台時間/URL，無觀看曲線。",
      caveat:"要回答需自建「同接爬蟲」逐分鐘抓直播在線人數，本專案不涵蓋。"},
    {id:"q3",status:"amber",question:"哪種遊戲或企劃是這個頻道的「吸粉密碼」？",
      headline:`能看內容類型的版圖變化：最新一季熱門影片以「${topVidBucket}」佔比最高，YouTube 直播則以「${topLiveBucket}」為主幹。可把類型趨勢和同期訂閱中位數變化並列觀察。`,
      method:"ACT 最新已結算季的 topvid_buckets / yt_live_buckets 取最大類別。",
      caveat:"只能看「全體類型分布趨勢」，無法把單一企劃歸因到具體的訂閱淨增長，也沒有「新觀眾佔比」。要做企劃級歸因需逐頻道、逐影片的時序訂閱資料。"},
    {id:"q4",status:"amber",question:"連動（Collaboration）到底有沒有圈粉？",
      headline:`連動在台 V 直播裡是少數：最新一季連動佔 YouTube 開台的 ${pct(collabNow)}，一年前是 ${pct(collabYoY)}，整體呈下滑趨勢。`,
      method:"ACT 各季 yt_live_buckets.collab ÷ 該季全部開台數；連動由標題關鍵字判定。",
      caveat:"標題關鍵字判定有雜訊（部分連動不寫在標題）。而且「連動前後個別頻道的訂閱波動」需要逐頻道、逐日的訂閱時序，本儀表板是季度聚合，看不到單場連動的拉抬效果。"},
    {id:"q5",status:"red",question:"什麼主題最能激發粉絲課金（Super Chat）？",
      headline:"答不了。本專案完全沒有 Super Chat / 抖內金流資料，無法分析課金與主題的關聯。",
      method:"所有 CSV 皆無 SC 欄位。",
      caveat:"要回答需接 Playboard 等第三方金流追蹤工具，本專案不涵蓋。"},
    {id:"q6",status:"red",question:"這個頻道具不具備接工商（業配）的轉換實力？",
      headline:"答不了。要算互動率（Engagement Rate）需要留言數、按讚數等互動數據，本資料源只有觀看數，無法計算。",
      method:"基本資料 / 近期數據 / 熱門影片資料皆無留言、按讚欄位。",
      caveat:"現有資料只能比規模與觀看熱度，無法判斷「觀看轉互動」的效率。要做需另抓影片層級的互動指標。"},
    {id:"q7",status:"red",question:"精華剪輯（Clips）對主頻道的灌流效果有多大？",
      headline:"答不了。本專案只追蹤 VTuber 本人的官方頻道，沒有追蹤烤肉/精華剪輯頻道，無法把「某支剪輯爆紅」對應到「主頻道訂閱/搜尋陡增」。",
      method:"追蹤名單僅含本人 YouTube / Twitch 頻道。",
      caveat:"要回答需建立剪輯頻道清單並逐日追蹤，再與主頻道高頻訂閱序列做事件分析，本專案不涵蓋。"},
    {id:"q8",status:"amber",question:"頻道是正常波動，還是面臨炎上危機？",
      headline:"具備偵測退訂潮的基礎：基本資料訂閱數約每 2 小時一筆，能抓出訂閱數的異常下降作為早期警訊。",
      method:"目前資料源的基本資料高頻資料截點（約每 2 小時）。",
      caveat:"本儀表板呈現的是季度聚合，沒有「逐頻道高頻退訂曲線」；也沒有倒讚率與留言情緒。要做即時炎上告警需另建逐頻道時序表與情緒來源。"}
  ];

  function renderFaq(){
    const selected = faqChannel;
    document.getElementById("faqStatus").textContent = selected ? `已套用：${selected.n||selected.t||"未命名頻道"}` : "";
    document.getElementById("faqWrap").innerHTML=questions.map(q=>{
      const personal = selected ? `<p class="desc faq-personal">👤 此頻道（${esc(selected.n||selected.t||"未命名頻道")}）：${esc(perChannel[q.id](selected))}</p>` : "";
      const chart = q.hasChart ? `<div class="box"><canvas id="faqStickiness"></canvas></div>` : "";
      return `<div class="card full" style="margin-bottom:14px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <span class="faq-badge faq-${q.status}">${badgeText[q.status]}</span>
          <h3 style="margin:0">${q.question}</h3>
        </div>
        <p class="desc" style="font-size:13px;color:#cfd6e6;margin:6px 0">${q.headline}</p>
        <p class="desc">資料說明：${q.method}</p>
        <p class="desc" style="color:var(--amber)">⚠ ${q.caveat}</p>
        ${personal}
        ${chart}
      </div>`;
    }).join("");
    if(store.faqStickiness){store.faqStickiness.destroy();store.faqStickiness=null;}
    const canvas=document.getElementById("faqStickiness");
    if(canvas){
      const bins=[0,0.001,0.003,0.01,0.03,0.1,0.3,1,Infinity],labels=["0","<0.1%","<0.3%","<1%","<3%","<10%","<30%","30%+"],counts=Array(labels.length).fill(0);
      ratios.forEach(v=>{for(let i=0;i<labels.length;i++){if(v>=bins[i]&&v<bins[i+1]){counts[i]++;break;}}});
      store.faqStickiness=new Chart(canvas,{type:"bar",data:{labels,datasets:[{label:"頻道數",data:counts,backgroundColor:"#ffb454"}]},
        options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{color:TICK},grid:{color:GRID}},y:{ticks:{color:TICK},grid:{color:GRID}}}}});
    }
  }

  const list=document.getElementById("faqList");
  if(list)list.innerHTML=DIRDATA.channels.filter(c=>c.n).slice(0,4000).map(c=>`<option value="${esc(c.n)}">`).join("");
  const find=document.getElementById("faqFind"),clear=document.getElementById("faqClear"),q=document.getElementById("faqQ"),status=document.getElementById("faqStatus");
  if(find)find.onclick=()=>{const c=findChannel(q.value);if(!c){status.textContent="找不到，請改貼 UCxxxx。";return;}faqChannel=c;renderFaq();};
  if(clear)clear.onclick=()=>{faqChannel=null;if(q)q.value="";renderFaq();};
  renderFaq();
}


function buildFaq(inclP){
  const bucketZh={game:"遊戲",chat:"雜談",singing:"歌回",shorts:"短影音",asmr:"ASMR",collab:"連動",announcement:"公告",other:"其他"};
  const badgeText={green:"可回答",amber:"部分回答"};
  const esc=s=>(s==null?"":String(s)).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
  const p=v=>v==null||!isFinite(v)?"—":v+"%";
  const pc=(a,v)=>p(pctile(a,v));
  const num=v=>v==null||!isFinite(v)?"—":fmt(v);
  const ratio=(a,b)=>a!=null&&b?a/b:null;
  const card=(tone,q,line,meta)=>`<div class="faq-card"><div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap"><span class="faq-badge faq-${tone}">${badgeText[tone]}</span><h4>${q}</h4></div><div class="faq-line">${line}</div><div class="faq-meta">${meta}</div></div>`;
  const yearsSince=d=>{if(!d)return "未記載"; const y=+String(d).slice(0,4); return y?((2026-y)+" 年左右"):"未記載";};
  const classify=(lm,vm)=>{if(lm==null&&vm==null)return "資料不足"; if(lm!=null&&vm==null)return "直播型"; if(vm!=null&&lm==null)return "投稿型"; if(lm>vm*1.5)return "直播型"; if(vm>lm*1.5)return "投稿型"; return "直播投稿均衡";};
  const topBuckets=cb=>{const es=Object.entries(cb||{}).filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]); const total=es.reduce((a,[,v])=>a+v,0); if(!total)return "資料不足"; return es.slice(0,3).map(([k,v])=>`${bucketZh[k]||k} ${((v/total)*100).toFixed(1)}%`).join("、");};
  const groupPct=(rows,c)=>{const vals=rows.map(x=>x.s).filter(v=>v!=null&&isFinite(v)).sort((a,b)=>a-b); return pc(vals,c.s);};
  const settled=ACT.filter(d=>!d.partial), cur=settled[settled.length-1]||ACT[ACT.length-1]||{};

  function buildChannel(c){
    const A=arrs(), yp=pctile(A.s,c.s), tp=pctile(A.f,c.f);
    const hasYT=c.s!=null, hasTW=c.f!=null, platform=hasYT&&hasTW?"雙平台經營":"單平台";
    const main=hasYT&&hasTW?(yp>=tp?"YouTube":"Twitch"):(hasYT?"YouTube":(hasTW?"Twitch":"資料不足"));
    const type=classify(c.lm,c.vm);
    const hot=c.lh==null&&c.vh==null?"資料不足":((c.lh||0)>=(c.vh||0)?"直播":"投稿");
    const rr=ratio(c.rh,c.r), swing=rr==null?"資料不足":(rr>=5?"偶有爆款":(rr<=2?"穩定盤":"起伏中等"));
    const reff=ratio(c.r,c.s), eff=ratio(c.v,c.s);
    const liveLink=c.lhu?`最熱直播：<a href="${esc(c.lhu)}" target="_blank">觀看 ${num(c.lh)}</a>`:"";
    const vidLink=c.vhu?`最熱投稿：<a href="${esc(c.vhu)}" target="_blank">觀看 ${num(c.vh)}</a>`:"";
    const dyear=String(c.d||"").slice(0,4);
    const sameTier=DIRDATA.channels.filter(x=>tierOf(x.s)===tierOf(c.s));
    const sameNat=DIRDATA.channels.filter(x=>x.nat&&x.nat===c.nat);
    const sameYear=DIRDATA.channels.filter(x=>String(x.d||"").slice(0,4)===dyear);
    let out=[
      card("green","C1 這個頻道在全台 V 排第幾、屬哪個級距？",`YouTube 訂閱 ${num(c.s)}，贏過全體 ${pc(A.s,c.s)}，屬 ${tierOf(c.s)||"—"} 級距。累計觀看 ${num(c.v)}（贏過 ${pc(A.v,c.v)}）。`,"資料說明：基本資料最新資料截點。"),
      card("green","C2 主戰場是 YouTube 還 Twitch？是否雙棲？",`${platform}：YouTube 訂閱 ${num(c.s)}、Twitch 追隨 ${num(c.f)}。相對全體，${main} 是它的主戰場（YT 贏過 ${pc(A.s,c.s)}、Twitch 贏過 ${pc(A.f,c.f)}）。`,"資料說明：YouTube 訂閱與 Twitch 追隨各自做全體百分位。"),
      card("green","C3 它是直播型還是投稿型創作者？",`近期直播中位觀看 ${num(c.lm)}、投稿影片中位 ${num(c.vm)} → 判定為「${type}」。`,"資料說明：近期數據直播/投稿分項中位數。"),
      card("green","C4 它的熱度來自直播還是投稿影片？",`近期最高觀看：直播 ${num(c.lh)}、投稿 ${num(c.vh)}，主要爆點來自${hot}。`,"資料說明：近期數據的近期直播最高與投稿最高。"),
      card("green","C5 它是穩定盤還是偶有爆款？",`近期最高觀看是中位的 ${rr==null?"—":rr.toFixed(1)} 倍 → ${swing}。`,"資料說明：近期數據最高 ÷ 近期中位。"),
      card("amber","C6 它的黏著度與爆紅力在同儕間如何？",`黏著度（近期中位觀看/訂閱）= ${reff==null?"—":reff.toFixed(3)}，贏過全體 ${pc(A.reff,reff)}；爆紅力（近期最高觀看 ${num(c.rh)}）贏過 ${pc(A.rh,c.rh)}。`,"黏著度是用 VOD 觀看推估，非真實同接。"),
      card("green","C7 它最熱的一場直播 / 一支影片是？",[liveLink,vidLink].filter(Boolean).join("；")||"此資料截點沒有可用的最熱內容連結。","資料說明：近期數據最高觀看 URL 欄位。"),
      card("green","C8 它近期都播什麼類型內容？",`近期內容以 ${topBuckets(c.cb)} 為主。`,"資料說明：該頻道熱門影片資料 + 直播資料標題分類，與「內容與組成」使用同一分類方式。"),
      card("green","C9 它最熱門的影片是哪支？",c.tv?`最熱影片：<a href="${esc(c.tv.url||"#")}" target="_blank">${esc(c.tv.title||"未命名影片")}</a>（觀看 ${num(c.tv.vc)}）。`:"此資料截點沒抓到它的熱門影片。","資料說明：最新熱門影片資料中該頻道 View Count 最高者。"),
      card("green","C10 它出道多久、目前狀態、團體還個人？",`${c.gn?`團體勢（${esc(c.gn)}）`:"個人勢"}，狀態 ${esc(c.ac||"未記載")}，出道 ${esc(c.d||"未記載")}（約 ${yearsSince(c.d)}）。`,"資料說明：追蹤名單。"),
      card("green","C12 它跟同屆/同國籍/同級距比贏過多少人？",`同級距贏過 ${groupPct(sameTier,c)}、同國籍(${esc(c.nat||"—")})贏過 ${groupPct(sameNat,c)}、同屆(${dyear||"—"})贏過 ${groupPct(sameYear,c)}。`,"更完整的定位圖見「定位你自己」分頁。")
    ];
    if(c.gn){
      const mates=DIRDATA.channels.filter(x=>x.gn===c.gn), sum=mates.reduce((a,x)=>a+(x.s||0),0);
      const names=mates.slice().sort((a,b)=>(b.s||0)-(a.s||0)).slice(0,5).map(x=>`${esc(x.n||x.t||"未命名")}(${num(x.s)})`).join("、");
      out.splice(10,0,card("green","C11 它同團體還有誰、團體規模如何？",`團體「${esc(c.gn)}」共 ${mates.length} 位、合計訂閱 ${num(sum)}。主要成員：${names}。`,"資料說明：追蹤名單團體名稱對齊。"));
    }
    return out.join("");
  }

  function buildIndustry(){
    const peak=(COH.series||[]).reduce((a,b)=>!a||b.debuts>a.debuts?b:a,null)||{};
    const tb=cur.topvid_buckets||{}, total=Object.values(tb).reduce((a,x)=>a+x,0)||1;
    const max=Object.entries(tb).sort((a,b)=>b[1]-a[1])[0]||["other",0];
    const nat=COH.current.nationality||{}, ns=Object.entries(nat).sort((a,b)=>b[1]-a[1]).slice(0,3).map(([k,v])=>`${k} ${fmt(v)}`).join("、");
    const years={}; DIRDATA.channels.forEach(c=>{const y=String(c.d||"").slice(0,4); if(!/^20/.test(y))return; years[y]=years[y]||{a:0,t:0}; years[y].t++; if(c.ac==="Active")years[y].a++;});
    const alive=Object.entries(years).filter(([y])=>+y>=2022).slice(-5).map(([y,o])=>`${y} 屆存活 ${((o.a/o.t)*100).toFixed(1)}%`).join("、");
    const lv={live:0,video:0,bal:0}; DIRDATA.channels.forEach(c=>{if(c.lm==null||c.vm==null)return; const t=classify(c.lm,c.vm); if(t==="直播型")lv.live++; else if(t==="投稿型")lv.video++; else lv.bal++;});
    const ltot=lv.live+lv.video+lv.bal||1, maj=lv.live>=lv.video&&lv.live>=lv.bal?"直播型":(lv.video>=lv.bal?"投稿型":"均衡");
    return [
      card("green","I1 台 V 產業在擴張還是成熟？",`出道潮高峰在 ${peak.quarter||"—"}（單季 ${num(peak.debuts)} 人），近季已放緩；現存名單 ${num(COH.current.total)} 人。產業由擴張轉成熟。`,"詳見「進出場動態」分頁。"),
      card("green","I2 哪種內容當道？短影音崛起了嗎？",`最新一季熱門影片以 ${bucketZh[max[0]]||max[0]} 為主，短影音(shorts)佔 ${(((tb.shorts||0)/total)*100).toFixed(1)}%。`,"詳見「內容與組成」分頁。"),
      card("green","I3 國籍組成、團體 vs 個人比例？",`現存名單前三：${ns}；團體 ${fmt(COH.current.group_split.group)} : 個人 ${fmt(COH.current.group_split.indie)}。`,"資料說明：追蹤名單現況。"),
      card("green","I4 頭部集中度與級距金字塔？",`前 10 大佔全體訂閱 ${cur.yt_top10_share==null?"—":(cur.yt_top10_share*100).toFixed(1)+"%"}、全體觀看 ${cur.yt_view_top10_share==null?"—":(cur.yt_view_top10_share*100).toFixed(1)+"%"}，訂閱中位數 ${num(cur.yt_subs_median)}；長尾變厚、中段墊高。`,"詳見「集中度與規模」「訂閱級距金字塔」分頁。"),
      card("green","I5 某屆出道者現在還活著的比例（畢業率）？",alive||"出道年資料不足。","追蹤名單為現存記載，含倖存者偏差；早被刪除者未必在列。"),
      card("green","I6 台 V 是直播型還是投稿型生態？",`在兩項皆有數據的頻道中，直播型 ${((lv.live/ltot)*100).toFixed(1)}%、投稿型 ${((lv.video/ltot)*100).toFixed(1)}%、均衡 ${((lv.bal/ltot)*100).toFixed(1)}% → 台 V 以${maj}為主。`,"資料說明：依近期直播/投稿中位觀看即時計算。")
    ].join("");
  }

  const list=document.getElementById("faqList");
  if(list)list.innerHTML=DIRDATA.channels.filter(c=>c.n).slice(0,4000).map(c=>`<option value="${esc(c.n)}">`).join("");
  const chan=document.getElementById("faqChan"), ind=document.getElementById("faqInd"), foot=document.getElementById("faqUnanswerable");
  const renderChan=()=>{document.getElementById("faqStatus").textContent=faqChannel?`已套用：${faqChannel.n||faqChannel.t||"未命名頻道"}`:""; chan.innerHTML=faqChannel?buildChannel(faqChannel):`<p class="muted">未選頻道。上方輸入後按「套用」。</p>`;};
  ind.innerHTML=buildIndustry();
  foot.innerHTML="本資料源（YouTube / Twitch 公開頻道統計）無法回答以下問題，需另接外部資料源：・Super Chat 抖內金額與主題關聯 → 需 Playboard 等金流工具 ・最高同時觀看數（同接）、黃金收視時段 → 需自建直播同接爬蟲 ・工商轉換力（留言/按讚互動率） → 需影片層級互動數據 ・精華剪輯（烤肉）對主頻道的灌流 → 需追蹤剪輯頻道清單";
  const find=document.getElementById("faqFind"),clear=document.getElementById("faqClear"),q=document.getElementById("faqQ"),status=document.getElementById("faqStatus");
  if(find)find.onclick=()=>{const c=findChannel(q.value);if(!c){status.textContent="找不到，請改貼 UCxxxx。";return;}faqChannel=c;renderChan();};
  if(clear)clear.onclick=()=>{faqChannel=null;if(q)q.value="";renderChan();};
  renderChan();
}


// ---------- 定位你自己 ----------
let DIRDATA = DIR;
let curChannel = null;
let faqChannel = null;
let gwChannel = null;
function arrs(){const C=DIRDATA.channels;const g=f=>C.map(f).filter(v=>v!=null&&isFinite(v)).sort((a,b)=>a-b);
  return {s:g(c=>c.s),v:g(c=>c.v),f:g(c=>c.f),r:g(c=>c.r),rh:g(c=>c.rh),
    eff:g(c=>(c.v!=null&&c.s)?c.v/c.s:null),reff:g(c=>(c.r!=null&&c.s)?c.r/c.s:null)};}
function pctile(arr,v){if(v==null||!arr.length)return null;let lo=0,hi=arr.length;
  while(lo<hi){const m=(lo+hi)>>1;if(arr[m]<v)lo=m+1;else hi=m;}return +(lo/arr.length*100).toFixed(1);}
function upperBound(arr,v){let lo=0,hi=arr.length;while(lo<hi){const m=(lo+hi)>>1;if(arr[m]<=v)lo=m+1;else hi=m;}return lo;}
function rankIn(arr,v){if(v==null||!arr.length)return null;const p=pctile(arr,v),gt=arr.length-upperBound(arr,v);return {pct:p,rank:gt+1,n:arr.length};}
function tierOf(s){if(s==null)return null;if(s>=100000)return">100k";if(s>=10000)return"10k–100k";if(s>=1000)return"1k–10k";return"<1k";}
function findChannel(q){q=(q||"").trim();if(!q)return null;const ql=q.toLowerCase(),ch=DIRDATA.channels;
  if(/^UC[\w-]{20,}$/.test(q)){const m=ch.find(c=>c.y===q);if(m)return m;}
  let m=ch.find(c=>c.t&&c.t.toLowerCase()===ql);if(m)return m;
  m=ch.find(c=>c.n&&c.n.toLowerCase()===ql);if(m)return m;
  m=ch.find(c=>(c.n&&c.n.toLowerCase().includes(ql))||(c.a&&c.a.toLowerCase().includes(ql)));return m||null;}
function fillDatalist(){const el=document.getElementById("locList");if(!el)return;
  el.innerHTML=DIRDATA.channels.filter(c=>c.n).slice(0,4000).map(c=>`<option value="${c.n.replace(/"/g,'')}">`).join("");}

function regularity(s){if(!s||!s.first||!s.last)return null;const a=new Date(s.first),b=new Date(s.last);const w=Math.max(1,(b-a)/86400000/7);return s.active_weeks/w;}
const LON={mom:Object.values(GROW.channels).map(c=>c.mom_3m).filter(v=>v!=null&&isFinite(v)).sort((a,b)=>a-b),
  cagr:Object.values(GROW.channels).map(c=>c.cagr_yr).filter(v=>v!=null&&isFinite(v)).sort((a,b)=>a-b),
  reg:Object.values(STM.yt.channels).map(regularity).filter(v=>v!=null&&isFinite(v)).sort((a,b)=>a-b)};
function pctText(v){return v==null||!isFinite(v)?"—":(v*100).toFixed(1)+"%";}
function monthsBetween(a,b){return (b.getFullYear()-a.getFullYear())*12+(b.getMonth()-a.getMonth());}
function locLong(o){return o&&o.id?GROW.channels[o.id]:null;}
function locStream(o){return o&&o.id?STM.yt.channels[o.id]||(o.y?STM.yt.channels[o.y]:null):null;}
function locEvents(o){return o&&o.id&&EVT.channels[o.id]?EVT.channels[o.id].events||[]:[];}
function metricVector(c){
  const A=arrs(),g=locLong(c),st=locStream(c),eff=(c.v!=null&&c.s)?c.v/c.s:null,reff=(c.r!=null&&c.s)?c.r/c.s:null;
  return {訂閱:pctile(A.s,c.s),累計觀看:pctile(A.v,c.v),Twitch:pctile(A.f,c.f),黏著:pctile(A.reff,reff),
    爆紅:pctile(A.rh,c.rh),動能:g?pctile(LON.mom,g.mom_3m):null,規律:st?pctile(LON.reg,regularity(st)):null,
    熱度:pctile(A.r,c.r),曝光:pctile(A.eff,eff)};
}
function renderHealth(o){
  const box=document.getElementById("locHealth"), sim=document.getElementById("locSimilar"), brief=document.getElementById("locBrief");
  if(!o.id){box.innerHTML='<div class="note">輸入數字模式無成長/體檢資料；用頻道查詢可看完整體檢卡。</div>';sim.innerHTML="";brief.innerHTML="";return null;}
  const g=locLong(o), st=locStream(o), ev=locEvents(o), mv=metricVector(o);
  const axes=[mv.訂閱,mv.累計觀看,mv.Twitch,mv.熱度,mv.爆紅,mv.黏著,mv.動能,mv.規律].filter(v=>v!=null);
  const score=axes.length?Math.round(axes.reduce((a,x)=>a+x,0)/axes.length):null;
  const tag=score==null?"資料不足":score>=75?"強健":score>=50?"穩健":score>=30?"普通":"需關注";
  const cls=score>=75?"up":score<30?"down":"";
  box.innerHTML=`<div class="card full" style="margin-bottom:14px"><h3>頻道體檢總分</h3><div class="kpi"><div class="l">相對百分位合成，非絕對品質；缺軸以現有軸平均</div><div class="v ${cls}">${score==null?"—":score}</div><div class="d">${tag}・使用 ${axes.length}/8 軸</div></div></div>`;
  const names={debut:"初配信",birthday:"生日",anniversary:"周年",outfit:"新衣裝","3d":"3D"};
  const best=ev.filter(e=>e.delta!=null).sort((a,b)=>b.delta-a.delta)[0];
  const cov=(STM.yt.coverage.weekdays||[]).join(",");
  brief.innerHTML=`<div class="faq-card"><h4>作息 / 事件一句話</h4><div class="faq-line">${st?`最常週${["一","二","三","四","五","六","日"][st.peak_weekday]} ${st.peak_hour} 點開台・最長斷更 ${st.gap_max_days} 天`:"作息資料不足"}${best?`<br>最大吸粉事件：${names[best.type]||best.type} ${best.date}（+${fmt(best.delta)} 訂閱）`:""}</div><div class="faq-meta">作息樣本：${cov}。看完整成長/作息/事件 → 切到「成長與生命週期」分頁。</div></div>`;
  const target=metricVector(o), dims=["訂閱","累計觀看","Twitch","黏著","爆紅","動能"];
  const near=DIRDATA.channels.filter(c=>c.id&&c.id!==o.id).map(c=>{const v=metricVector(c);const ds=dims.filter(k=>target[k]!=null&&v[k]!=null).map(k=>[k,Math.abs(target[k]-v[k])]); if(ds.length<3)return null; const dist=Math.sqrt(ds.reduce((a,x)=>a+x[1]*x[1],0)/ds.length); ds.sort((a,b)=>a[1]-b[1]); return {c,dist,why:ds.slice(0,2).map(x=>x[0]).join("、")};}).filter(Boolean).sort((a,b)=>a.dist-b.dist).slice(0,5);
  sim.innerHTML=`<div class="faq-card"><h4>和你體質最像的台V</h4>${near.map(x=>`<div class="faq-line">${avatar(x.c)}${escHtml(x.c.n||x.c.t||"未命名")}・${x.why}相近</div>`).join("")||'<div class="faq-line">資料不足。</div>'}<div class="faq-meta">相似基於數據體質，非內容題材/風格。</div></div>`;
  return score;
}

function jumpLocate(id){
  const c=DIRDATA.channels.find(x=>x.id===id); if(!c)return;
  showTab("s_locate"); const q=document.getElementById("locQ"); if(q)q.value=c.n||c.y||c.t||"";
  curChannel=c; locate(Object.assign({},c,{label:c.n||c.t}));
}
function escHtml(s){return (s==null?"":String(s)).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));}
function avatar(c){return c&&c.img?`<img class="avatar" src="${escHtml(c.img)}" loading="lazy" onerror="this.style.display='none'">`:"";}

function buildRank(){
  const bestEvent=id=>((EVT.channels[id]||{}).events||[]).filter(e=>e.delta!=null).sort((a,b)=>b.delta-a.delta)[0];
  const sticky=c=>(c.r!=null&&c.s)?c.r/c.s:null, reg=c=>regularity(locStream(c));
  const boards=[["subs","訂閱 Top",c=>c.s,"訂閱"],["views","累計觀看 Top",c=>c.v,"觀看"],["tw","Twitch 追隨 Top",c=>c.f,"追隨"],
    ["mom","成長最快",c=>c.s>=5000&&GROW.channels[c.id]?GROW.channels[c.id].mom_3m:null,"近3月"],
    ["cagr","年化成長",c=>c.s>=5000&&GROW.channels[c.id]?GROW.channels[c.id].cagr_yr:null,"年化"],
    ["sticky","最黏",c=>c.s>=1000?sticky(c):null,"r/s"],["burst","爆紅力",c=>c.rh,"最高觀看"],
    ["event","最大吸粉事件",c=>{const e=bestEvent(c.id);return e?e.delta:null;},"淨增長"],
    ["rookie","出道黑馬",c=>{const g=GROW.channels[c.id]; if(!g||!c.d)return null; const m=monthsBetween(new Date(c.d),new Date(GROW.months[GROW.months.length-1]+"-01")); return m<=18?g.subs_now:null;},"訂閱"],
    ["regular","最規律開台",c=>{const s=locStream(c); return s&&s.n_streams>=10?reg(c):null;},"規律"],
    ["tv","熱門影片 Top",c=>c.tv&&c.tv.vc,"待資料"],["dual","雙棲最強",c=>XPLAT.channels[c.id]?XPLAT.channels[c.id].yt_pct+XPLAT.channels[c.id].tw_pct:null,"雙平台百分位和"]];
  let cur="subs";
  rankNat.innerHTML='<option value="">全部</option>'+[...new Set(DIRDATA.channels.map(c=>c.nat).filter(Boolean))].sort().map(n=>`<option>${escHtml(n)}</option>`).join("");
  rankChips.innerHTML=boards.map((b,i)=>`<button class="chip ${i?'':'on'}" data-k="${b[0]}">${b[1]}</button>`).join("");
  const valFmt=(k,v)=>["mom","cagr","sticky","regular"].includes(k)?pctText(v):fmt(v);
  function pass(c){const tier=rankTier.value,na=rankNat.value,ty=rankType.value;return(!tier||tierOf(c.s)===tier)&&(!na||c.nat===na)&&(ty===""||c.g===+ty);}
  function render(){const b=boards.find(x=>x[0]===cur), n=+rankN.value;if(String(b[3]).startsWith("待")){rankList.innerHTML='<div class="note">此榜待資料：熱門影片榜需 DIR.tv；雙棲榜需 crossplatform.json。</div>';return;}
    const rows=DIRDATA.channels.filter(c=>c.id&&pass(c)).map(c=>({c,v:b[2](c),e:bestEvent(c.id)})).filter(x=>x.v!=null&&isFinite(x.v)).sort((a,b)=>b.v-a.v).slice(0,n);
    if(store.rankBar){store.rankBar.destroy();store.rankBar=null;}
    if(!rows.length){rankList.innerHTML='<div class="note">此榜目前沒有符合篩選條件的頻道。</div>';return;}
    rankList.innerHTML=`<div class="card full"><h3>${b[1]}</h3><p class="desc">直播用橫條榜；下方表格可點回定位頁</p><div class="box tall"><canvas id="rankBar"></canvas></div></div><table class="table"><thead><tr><th>#</th><th>頻道</th><th>${b[3]}</th><th>標籤</th><th>補充</th></tr></thead><tbody>${rows.map((r,i)=>`<tr><td>${i+1}</td><td><a href="#" data-loc="${r.c.id}">${avatar(r.c)}${escHtml(r.c.n||r.c.t||r.c.id)}</a></td><td>${valFmt(cur,r.v)}</td><td><span class="tag">${tierOf(r.c.s)||"—"}</span><span class="tag">${escHtml(r.c.nat||"—")}</span><span class="tag">${r.c.g?"團體":"個人"}</span></td><td>${cur==="event"&&r.e?`${r.e.type} ${r.e.date} <a href="${escHtml(r.e.url)}" target="_blank">影片</a>`:""}</td></tr>`).join("")}</tbody></table><div class="footer">成長/黏著/規律為比率指標，已用門檻過濾；事件淨增長為毛估、未扣自然成長。</div>`;
    store.rankBar=new Chart(document.getElementById("rankBar"),{type:"bar",data:{labels:rows.map(r=>r.c.n||r.c.t||r.c.id),datasets:[{label:b[3],data:rows.map(r=>r.v),backgroundColor:rows.map((r,i)=>i<3?C.rate:C.blue)}]},options:{responsive:true,maintainAspectRatio:false,indexAxis:"y",plugins:{legend:{display:false}},scales:{x:{ticks:{color:TICK},grid:{color:GRID}},y:{ticks:{color:TICK,font:{size:11}},grid:{color:GRID}}}}});
    rankList.querySelectorAll("[data-loc]").forEach(a=>a.onclick=e=>{e.preventDefault();jumpLocate(a.dataset.loc);});}
  rankChips.querySelectorAll(".chip").forEach(ch=>ch.onclick=()=>{cur=ch.dataset.k;rankChips.querySelectorAll(".chip").forEach(x=>x.classList.toggle("on",x===ch));render();});
  ["rankTier","rankNat","rankType","rankN"].forEach(id=>document.getElementById(id).onchange=render);render();
}

function buildAgency(){
  const chans=DIRDATA.channels.filter(c=>c.id), byId=Object.fromEntries(chans.map(c=>[c.id,c])), groups={};
  Object.entries(GROW.channels).forEach(([id,g])=>{const c=byId[id], gn=(g.gn||c&&c.gn||"").trim(); if(!gn)return; (groups[gn]||(groups[gn]=[])).push(Object.assign({},c,g,{id}));});
  const med=a=>{a=a.filter(v=>v!=null).sort((x,y)=>x-y);return a.length?a[Math.floor(a.length/2)]:null;};
  const stats=Object.entries(groups).map(([gn,m])=>{const total=m.reduce((a,x)=>a+(x.subs_now||x.s||0),0),mx=m.slice().sort((a,b)=>(b.subs_now||0)-(a.subs_now||0))[0];return{gn,members:m.length,total,median:med(m.map(x=>x.subs_now||x.s)),max:mx,head:total&&mx?((mx.subs_now||mx.s||0)/total):null,mom:med(m.map(x=>x.mom_3m)),alive:m.filter(x=>x.ac==="Active").length/m.length};});
  agList.innerHTML=stats.filter(x=>x.members>=3).sort((a,b)=>b.members-a.members).map(x=>`<option value="${escHtml(x.gn)}">`).join("");
  function table(){const key=agSort.value,arr=stats.slice().sort((a,b)=>(key==="members"?b.members-a.members:key==="median"?(b.median||0)-(a.median||0):b.total-a.total)).slice(0,30);
    agTable.innerHTML=`<table class="table"><thead><tr><th>團體</th><th>成員</th><th>總訂閱</th><th>每人中位</th><th>頭部集中</th><th>存活率</th></tr></thead><tbody>${arr.map(x=>`<tr><td><a href="#" data-ag="${escHtml(x.gn)}">${escHtml(x.gn)}</a></td><td>${x.members}</td><td>${fmt(x.total)}</td><td>${fmt(x.median)}</td><td>${pctText(x.head)}</td><td>${pctText(x.alive)}</td></tr>`).join("")}</tbody></table>`;
    agTable.querySelectorAll("[data-ag]").forEach(a=>a.onclick=e=>{e.preventDefault();agQ.value=a.dataset.ag;deep(a.dataset.ag);});}
  function deep(gn){const st=stats.find(x=>x.gn===gn);if(!st){agStatus.textContent="找不到團體";return;}agStatus.textContent="已套用："+gn;const m=groups[gn].slice().sort((a,b)=>(b.subs_now||b.s||0)-(a.subs_now||a.s||0));
    agKpi.innerHTML=`<div class="kpis"><div class="kpi"><div class="l">成員數</div><div class="v">${st.members}</div></div><div class="kpi"><div class="l">總訂閱</div><div class="v">${fmt(st.total)}</div></div><div class="kpi"><div class="l">每人中位</div><div class="v">${fmt(st.median)}</div></div><div class="kpi"><div class="l">頭部集中</div><div class="v">${pctText(st.head)}</div></div></div>`;
    agDeep.innerHTML=`<table class="table"><thead><tr><th>成員</th><th>訂閱</th><th>近3月</th><th>狀態</th></tr></thead><tbody>${m.map(x=>`<tr><td><a href="#" data-loc="${x.id}">${avatar(x)}${escHtml(x.n||x.id)}</a></td><td>${fmt(x.subs_now||x.s)}</td><td>${pctText(x.mom_3m)}</td><td>${escHtml(x.ac||"")}</td></tr>`).join("")}</tbody></table><div class="footer">存活率含倖存者偏差；企業/社團三分目前無標記。</div>`;
    agDeep.querySelectorAll("[data-loc]").forEach(a=>a.onclick=e=>{e.preventDefault();jumpLocate(a.dataset.loc);});}
  agSort.onchange=table; agFind.onclick=()=>deep(agQ.value); table();
  const g1=chans.filter(c=>c.g),g0=chans.filter(c=>!c.g),val=(arr,fn)=>med(arr.map(fn));
  const tierPts=stats.filter(x=>x.members>=2&&x.total>0&&x.median>0).map(x=>({x:x.total,y:x.median,r:Math.max(4,Math.min(18,3+Math.sqrt(x.members)*3)),gn:x.gn,members:x.members,head:x.head,alive:x.alive}));
  new Chart(agTier,{type:"scatter",data:{datasets:[{label:"廠牌/團體",data:tierPts,backgroundColor:tierPts.map(p=>p.x>=100000&&p.y>=10000?C.rate+"cc":p.y>=10000?C.green+"aa":C.blue+"88"),pointRadius:tierPts.map(p=>p.r),pointHoverRadius:tierPts.map(p=>p.r+3)}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>`${ctx.raw.gn}｜總訂閱 ${fmt(ctx.raw.x)}｜每人中位 ${fmt(ctx.raw.y)}｜成員 ${ctx.raw.members}｜集中 ${pctText(ctx.raw.head)}`}}},scales:{x:{type:"logarithmic",ticks:{color:TICK,callback:v=>fmt(v)},grid:{color:GRID},title:{display:true,text:"總訂閱（log）",color:TICK}},y:{type:"logarithmic",ticks:{color:TICK,callback:v=>fmt(v)},grid:{color:GRID},title:{display:true,text:"每人訂閱中位（log）",color:TICK}}}}});
  new Chart(agCmp,{type:"bar",data:{labels:["訂閱中位","成長中位%","Active%","黏著中位"],datasets:[{label:"團體",data:[val(g1,c=>c.s),val(g1,c=>((GROW.channels[c.id]||{}).mom_3m||0)*100),val(g1,c=>((GROW.channels[c.id]||{}).ac==="Active"?100:0)),val(g1,c=>(c.r&&c.s)?c.r/c.s*100:null)],backgroundColor:C.cum},{label:"個人",data:[val(g0,c=>c.s),val(g0,c=>((GROW.channels[c.id]||{}).mom_3m||0)*100),val(g0,c=>((GROW.channels[c.id]||{}).ac==="Active"?100:0)),val(g0,c=>(c.r&&c.s)?c.r/c.s*100:null)],backgroundColor:C.green}]},options:opts()});
  const labels=["1","2","3-4","5-9","10-19","20+"],counts=Array(labels.length).fill(0);stats.forEach(x=>{const i=x.members<3?x.members-1:x.members<5?2:x.members<10?3:x.members<20?4:5;counts[i]++;});
  new Chart(agSize,{type:"bar",data:{labels,datasets:[{label:"團體數",data:counts,backgroundColor:C.rate}]},options:opts()});
}

function buildReport(){
  const years=[...new Set(ACT.filter(d=>!d.partial).map(d=>d.quarter.slice(0,4)))].filter(y=>+y>=2023); repYear.innerHTML=years.map(y=>`<option>${y}</option>`).join("")+'<option value="latest">最新狀態</option>'; repYear.value=years[years.length-1]||"latest";
  const bz={game:"遊戲",chat:"雜談",singing:"歌回",shorts:"短影音",asmr:"ASMR",collab:"連動",announcement:"公告",other:"其他"}, maxB=o=>{const e=Object.entries(o||{}).sort((a,b)=>b[1]-a[1])[0];return e?bz[e[0]]||e[0]:"—";}, range=n=>[...Array(n).keys()];
  function render(){const rows=ACT.filter(d=>!d.partial),y=repYear.value,cur=y==="latest"?rows[rows.length-1]:rows.filter(d=>d.quarter.startsWith(y)).slice(-1)[0],coh=COH.series.filter(d=>d.quarter.startsWith(cur.quarter.slice(0,4))),peak=COH.series.reduce((a,b)=>b.debuts>a.debuts?b:a),nat=Object.entries(COH.current.nationality).slice(0,3).map(([k,v])=>`${k} ${fmt(v)}`).join("、"),sh=cur.topvid_buckets||{},sht=Object.values(sh).reduce((a,x)=>a+x,0)||1,peakH=range(24).reduce((a,b)=>STM.yt.industry.hours[b]>STM.yt.industry.hours[a]?b:a,0);
    const dual=Object.keys(XPLAT.channels||{}).length, topDual=Object.values(XPLAT.channels||{}).filter(x=>x.yt_pct>=90&&x.tw_pct>=90).length, topShare=(cur.yt_top10_share*100).toFixed(1);
    const story=[["追蹤台V",fmt(cur.tracked_channels),`近期活躍 ${fmt(cur.recently_active_any)}，活躍率 ${cur.activation_rate}%`],["雙棲頻道",fmt(dual),`${fmt(topDual)} 個同時在 YT/Twitch 前 10%`],["長尾壓力",topShare+"%",`前 10 大訂閱佔比；中位數 ${fmt(cur.yt_subs_median)}`],["內容主軸",maxB(cur.topvid_buckets),`短影音佔熱門影片 ${((sh.shorts||0)/sht*100).toFixed(1)}%`],["開台尖峰",peakH+" 時",`這是開台時間，不是同接尖峰`]];
    const chapters=[["第一章","台V不是小圈圈，是一個可量測的長尾市場",fmt(cur.tracked_channels),`目前追蹤 ${fmt(cur.tracked_channels)} 個頻道，近期活躍 ${fmt(cur.recently_active_any)}。直播開場可以先問：這裡面誰真的還在動？`],["第二章","平台分工正在成形",fmt(dual),`雙棲頻道 ${fmt(dual)} 個，其中 ${fmt(topDual)} 個同時站進 YouTube/Twitch 前 10%。這適合接到雙棲象限圖。`],["第三章","大者恆大，但長尾還在變厚",topShare+"%",`前 10 大吃掉 ${topShare}% 訂閱；同時訂閱中位數只有 ${fmt(cur.yt_subs_median)}，適合談新人卡位與流量集中。`],["第四章","作息資料能講開台生態，不能冒充同接",peakH+" 時",`YouTube 開台尖峰在台灣時間 ${peakH} 時。這是開台時間，不是觀看尖峰，避免把估算指標講成真同接。`]];
    const txt=[["產業規模",`追蹤頻道 <b>${fmt(cur.tracked_channels)}</b>，近期活躍 <b>${fmt(cur.recently_active_any)}</b>（活躍率 ${cur.activation_rate}%）。YouTube 訂閱中位數 ${fmt(cur.yt_subs_median)}，Twitch 近期活躍 ${fmt(cur.recently_active_twitch)}。`],["進出場動態",`出道高峰在 ${peak.quarter}，單季 ${peak.debuts} 人；${cur.quarter.slice(0,4)} 年出道 ${fmt(coh.reduce((a,x)=>a+x.debuts,0))}、畢業 ${fmt(coh.reduce((a,x)=>a+x.graduations,0))}。`],["內容趨勢",`熱門影片以 <b>${maxB(cur.topvid_buckets)}</b> 為主，短影音佔 ${((sh.shorts||0)/sht*100).toFixed(1)}%；直播內容主幹為 ${maxB(cur.yt_live_buckets)}。`],["平台版圖",`近期活躍中 YouTube ${fmt(cur.recently_active_yt)}、Twitch ${fmt(cur.recently_active_twitch)}；雙棲頻道 ${fmt(dual)}，其中 ${fmt(topDual)} 個同時位在 YouTube/Twitch 平台內前 10%。`],["集中度",`前 10 大佔全體訂閱 ${topShare}%，訂閱中位數 ${fmt(cur.yt_subs_median)}，長尾持續變厚。`],["世代組成",`國籍前三為 ${nat}；團體 : 個人 = ${fmt(COH.current.group_split.group)} : ${fmt(COH.current.group_split.indie)}。`],["生命週期",`典型台 V 出道 12 個月生命週期中位為 ${GROW.lifecycle.median[12]} 倍初始訂閱，前段 p75 為 ${GROW.lifecycle.p75[12]} 倍。`],["開台生態",`YouTube 開台尖峰落在台灣時間 ${peakH} 時；作息資料已補完 7/7，但這是開台時間，不是觀看尖峰。`]];
    reportBody.innerHTML=`<div class="story-grid">${story.map(x=>`<div class="story-card"><div class="l">${x[0]}</div><div class="v">${x[1]}</div><div class="d">${x[2]}</div></div>`).join("")}</div><div class="chapter-grid">${chapters.map(x=>`<div class="chapter"><div class="eyebrow">${x[0]}</div><h3>${x[1]}</h3><div class="big">${x[2]}</div><p>${x[3]}</p></div>`).join("")}</div>`+txt.map(([h,p])=>`<div class="faq-card"><h4>${h}</h4><div class="faq-line">${p}</div></div>`).join(""); reportBody.dataset.text=story.map(x=>`${x[0]}：${x[1]}｜${x[2]}`).join("\\n")+"\\n\\n"+chapters.map(x=>`${x[0]} ${x[1]}\\n${x[2]}｜${x[3]}`).join("\\n\\n")+"\\n\\n"+txt.map(([h,p])=>h+"\\n"+p.replace(/<[^>]+>/g,"")).join("\\n\\n");}
  repYear.onchange=render; repCopy.onclick=async()=>{await navigator.clipboard.writeText(reportBody.dataset.text||"");repStatus.textContent="已複製";}; render();
}

function buildGrowth(inclP){
  const esc=s=>(s==null?"":String(s)).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
  const pct=v=>v==null||!isFinite(v)?"—":(v*100).toFixed(1)+"%";
  const nowMonth=new Date().toISOString().slice(0,7), months=GROW.months.filter(m=>m<=nowMonth), wd=["一","二","三","四","五","六","日"];
  const pctArr=a=>{const t=a.reduce((x,y)=>x+y,0)||1;return a.map(v=>+(v/t*100).toFixed(1));};
  const clearCharts=()=>["gwTraj","gwLife","gwSurv","gwEvt","gwX1","gwX2","gwX3","gwX4","gwHour","gwWeek","gwMonth"].forEach(k=>{if(store[k]){store[k].destroy();store[k]=null;}});
  const medSeries=rows=>months.map((m,i)=>{const vals=rows.map(c=>c.series&&c.series[i]).filter(v=>v!=null); if(!vals.length)return null; vals.sort((a,b)=>a-b); return vals[Math.floor(vals.length/2)];});
  const selected=()=>gwChannel&&gwChannel.id?GROW.channels[gwChannel.id]:null;
  function panel(el,html){document.getElementById(el).innerHTML=html;}
  function kpiRow(items){return `<div class="kpis">${items.map(x=>`<div class="kpi"><div class="l">${x[0]}</div><div class="v">${x[1]}</div><div class="d">${x[2]||""}</div></div>`).join("")}</div>`;}
  function renderTraj(){
    clearCharts(); const c=selected();
    if(!c||!c.series){
      const top=Object.entries(GROW.channels).filter(([,x])=>x.mom_3m!=null).sort((a,b)=>b[1].mom_3m-a[1].mom_3m).slice(0,8);
      panel("gw_traj",`<div class="insight">未選頻道時顯示近 3 月動能最高者。早期月份樣本稀疏，請搭配分組比較看。</div><div class="grid">${top.map(([id,x])=>`<div class="faq-card"><h4>${esc(x.n||id)}</h4><div class="faq-line">目前 ${fmt(x.subs_now)}，近 3 月 ${pct(x.mom_3m)}，年化 ${pct(x.cagr_yr)}</div></div>`).join("")}</div>`);
      return;
    }
    const all=Object.values(GROW.channels).filter(x=>x.series);
    const cohort=all.filter(x=>String(x.d||"").slice(0,4)===String(c.d||"").slice(0,4));
    panel("gw_traj",kpiRow([["YT 目前訂閱",fmt(c.subs_now),c.peak_m?"高點 "+c.peak_m:""],["YT 年化成長",pct(c.cagr_yr)],["YT 近 3 月動能",pct(c.mom_3m)],["YT 距高點回落",pct(c.drawdown)],["Twitch 目前追隨",fmt(c.tw_now)],["Twitch 年化成長",pct(c.tw_cagr_yr)],["Twitch 近 3 月動能",pct(c.tw_mom_3m)],["Twitch 距高點回落",pct(c.tw_drawdown)]])+`<div class="note">YouTube 訂閱與 Twitch 追隨語意不同，左右軸只看各自趨勢，不可直接比較絕對高低。</div><div class="card full"><h3>月度訂閱 / 追隨軌跡</h3><p class="desc">YT 訂閱（左軸）+ Twitch 追隨（右軸）+ YT 同屆/全體中位線</p><div class="box tall"><canvas id="gwTraj"></canvas></div></div>`);
    store.gwTraj=new Chart(gwTraj,{type:"line",data:{labels:months,datasets:[
      {label:"YT 訂閱",data:c.series.slice(0,months.length),borderColor:C.green,tension:.2,yAxisID:"y"},
      {label:"Twitch 追隨",data:c.series_tw?c.series_tw.slice(0,months.length):[],borderColor:C.tw,tension:.2,yAxisID:"y1"},
      {label:"同屆中位",data:medSeries(cohort),borderColor:C.rate,borderDash:[5,4],tension:.2},
      {label:"全體中位",data:medSeries(all),borderColor:C.blue,borderDash:[2,3],tension:.2}]},options:opts({y1:{position:"right",ticks:{color:TICK},grid:{drawOnChartArea:false}}})});
  }
  function survival(groupFn){
    const last=months[months.length-1]+"-01", lastD=new Date(last), rows=[];
    Object.values(GROW.channels).forEach(c=>{if(!c.d)return; const d=new Date(c.d); if(isNaN(d))return; const grad=c.grad&&c.ac==="Graduated"?new Date(c.grad):null; const end=grad&&!isNaN(grad)?grad:lastD; const m=(end.getFullYear()-d.getFullYear())*12+(end.getMonth()-d.getMonth()); if(m>=0)rows.push({m,event:!!grad,g:groupFn?groupFn(c):"全體"});});
    const groups=[...new Set(rows.map(r=>r.g))], x=[...Array(49).keys()];
    return groups.map(g=>{let s=1; const y=[]; x.forEach(i=>{const at=rows.filter(r=>r.g===g&&r.m>=i).length; const ev=rows.filter(r=>r.g===g&&r.m===i&&r.event).length; if(at>0)s*=1-ev/at; y.push(+(s*100).toFixed(1));}); return {label:g,data:y};});
  }
  function renderLife(){
    clearCharts(); const c=selected();
    panel("gw_life",`<div class="note"><b>存活率偏樂觀：</b>追蹤名單為現存記載，含倖存者偏差；早被清單刪除者未必在列。</div><div class="grid"><div class="card"><h3>典型生命週期曲線</h3><p class="desc">出道後月數對齊，訂閱相對初始值</p><div class="box tall"><canvas id="gwLife"></canvas></div></div><div class="card"><h3>近似存活曲線</h3><p class="desc">事件=Graduated，Active 右設限；團體/個人對照</p><div class="box tall"><canvas id="gwSurv"></canvas></div></div></div>`);
    const ds=[{label:"p25",data:GROW.lifecycle.p25,borderColor:"#5b6377",borderDash:[3,3],tension:.2},{label:"中位",data:GROW.lifecycle.median,borderColor:C.green,tension:.2},{label:"p75",data:GROW.lifecycle.p75,borderColor:"#5b6377",borderDash:[3,3],tension:.2}];
    if(c&&c.series&&c.d){const start=new Date(c.d); const own=[]; const base=c.series.find(v=>v); months.forEach((m,i)=>{const d=new Date(m+"-01"); const x=(d.getFullYear()-start.getFullYear())*12+(d.getMonth()-start.getMonth()); if(x>=0&&x<=48)own[x]=base?c.series[i]/base:null;}); ds.push({label:c.n||gwChannel.n,data:own,borderColor:C.rate,tension:.2});}
    store.gwLife=new Chart(gwLife,{type:"line",data:{labels:GROW.lifecycle.x,datasets:ds},options:opts()});
    store.gwSurv=new Chart(gwSurv,{type:"line",data:{labels:GROW.lifecycle.x,datasets:survival(c=>c.g?"團體":"個人").map((d,i)=>Object.assign(d,{borderColor:i?C.blue:C.purple,tension:.2}))},options:opts({y:{ticks:{color:TICK,callback:v=>v+"%"},grid:{color:GRID},min:0,max:100}})});
  }
  function renderEvent(){
    clearCharts(); const c=gwChannel&&gwChannel.id?EVT.channels[gwChannel.id]:null;
    const rows=c&&c.events?c.events.slice().sort((a,b)=>b.date.localeCompare(a.date)).slice(0,30):[];
    panel("gw_event",`<div class="note">事件淨增長是事件後 14 天訂閱差的毛估，未扣除自然成長；事件靠標題比對，有漏判誤判，需人工查核。</div><div class="grid"><div class="card"><h3>事件類型吸粉中位數</h3><p class="desc">各類標題事件後 14 天訂閱淨增中位數</p><div class="box"><canvas id="gwEvt"></canvas></div></div><div class="card"><h3>選定頻道事件</h3><div style="max-height:330px;overflow:auto">${rows.length?rows.map(e=>`<div class="faq-line">${e.date} ${e.type}｜<a href="${esc(e.url)}" target="_blank">${esc(e.title)}</a><br>淨增長 ${fmt(e.delta)}（${pct(e.delta_pct)}）</div>`).join(""):`<p class="muted">未選頻道，或此頻道沒有偵測到事件。</p>`}</div></div></div>`);
    const labels=Object.keys(EVT.by_type), vals=labels.map(k=>EVT.by_type[k].median_delta||0);
    store.gwEvt=new Chart(gwEvt,{type:"bar",data:{labels,datasets:[{label:"中位淨增",data:vals,backgroundColor:C.rate}]},options:opts()});
  }
  function renderCross(){
    clearCharts(); const x=gwChannel&&gwChannel.id?XPLAT.channels[gwChannel.id]:null, ind=XPLAT.industry, ms=ind.months.filter(m=>m<=nowMonth);
    const idx=ms.map(m=>ind.months.indexOf(m));
    const note=x?`<div class="note">Twitch 追隨與 YouTube 訂閱語意不同，跨平台只比較平台內百分位。</div>${kpiRow([["主場",x.home],["YT 平台內百分位",x.yt_pct+"%"],["Twitch 平台內百分位",x.tw_pct+"%"],["近期傾斜",x.tilt],["YT 近3月",pct(x.yt_mom)],["Twitch 近3月",pct(x.tw_mom)]])}`:`<div class="note">未選頻道時顯示產業平台版圖。Twitch 線從 2023-07 起；總量圖僅看趨勢，不比較訂閱/追隨絕對高低。</div>`;
    panel("gw_cross",note+`<div class="grid"><div class="card full"><h3>雙棲象限：誰在兩個平台都站得住？</h3><p class="desc">每個點是雙棲頻道；X=YouTube 平台內百分位，Y=Twitch 平台內百分位。${x?`<b>橘色大點</b>為目前選定頻道（${esc(gwChannel.n||gwChannel.id||"")}）。`:""}</p><div class="box tall"><canvas id="gwX4"></canvas></div></div><div class="card"><h3>平台存在型態</h3><div class="box"><canvas id="gwX1"></canvas></div></div><div class="card"><h3>平台總量趨勢</h3><div class="box"><canvas id="gwX2"></canvas></div></div><div class="card full"><h3>出道屆平台選擇</h3><div class="box"><canvas id="gwX3"></canvas></div></div></div>`);
    const pts=Object.entries(XPLAT.channels).map(([id,c])=>({x:c.yt_pct,y:c.tw_pct,n:c.n||id,home:c.home,tilt:c.tilt,id})).filter(p=>isFinite(p.x)&&isFinite(p.y));
    const datasets=[{label:"雙棲頻道",data:pts,backgroundColor:pts.map(p=>p.x>=90&&p.y>=90?C.rate+"cc":p.home==="Twitch"?C.tw+"99":p.home==="YT"?C.blue+"99":C.green+"aa"),pointRadius:4,pointHoverRadius:7}];
    if(x)datasets.push({label:gwChannel.n||gwChannel.id||"選定頻道",data:[{x:x.yt_pct,y:x.tw_pct,n:gwChannel.n||gwChannel.id,home:x.home,tilt:x.tilt}],backgroundColor:C.amber||"#ffb454",borderColor:"#fff",borderWidth:2,pointRadius:10,pointHoverRadius:13,pointStyle:"star"});
    store.gwX4=new Chart(document.getElementById("gwX4"),{type:"scatter",data:{datasets},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:!!x,labels:{color:TICK}},tooltip:{callbacks:{label:ctx=>`${ctx.raw.n}｜YT ${ctx.raw.x}% / TW ${ctx.raw.y}%｜${ctx.raw.home}｜${ctx.raw.tilt}`}}},scales:{x:{min:0,max:100,ticks:{color:TICK,callback:v=>v+"%"},grid:{color:GRID},title:{display:true,text:"YouTube 平台內百分位",color:TICK}},y:{min:0,max:100,ticks:{color:TICK,callback:v=>v+"%"},grid:{color:GRID},title:{display:true,text:"Twitch 平台內百分位",color:TICK}}}}});
    store.gwX1=new Chart(document.getElementById("gwX1"),{type:"line",data:{labels:ms,datasets:[
      {label:"YT only",data:idx.map(i=>ind.active_yt_only[i]),borderColor:C.blue,tension:.2},
      {label:"TW only",data:idx.map(i=>ind.active_tw_only[i]),borderColor:C.tw,tension:.2},
      {label:"雙棲",data:idx.map(i=>ind.active_dual[i]),borderColor:C.green,tension:.2}]},options:opts()});
    store.gwX2=new Chart(document.getElementById("gwX2"),{type:"line",data:{labels:ms,datasets:[
      {label:"YT 訂閱總量",data:idx.map(i=>ind.yt_subs_total[i]),borderColor:C.green,tension:.2,yAxisID:"y"},
      {label:"Twitch 追隨總量",data:idx.map(i=>ind.tw_fol_total[i]),borderColor:C.tw,tension:.2,yAxisID:"y1"}]},options:opts({y1:{position:"right",ticks:{color:TICK},grid:{drawOnChartArea:false}}})});
    const years=Object.keys(ind.debut_cohort_platform).filter(y=>+y>=2022).sort();
    store.gwX3=new Chart(document.getElementById("gwX3"),{type:"bar",data:{labels:years,datasets:[{label:"YT only",data:years.map(y=>ind.debut_cohort_platform[y].yt_only),backgroundColor:C.blue},{label:"Twitch present",data:years.map(y=>ind.debut_cohort_platform[y].tw_present),backgroundColor:C.tw}]},options:opts({},true)});
  }
  function renderSched(){
    if(!gwChannel&&curChannel){gwChannel=curChannel;const q=document.getElementById("gwQ"),st=document.getElementById("gwStatus");if(q)q.value=gwChannel.n||gwChannel.t||"";if(st)st.textContent=`已套用：${gwChannel.n||gwChannel.t||"未命名頻道"}`;}
    clearCharts(); const yt=STM.yt||{}, tw=STM.tw||{}, ytc=gwChannel&&gwChannel.id?(yt.channels[gwChannel.id]||(gwChannel.y?yt.channels[gwChannel.y]:null)):null, twc=gwChannel&&gwChannel.id?(tw.channels[gwChannel.id]||(gwChannel.t?tw.channels[gwChannel.t]:null)):null;
    const zh={mon:"週一",tue:"週二",wed:"週三",thu:"週四",fri:"週五",sat:"週六",sun:"週日"};
    const cov=(yt.coverage&&yt.coverage.weekdays||[]).map(x=>zh[x]||x).join("、")||"未標記";
    const done=(yt.coverage&&yt.coverage.weekdays||[]).length>=7;
    const streamNote=STM.note?"直播樣本已去除重複網址，並排除長時間待機室。":"";
    const noStreamData=gwChannel&&gwChannel.id&&!ytc&&!twc;
    panel("gw_sched",`<div class="note">目前以 ${cov} 資料截點取樣${done?"":"（分段補完中）"}。星期分布偏向這些日及鄰近日，未覆蓋星期是低估，不代表不開台；這是「開台時間」分布，不是觀看人數最多的時段，沒有同接資料，無法做觀眾權重。${streamNote}</div>${noStreamData?`<div class="note">「${esc(gwChannel.n||gwChannel.id)}」在直播作息資料中無足夠取樣（至少需 5 場），下方圖表僅顯示產業整體分布。</div>`:""}${kpiRow([["YT 開台樣本",ytc?fmt(ytc.n_streams):"—"],["Twitch 開台樣本",twc?fmt(twc.n_streams):"—"],["YT 最長斷更",ytc?fmt(ytc.gap_max_days)+" 天":"—"],["Twitch 最長斷更",twc?fmt(twc.gap_max_days)+" 天":"—"]])}<div class="grid"><div class="card"><h3>開台時段（台灣時間）</h3><div class="box"><canvas id="gwHour"></canvas></div></div><div class="card"><h3>星期分布</h3><p class="desc">樣本未滿 7 天時，未覆蓋星期會被低估。</p><div class="box"><canvas id="gwWeek"></canvas></div></div><div class="card full"><h3>每月開台樣本數</h3><p class="desc">最右端月份為進行中，僅到載入當天。</p><div class="box"><canvas id="gwMonth"></canvas></div></div></div>`);
    store.gwHour=new Chart(gwHour,{type:"bar",data:{labels:[...Array(24).keys()],datasets:[
      {label:"YT 產業%",data:pctArr(yt.industry.hours),backgroundColor:C.blue+"99"},
      {label:"Twitch 產業%",data:pctArr(tw.industry.hours),backgroundColor:C.tw+"99"},
      {label:"此頻道 YT%",data:ytc?pctArr(ytc.hours):[],backgroundColor:C.green+"99"},
      {label:"此頻道 Twitch%",data:twc?pctArr(twc.hours):[],backgroundColor:C.rate+"99"}]},options:opts()});
    store.gwWeek=new Chart(gwWeek,{type:"bar",data:{labels:wd,datasets:[
      {label:"YT 產業%",data:pctArr(yt.industry.weekday),backgroundColor:C.blue+"99"},
      {label:"Twitch 產業%",data:pctArr(tw.industry.weekday),backgroundColor:C.tw+"99"},
      {label:"此頻道 YT%",data:ytc?pctArr(ytc.weekday):[],backgroundColor:C.green+"99"},
      {label:"此頻道 Twitch%",data:twc?pctArr(twc.weekday):[],backgroundColor:C.rate+"99"}]},options:opts()});
    const smonths=[...new Set([...Object.keys(yt.industry.by_month),...Object.keys(tw.industry.by_month)])].filter(m=>m<=nowMonth).sort();
    store.gwMonth=new Chart(gwMonth,{type:"line",data:{labels:smonths.map(m=>m===nowMonth?m+"（進行中）":m),datasets:[
      {label:"YT 產業開台樣本",data:smonths.map(m=>yt.industry.by_month[m]||0),borderColor:C.blue,tension:.2,segment:{borderDash:c=>c.p1DataIndex===smonths.length-1?[5,4]:undefined}},
      {label:"Twitch 產業開台樣本",data:smonths.map(m=>tw.industry.by_month[m]||0),borderColor:C.tw,tension:.2,segment:{borderDash:c=>c.p1DataIndex===smonths.length-1?[5,4]:undefined}}]},options:opts()});
  }
  const subs=[["gw_traj","成長軌跡",renderTraj],["gw_life","生命週期&存活",renderLife],["gw_event","事件吸粉",renderEvent],["gw_cross","雙棲比較",renderCross],["gw_sched","開台作息",renderSched]];
  const sub=document.getElementById("gwSub"); sub.innerHTML=subs.map((s,i)=>`<div class="tab ${i?'':'on'}" data-id="${s[0]}">${s[1]}</div>`).join("");
  function show(id){subs.forEach(s=>document.getElementById(s[0]).style.display=s[0]===id?"block":"none"); sub.querySelectorAll(".tab").forEach(t=>t.classList.toggle("on",t.dataset.id===id)); subs.find(s=>s[0]===id)[2]();}
  sub.querySelectorAll(".tab").forEach(t=>t.onclick=()=>show(t.dataset.id));
  const list=document.getElementById("gwList"); if(list)list.innerHTML=DIRDATA.channels.filter(c=>c.n).slice(0,4000).map(c=>`<option value="${esc(c.n)}">`).join("");
  const q=document.getElementById("gwQ"), st=document.getElementById("gwStatus"), find=document.getElementById("gwFind"), clear=document.getElementById("gwClear");
  if(!gwChannel&&curChannel){gwChannel=curChannel;if(q)q.value=gwChannel.n||gwChannel.t||"";if(st)st.textContent=`已套用：${gwChannel.n||gwChannel.t||"未命名頻道"}`;}
  if(find)find.onclick=()=>{const c=findChannel(q.value); if(!c){st.textContent="找不到，請改貼 UCxxxx。";return;} gwChannel=c; st.textContent=`已套用：${c.n||c.t||"未命名頻道"}`; show(sub.querySelector(".tab.on").dataset.id);};
  if(clear)clear.onclick=()=>{gwChannel=null;if(q)q.value="";st.textContent="";show(sub.querySelector(".tab.on").dataset.id);};
  show("gw_traj");
}

function locate(o){ // o={s,v,f,r,rh,nat,d,label}
  const A=arrs(),rows=[];
  const g=locLong(o), st=locStream(o);
  renderHealth(o);
  if(o.label)rows.push({l:"頻道",v:o.label,d:DIRDATA.snapshot+" 數據"});
  const rs=rankIn(A.s,o.s);
  if(rs)rows.push({l:"YouTube 訂閱",v:fmt(o.s),d:"贏過 "+rs.pct+"%・第 "+rs.rank+"/"+rs.n+"・"+tierOf(o.s)});
  if(o.v!=null){const r=rankIn(A.v,o.v);rows.push({l:"累計觀看",v:fmt(o.v),d:r?"贏過 "+r.pct+"%":""});}
  if(o.f!=null){const r=rankIn(A.f,o.f);rows.push({l:"Twitch 追隨",v:fmt(o.f),d:r?"贏過 "+r.pct+"%・第 "+r.rank+"/"+r.n:""});}
  if(o.r!=null){const r=rankIn(A.r,o.r);rows.push({l:"近期中位觀看(熱度)",v:fmt(o.r),d:r?"贏過 "+r.pct+"%":""});}
  if(o.g!=null&&o.s!=null){const tArr=DIRDATA.channels.filter(c=>c.g===o.g&&c.s!=null).map(c=>c.s).sort((a,b)=>a-b);const rt=rankIn(tArr,o.s);if(rt)rows.push({l:(o.g?"團體勢":"個人勢")+"中排名",v:"第 "+rt.rank+"/"+rt.n,d:"贏過同類型 "+rt.pct+"%"});}
  const reff=(o.r!=null&&o.s)?o.r/o.s:null;
  if(reff!=null){const r=rankIn(A.reff,reff);rows.push({l:"黏著度 近期觀看/訂閱",v:reff.toFixed(3),d:r?"贏過 "+r.pct+"%":""});}
  const eff=(o.v!=null&&o.s)?o.v/o.s:null;
  if(eff!=null){const r=rankIn(A.eff,eff);rows.push({l:"曝光效率 累計觀看/訂閱",v:eff.toFixed(0),d:r?"贏過 "+r.pct+"%":""});}
  if(g){
    rows.push({l:"成長動能",v:(g.mom_3m>=0?"+":"")+pctText(g.mom_3m),d:"動能贏過 "+(pctile(LON.mom,g.mom_3m)??"—")+"%"});
    rows.push({l:"年化成長",v:pctText(g.cagr_yr),d:"贏過 "+(pctile(LON.cagr,g.cagr_yr)??"—")+"%"});
    rows.push({l:"距高點回落",v:"-"+pctText(g.drawdown),d:g.peak_m?"高點 "+g.peak_m:""});
    if(o.d&&g.subs_now){const m=monthsBetween(new Date(o.d),new Date(GROW.months[GROW.months.length-1]+"-01"));const i=Math.max(0,Math.min(GROW.lifecycle.x.length-1,m));const med=GROW.lifecycle.median[i];const sample=GROW.lifecycle.n_by_x[i];if(med){rows.push({l:"生命週期定位",v:`出道 ${m} 個月`,d:`${g.subs_now>med?"領先":"落後"}典型台V（你 ${fmt(g.subs_now)} / 中位 ${fmt(Math.round(med))}）${sample<20?"・同期樣本少":""}`});}}
    const nt=o.s<1000?1000:o.s<10000?10000:o.s<100000?100000:null;const gm=g.mom_3m!=null?Math.pow(1+g.mom_3m,1/3)-1:null;
    if(nt)rows.push({l:"升級預測",v:gm>0?`約 ${Math.ceil(Math.log(nt/o.s)/Math.log(1+gm))} 個月破 ${fmt(nt)}`:"近期成長停滯",d:"線性外推，僅參考"});
  }
  // cohort
  if(o.d){const yr=o.d.slice(0,4);const sub=DIRDATA.channels.filter(c=>c.d&&c.d.slice(0,4)===yr&&c.s!=null).map(c=>c.s).sort((a,b)=>a-b);
    const r=rankIn(sub,o.s);if(r)rows.push({l:yr+" 出道屆排名",v:"第 "+r.rank+"/"+r.n,d:"贏過 "+r.pct+"% 同屆"});}
  // milestone
  if(o.s!=null){const t10=A.s[Math.floor(A.s.length*0.9)];const med=A.s[Math.floor(A.s.length*0.5)];
    const nt=o.s<1000?1000:o.s<10000?10000:o.s<100000?100000:null;
    let parts=[];if(nt)parts.push("再 "+fmt(nt-o.s)+" 訂閱升級");
    if(o.s<med)parts.push("距中位數 "+fmt(med-o.s));else parts.push("已超過中位數");
    if(o.s<t10)parts.push("距前10% "+fmt(t10-o.s));else parts.push("已在前10%");
    rows.push({l:"里程碑",v:parts[0]||"—",d:parts.slice(1).join("・")});}
  if(rows.length===0)rows.push({l:"請輸入頻道或數字",v:"—"});
  kpis("kpi_loc",rows);
  drawLocCharts(o);
}

function drawLocCharts(o){
  Object.values(Chart.instances).filter(c=>c.canvas&&["lc1","lc2","lc3","lc4"].includes(c.canvas.id)).forEach(c=>c.destroy());
  const A=arrs(),desc=[...A.s].sort((a,b)=>b-a),subs=o.s;
  // lc1 rank curve
  const ds=[{label:"全體台V訂閱(高→低)",data:desc.map((v,i)=>({x:i+1,y:v})),borderColor:"#4aa8ff",borderWidth:1,pointRadius:0,showLine:true}];
  if(subs!=null){let r=desc.findIndex(v=>v<=subs);if(r<0)r=desc.length;ds.push({label:"你",data:[{x:r+1,y:subs}],borderColor:"#37d99a",backgroundColor:"#37d99a",pointRadius:8,pointStyle:"rectRot",showLine:false});}
  new Chart(lc1,{type:"scatter",data:{datasets:ds},options:{responsive:true,maintainAspectRatio:false,
    plugins:{legend:{labels:{color:TICK,font:{size:10.5}}}},
    scales:{x:{type:"linear",title:{display:true,text:"訂閱排名",color:TICK},ticks:{color:TICK},grid:{color:GRID}},
      y:{type:"logarithmic",title:{display:true,text:"訂閱數 (log)",color:TICK},ticks:{color:TICK},grid:{color:GRID}}}}});
  // lc2 tier
  const tiers=[[">100k",100000,Infinity,"#ff5a5f"],["10k–100k",10000,100000,"#ffb454"],["1k–10k",1000,10000,"#4aa8ff"],["<1k",0,1000,"#5b6377"]];
  const counts=tiers.map(t=>A.s.filter(v=>v>=t[1]&&v<t[2]).length),yt=subs!=null?tierOf(subs):null;
  new Chart(lc2,{type:"bar",data:{labels:tiers.map(t=>t[0]),datasets:[{label:"頻道數",data:counts,backgroundColor:tiers.map(t=>t[0]===yt?"#37d99a":t[3])}]},
    options:{indexAxis:"y",responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{color:TICK},grid:{color:GRID}},y:{ticks:{color:TICK},grid:{color:GRID}}}}});
  // lc3 radar
  const eff=(o.v!=null&&o.s)?o.v/o.s:null;
  const g=locLong(o), st=locStream(o), reff=(o.r!=null&&o.s)?o.r/o.s:null;
  const rad=[pctile(A.s,o.s),pctile(A.v,o.v),pctile(A.f,o.f),pctile(A.r,o.r),pctile(A.rh,o.rh),pctile(A.reff,reff),g?pctile(LON.mom,g.mom_3m):null,st?pctile(LON.reg,regularity(st)):null].map(x=>x==null?0:x);
  new Chart(lc3,{type:"radar",data:{labels:["訂閱","累計觀看","Twitch","近期熱度","爆紅力","黏著度","成長動能","開台規律"],
    datasets:[{label:"你的百分位",data:rad,borderColor:"#37d99a",backgroundColor:"#37d99a33",pointBackgroundColor:"#37d99a"}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:TICK,font:{size:10.5}}}},
      scales:{r:{min:0,max:100,angleLines:{color:GRID},grid:{color:GRID},pointLabels:{color:TICK,font:{size:11}},ticks:{color:TICK,backdropColor:"transparent",stepSize:25}}}}});
  // lc4 group percentile (subs)
  const labels=["全體"],vals=[pctile(A.s,o.s)||0];
  if(o.s!=null){const tsub=DIRDATA.channels.filter(c=>tierOf(c.s)===tierOf(o.s)).map(c=>c.s).filter(v=>v!=null).sort((a,b)=>a-b);labels.push("同級距");vals.push(pctile(tsub,o.s)||0);}
  if(o.nat){const nsub=DIRDATA.channels.filter(c=>c.nat===o.nat&&c.s!=null).map(c=>c.s).sort((a,b)=>a-b);labels.push("同國籍"+o.nat);vals.push(pctile(nsub,o.s)||0);}
  if(o.g!=null){const gsub=DIRDATA.channels.filter(c=>c.g===o.g&&c.s!=null).map(c=>c.s).sort((a,b)=>a-b);labels.push(o.g?"團體勢":"個人勢");vals.push(pctile(gsub,o.s)||0);}
  if(o.d){const yr=o.d.slice(0,4);const dsub=DIRDATA.channels.filter(c=>c.d&&c.d.slice(0,4)===yr&&c.s!=null).map(c=>c.s).sort((a,b)=>a-b);labels.push(yr+"屆");vals.push(pctile(dsub,o.s)||0);}
  new Chart(lc4,{type:"bar",data:{labels,datasets:[{label:"你的訂閱百分位",data:vals,backgroundColor:"#7c5cff"}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>"贏過 "+c.parsed.y+"%"}}},
      scales:{x:{ticks:{color:TICK},grid:{color:GRID}},y:{min:0,max:100,ticks:{color:TICK,callback:v=>v+"%"},grid:{color:GRID}}}}});
}

function parseCSV(text){const rows=[];let i=0,f="",row=[],q=false;text=text.replace(/^﻿/,"");
  while(i<text.length){const c=text[i];
    if(q){if(c=='"'){if(text[i+1]=='"'){f+='"';i++;}else q=false;}else f+=c;}
    else{if(c=='"')q=true;else if(c==','){row.push(f);f="";}else if(c=='\n'){row.push(f);rows.push(row);row=[];f="";}else if(c=='\r'){}else f+=c;}
    i++;}
  if(f.length||row.length){row.push(f);rows.push(row);}return rows;}
function csvObjs(text){const r=parseCSV(text);if(!r.length)return[];const h=r[0].map(x=>x.replace(/^﻿/,"").split("##").pop().trim());
  return r.slice(1).filter(x=>x.length>1).map(x=>{const o={};h.forEach((k,j)=>o[k]=x[j]);return o;});}
function num(v){if(v==null)return null;const s=(""+v).replace(/,/g,"").trim();if(!s)return null;const n=+s;return isNaN(n)?null:Math.round(n);}
async function refreshLive(st){
  const base="https://raw.githubusercontent.com/TaiwanVtuberData/TaiwanVtuberTrackingData/master/";
  const api="https://api.github.com/repos/TaiwanVtuberData/TaiwanVtuberTrackingData/contents/";
  st.textContent="抓取中…";
  try{
    async function mf(ym){const r=await fetch(api+ym);if(!r.ok)return null;const j=await r.json();return Array.isArray(j)?j:null;}
    const now=new Date();let ym=now.toISOString().slice(0,7);let files=await mf(ym);
    if(!files){const d=new Date(now.getFullYear(),now.getMonth()-1,1);ym=d.toISOString().slice(0,7);files=await mf(ym);}
    if(!files)throw new Error("無法列出資料夾");
    const pick=pre=>files.filter(f=>f.name.startsWith(pre)).map(f=>f.name).sort().pop();
    const bd=pick("basic-data_"),rc=pick("record_");if(!bd)throw new Error("找不到 basic-data");
    const [bdt,rct,tlt]=await Promise.all([fetch(base+ym+"/"+bd).then(r=>r.text()),
      rc?fetch(base+ym+"/"+rc).then(r=>r.text()):Promise.resolve(""),
      fetch(base+"DATA/TW_VTUBER_TRACK_LIST.csv").then(r=>r.text())]);
    const basic={},rec={};
    csvObjs(bdt).forEach(o=>{const id=(o["VTuber ID"]||"").trim();if(id)basic[id]=o;});
    csvObjs(rct).forEach(o=>{const id=(o["VTuber ID"]||"").trim();if(id)rec[id]=o;});
    const rmcol=r=>{let x=num(r["YouTube Recent Total Median View Count"]);if(x==null)x=num(r["YouTube Recent Median View Count"]);return x;};
    const rhcol=r=>{let x=num(r["YouTube Recent Total Highest View Count"]);if(x==null)x=num(r["YouTube Recent Highest View Count"]);return x;};
    const chans=[];
    csvObjs(tlt).forEach(t=>{const id=(t["ID"]||"").trim();if(!id||id.startsWith("##"))return;const b=basic[id],r=rec[id];
      const s=b?num(b["YouTube Subscriber Count"]):null,v=b?num(b["YouTube View Count"]):null,f=b?num(b["Twitch Follower Count"]):null;
      if(s==null&&f==null)return;
      chans.push({n:(t["Display Name"]||"").trim(),a:(t["Alias Names"]||"").trim(),y:(t["Youtube Channel ID"]||"").trim(),t:(t["Twitch Channel Name"]||"").trim(),nat:(t["Nationality"]||"").trim(),g:(t["Group Name"]||"").trim()?1:0,d:(t["Debut Date"]||"").trim(),s,v,f,r:r?rmcol(r):null,rh:r?rhcol(r):null});});
    if(!chans.length)throw new Error("解析為空");
    DIRDATA={snapshot:ym+" 即時("+bd.replace("basic-data_","").replace(".csv","")+")",source:DIR.source,channels:chans};
    st.textContent="已更新："+bd;return true;
  }catch(e){st.textContent="即時抓取失敗("+e.message+")，已退回內建 "+DIR.snapshot+"。";DIRDATA=DIR;return false;}
}
function readNumO(){return {s:num((document.getElementById("numSubs")||{}).value),
  f:num((document.getElementById("numFol")||{}).value),r:num((document.getElementById("numRec")||{}).value),
  d:((document.getElementById("numDebut")||{}).value||"").trim()?((document.getElementById("numDebut").value)+"-01-01"):"",
  g:((document.getElementById("numType")||{}).value==="")?null:+document.getElementById("numType").value};}
function buildLocate(){
  fillDatalist();
  const find=document.getElementById("locFind"),live=document.getElementById("locLive"),
    go=document.getElementById("numGo"),st=document.getElementById("locStatus");
  if(find)find.onclick=()=>{const c=findChannel(document.getElementById("locQ").value);
    if(!c){st.textContent="找不到，請改貼 UCxxxx 或用純數字。";return;}curChannel=c;st.textContent="";
    locate(Object.assign({},c,{label:c.n||c.t}));};
  if(go)go.onclick=()=>{curChannel=null;locate(Object.assign(readNumO(),{label:null}));};
  if(live)live.onclick=async()=>{await refreshLive(st);fillDatalist();
    if(curChannel){const c=findChannel(curChannel.n||curChannel.t)||curChannel;curChannel=c;
      locate(Object.assign({},c,{label:c.n||c.t}));}
    else locate(Object.assign(readNumO(),{label:null}));};
  drawLocCharts({});
}

const TABS=[["s_locate","定位你自己",buildLocate],["s_rank","排行榜",buildRank],["s_agency","廠牌生態",buildAgency],["s_report","產業報告",buildReport],["s_overview","活躍總覽",buildOverview],["s_cohort","進出場動態",buildCohort],
  ["s_conc","集中度與規模",buildConc],["s_pyr","訂閱級距金字塔",buildPyr],["s_content","內容與組成",buildContent],
  ["s_faq","常見問題",buildFaq],["s_growth","成長與生命週期",buildGrowth]];
let curTab="s_overview";
function showTab(id){
  curTab=id;
  document.querySelectorAll("section").forEach(s=>s.classList.toggle("on",s.id===id));
  document.querySelectorAll(".tab").forEach(t=>t.classList.toggle("on",t.dataset.id===id));
  if(!built[id]){ TABS.find(t=>t[0]===id)[2](document.getElementById("tp").checked); built[id]=true; }
}
function rebuildAll(){ // on partial toggle: destroy charts, reset
  Object.values(Chart.instances).forEach(c=>c.destroy());
  built={}; showTab(curTab);
}
document.getElementById("tabs").innerHTML=TABS.map(t=>`<div class="tab" data-id="${t[0]}">${t[1]}</div>`).join("");
document.querySelectorAll(".tab").forEach(t=>t.addEventListener("click",()=>showTab(t.dataset.id)));
document.getElementById("tp").addEventListener("change",rebuildAll);
document.getElementById("ft").innerHTML="指標定義：追蹤頻道=基本資料有資料的 VTuber 數；近期活躍=近期中位觀看>0（跨資料格式對齊）；top10 share=前10大訂閱÷全體訂閱；級距依 YouTube 訂閱數分；出道/畢業=追蹤名單記載日期歸入日曆季。基本資料始於 2022-03、YT 直播 2022-06、Twitch 直播 2023-09。"+COH.note+" 產生時間 __GEN__。";
showTab("s_locate");
</script>
</body></html>"""

HTML = HTML.replace("__ACT__",ACT_JSON).replace("__COH__",COH_JSON).replace("__CONC__",CONC_JSON).replace("__DIR__",DIR_JSON).replace("__GROW__",GROW_JSON).replace("__EVT__",EVT_JSON).replace("__STM__",STM_JSON).replace("__XPLAT__",XPLAT_JSON).replace("__GEN__",GEN)
out = ACT/"vtuber_activity_dashboard.html"
out.write_text(HTML, encoding="utf-8")
print("wrote", out, len(HTML),"bytes")
