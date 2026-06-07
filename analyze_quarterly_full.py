"""Integrated quarterly (month-end) metrics for the Taiwan VTuber dashboard.

Single x-axis = calendar quarter-end (Mar/Jun/Sep/Dec), snapshot closest to
month-end across archive + current. The in-progress month (2026-06) is kept and
flagged partial. Also reconstructs debut/graduation cohort dynamics from the
current track-list. Output: outputs/activity/quarterly_full.json
"""
import csv, io, json, subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "vtuber_index.sqlite"
OUT = ROOT / "outputs" / "activity"
REPO = {"archive": ROOT / "archive", "current": ROOT / "current"}
PARTIAL = {"2026-06"}

TITLE_KEYWORDS = {
    "singing": ["歌", "唱", "karaoke", "sing", "cover"],
    "chat": ["雜談", "閒聊", "聊天", "talk", "zatsu"],
    "game": ["遊戲", "game", "minecraft", "apex", "valorant", "lol", "原神"],
    "asmr": ["asmr", "助眠"],
    "collab": ["合作", "連動", "collab", "feat."],
    "shorts": ["shorts", "#shorts"],
    "announcement": ["公告", "告知", "重大", "初配信", "畢業", "新衣装", "新衣裝"],
}


def nh(name): return name.strip().lstrip("﻿").split("##", 1)[-1]
def show(repo, p): return subprocess.run(["git","-C",str(REPO[repo]),"show","HEAD:"+p],
                                         check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
def rd(data):
    t = data.decode("utf-8-sig", errors="replace")
    r = csv.DictReader(io.StringIO(t, newline=""))
    if r.fieldnames: r.fieldnames = [nh(f) for f in r.fieldnames]
    return list(r)
def ii(v):
    if v is None: return None
    s = str(v).replace(",","").strip()
    if not s: return None
    try: return int(float(s))
    except ValueError: return None
def median(vals):
    vs = sorted(v for v in vals if v is not None)
    if not vs: return None
    m = len(vs)//2
    return vs[m] if len(vs)%2 else int((vs[m-1]+vs[m])/2)
def pctl(vals, p):
    vs = sorted(v for v in vals if v is not None)
    if not vs: return None
    k = int(round((len(vs)-1)*p))
    return vs[k]
def parse_dt(v):
    if not v: return None
    try: return datetime.fromisoformat(str(v).replace("Z","+00:00"))
    except ValueError: return None
def buckets(titles):
    c = Counter()
    for t in titles:
        text = (t or "").lower()
        hit = [b for b,kw in TITLE_KEYWORDS.items() if any(k.lower() in text for k in kw)]
        for b in (hit or ["other"]): c[b]+=1
    return dict(c)
def q_label(dt):
    # map any date to calendar quarter-end ym label
    qm = ((dt.month-1)//3)*3+3
    return f"{dt.year}-{qm:02d}"


def pick(conn):
    q = """WITH m AS (SELECT repo,kind,substr(snapshot_at,1,7) ym,snapshot_at,path,
           ROW_NUMBER() OVER(PARTITION BY kind,substr(snapshot_at,1,7) ORDER BY snapshot_at DESC) rn
           FROM snapshots WHERE substr(snapshot_at,6,2) IN ('03','06','09','12'))
           SELECT kind,ym,repo,snapshot_at,path FROM m WHERE rn=1 ORDER BY kind,ym"""
    return list(conn.execute(q))


def pick_basic_monthly(conn):
    q = """WITH m AS (
             SELECT repo, substr(snapshot_at,1,7) ym, snapshot_at, path,
                    ROW_NUMBER() OVER(PARTITION BY substr(snapshot_at,1,7) ORDER BY snapshot_at DESC) rn
             FROM snapshots WHERE kind = 'basic-data'
           )
           SELECT ym, repo, snapshot_at, path FROM m WHERE rn = 1 ORDER BY ym"""
    return list(conn.execute(q))


def m_basic(rows):
    subs = [ii(r.get("YouTube Subscriber Count")) for r in rows]
    tw = [ii(r.get("Twitch Follower Count")) for r in rows]
    ids = {(r.get("VTuber ID") or "").strip() for r in rows if (r.get("VTuber ID") or "").strip()}
    pos = [s for s in subs if s and s>0]
    total = sum(pos)
    top10 = sum(sorted(pos, reverse=True)[:10])
    views = [ii(r.get("YouTube View Count")) for r in rows]
    vpos = [v for v in views if v and v > 0]
    vtotal = sum(vpos)
    vtop10 = sum(sorted(vpos, reverse=True)[:10])
    tiers = {"mega":0,"large":0,"mid":0,"small":0}
    for s in pos:
        if s>=100000: tiers["mega"]+=1
        elif s>=10000: tiers["large"]+=1
        elif s>=1000: tiers["mid"]+=1
        else: tiers["small"]+=1
    return {
        "tracked_channels": len(ids),
        "yt_channels_with_subs": len(pos),
        "yt_subs_total": total,
        "yt_subs_median": median(subs),
        "yt_subs_p90": pctl(subs,0.9),
        "yt_top10_share": round(top10/total,4) if total else None,
        "yt_view_top10_share": round(vtop10/vtotal,4) if vtotal else None,
        "yt_tier_mega": tiers["mega"], "yt_tier_large": tiers["large"],
        "yt_tier_mid": tiers["mid"], "yt_tier_small": tiers["small"],
        "twitch_channels_with_followers": sum(1 for v in tw if v and v>0),
        "twitch_followers_total": sum(v or 0 for v in tw),
        "twitch_followers_median": median(tw),
    }


def concentration():
    track = rd(show("current","DATA/TW_VTUBER_TRACK_LIST.csv"))
    track_info = {}
    for r in track:
        vid = (r.get("ID") or "").strip()
        if not vid or vid.startswith("##"):
            continue
        track_info[vid] = {
            "n": (r.get("Display Name") or r.get("Twitch Channel Name") or "").strip(),
            "ac": (r.get("Activity") or "").strip(),
        }
    conn = sqlite3.connect(DB_PATH)
    try: picks = pick_basic_monthly(conn)
    finally: conn.close()

    monthly = []
    for ym, repo, snap, path in picks:
        rows = rd(show(repo, path))
        channels = {}
        for r in rows:
            vid = (r.get("VTuber ID") or "").strip()
            if not vid: continue
            channels[vid] = {
                "id": vid,
                "n": (track_info.get(vid, {}).get("n") or vid),
                "ac": track_info.get(vid, {}).get("ac"),
                "s": ii(r.get("YouTube Subscriber Count")),
                "v": ii(r.get("YouTube View Count")),
            }
        monthly.append({"label": ym, "at": snap, "channels": channels})

    def select(granularity):
        if granularity == "month":
            return monthly
        if granularity == "quarter":
            return [m for m in monthly if m["label"][5:7] in ("03","06","09","12")]
        years = {}
        for m in monthly:
            years[m["label"][:4]] = m
        return [years[y] for y in sorted(years)]

    def build(records):
        out, prev = [], None
        for rec in records:
            rows = []
            for vid, cur in rec["channels"].items():
                old = prev["channels"].get(vid, {}) if prev else {}
                ps = None if prev is None or cur.get("s") is None or old.get("s") is None else max(0, cur["s"] - old["s"])
                pv = None if prev is None or cur.get("v") is None or old.get("v") is None else max(0, cur["v"] - old["v"])
                rows.append({"id": vid, "n": cur["n"], "ac": cur.get("ac"), "s": cur.get("s"), "v": cur.get("v"), "ps": ps, "pv": pv})
            out.append({"label": rec["label"], "at": rec["at"], "channels": rows})
            prev = rec
        return out

    return {
        "note": "累計觀看使用該時間截點的 YouTube View Count；期間觀看數使用本期累計觀看減前一期累計觀看，負向資料校正以 0 處理。",
        "month": build(select("month")),
        "quarter": build(select("quarter")),
        "year": build(select("year")),
    }


def m_record(rows):
    YT = ["YouTube Recent Total Median View Count","YouTube Recent Median View Count"]
    TW = ["Twitch Recent Median View Count"]
    def pos(r,cols):
        for c in cols:
            if c in r:
                v = ii(r.get(c))
                if v is not None and v>0: return True
        return False
    def val(r,cols):
        for c in cols:
            if c in r:
                v = ii(r.get(c))
                if v is not None: return v
        return None
    yt_med_vals = [val(r,YT) for r in rows]
    return {
        "recently_active_any": sum(1 for r in rows if pos(r,YT) or pos(r,TW)),
        "recently_active_yt": sum(1 for r in rows if pos(r,YT)),
        "recently_active_twitch": sum(1 for r in rows if pos(r,TW)),
        "recent_yt_median": median(yt_med_vals),
        "recent_yt_p90": pctl(yt_med_vals,0.9),
    }


def m_live(rows, pre):
    ids = {(r.get("VTuber ID") or "").strip() for r in rows if (r.get("VTuber ID") or "").strip()}
    return {pre+"_streams": len(rows), pre+"_hosts": len(ids),
            pre+"_buckets": buckets(r.get("Title") for r in rows)}


def m_topvid(rows, sdt):
    views = [ii(r.get("View Count")) for r in rows]
    ids = {(r.get("VTuber ID") or "").strip() for r in rows if (r.get("VTuber ID") or "").strip()}
    return {
        "topvid_channels": len(ids),
        "topvid_view_total": sum(v or 0 for v in views),
        "topvid_view_median": median(views),
        "topvid_view_max": max((v for v in views if v is not None), default=None),
        "topvid_buckets": buckets(r.get("Title") for r in rows),
    }


def cohort():
    rows = rd(show("current","DATA/TW_VTUBER_TRACK_LIST.csv"))
    rows = [r for r in rows if (r.get("ID") or "").strip() and not r["ID"].startswith("##")]
    debut, grad = defaultdict(int), defaultdict(int)
    nat_by_q = defaultdict(lambda: Counter())
    grp_by_q = defaultdict(lambda: Counter())
    for r in rows:
        d = parse_dt((r.get("Debut Date") or "").strip() or None)
        if d:
            ql = q_label(d); debut[ql]+=1
            nat = (r.get("Nationality") or "").strip() or "UNKNOWN"
            nat_by_q[ql][nat if nat in ("TW","HK","MY","JP") else "OTHER"] += 1
            grp_by_q[ql]["group" if (r.get("Group Name") or "").strip() else "indie"] += 1
        g = parse_dt((r.get("Graduation Date") or "").strip() or None)
        if g: grad[q_label(g)] += 1
    # quarterly series with cumulative net active
    quarters = sorted(set(list(debut)+list(grad)))
    # restrict to 2020-03 .. 2026-06 quarter labels
    quarters = [q for q in quarters if "2020-03" <= q <= "2026-06"]
    cum = 0
    # need cumulative from the very beginning (incl pre-2020)
    all_q = sorted(set(list(debut)+list(grad)))
    cum_map = {}
    run = 0
    for q in all_q:
        run += debut.get(q,0) - grad.get(q,0)
        cum_map[q] = run
    series = []
    for q in quarters:
        series.append({
            "quarter": q, "partial": q in PARTIAL,
            "debuts": debut.get(q,0), "graduations": grad.get(q,0),
            "net": debut.get(q,0)-grad.get(q,0),
            "cumulative_active": cum_map.get(q,0),
            "nat": dict(nat_by_q.get(q, Counter())),
            "grp": dict(grp_by_q.get(q, Counter())),
        })
    # current composition (whole list)
    comp_nat = Counter((r.get("Nationality") or "UNKNOWN").strip() for r in rows)
    comp_act = Counter((r.get("Activity") or "").strip() for r in rows)
    comp_grp = Counter("group" if (r.get("Group Name") or "").strip() else "indie" for r in rows)
    return {
        "series": series,
        "current": {
            "total": len(rows),
            "nationality": dict(comp_nat.most_common()),
            "activity": dict(comp_act.most_common()),
            "group_split": dict(comp_grp),
        },
        "note": "出道世代由目前追蹤名單的出道/畢業日期重建；已從名單完全移除的頻道不會被捕捉（含倖存者偏差）。",
    }


def main():
    conn = sqlite3.connect(DB_PATH)
    try: picks = pick(conn)
    finally: conn.close()
    quarters = {}
    for kind, ym, repo, snap, path in picks:
        rows = rd(show(repo, path))
        sdt = parse_dt(snap.replace(" ","T")+"+00:00")
        if kind=="basic-data": m=m_basic(rows)
        elif kind=="record": m=m_record(rows)
        elif kind=="livestreams": m=m_live(rows,"yt_live")
        elif kind=="twitch-livestreams": m=m_live(rows,"tw_live")
        elif kind=="top-videos": m=m_topvid(rows,sdt)
        else: m={}
        q = quarters.setdefault(ym, {"quarter":ym,"partial":ym in PARTIAL,"snap":{}})
        q.update(m); q["snap"][kind]={"repo":repo,"at":snap}
    series = [quarters[k] for k in sorted(quarters)]
    for s in series:
        if s.get("tracked_channels") and s.get("recently_active_any"):
            s["activation_rate"] = round(s["recently_active_any"]/s["tracked_channels"]*100,1)
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Quarter-end snapshots (global latest per quarter month across archive+current). "
                "Live-stream counts are instantaneous concurrent values (time-of-day sensitive). "
                "2026-06 = in-progress quarter (as of 2026-06-06), partial. "
                "Metrics recomputed at month-end nodes; figures may differ slightly from the earlier decks "
                "(which sampled month-first).",
        "activity": series,
        "cohort": cohort(),
        "concentration": concentration(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/"quarterly_full.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("activity quarters:", len(series), "cohort quarters:", len(out["cohort"]["series"]))
    print("latest:", series[-1]["quarter"], "top10_share=", series[-1].get("yt_top10_share"),
          "tiers=", {k:series[-1].get(k) for k in ("yt_tier_mega","yt_tier_large","yt_tier_mid","yt_tier_small")})


if __name__ == "__main__":
    main()
