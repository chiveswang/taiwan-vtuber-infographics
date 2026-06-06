import csv, io, json, subprocess
from collections import Counter, defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def show(p): return subprocess.run(["git","-C",str(ROOT/"current"),"show","HEAD:"+p],
    check=True,stdout=subprocess.PIPE).stdout
def nh(n): return n.strip().lstrip("﻿").split("##",1)[-1]
def rd(b):
    r=csv.DictReader(io.StringIO(b.decode("utf-8-sig",errors="replace"),newline=""))
    if r.fieldnames: r.fieldnames=[nh(f) for f in r.fieldnames]
    return list(r)
def ii(v):
    if not v: return None
    s=str(v).replace(",","").strip()
    if not s: return None
    try: return int(float(s))
    except: return None

TITLE_KEYWORDS = {
    "singing":["歌","唱","karaoke","sing","cover"],
    "chat":["雜談","閒聊","聊天","talk","zatsu"],
    "game":["遊戲","game","minecraft","apex","valorant","lol","原神"],
    "asmr":["asmr","助眠"],
    "collab":["合作","連動","collab","feat."],
    "shorts":["shorts","#shorts"],
    "announcement":["公告","告知","重大","初配信","畢業","新衣装","新衣裝"],
}

def buckets(titles):
    c = Counter()
    for t in titles:
        text = (t or "").lower()
        hit = [b for b,kw in TITLE_KEYWORDS.items() if any(k.lower() in text for k in kw)]
        for b in (hit or ["other"]):
            c[b] += 1
    return dict(c)

def raw(r, col):
    v = (r.get(col) or "").strip()
    return v or None

def latest_csv(kind):
    ym = BD.split("/", 1)[0]
    out = subprocess.run(["git","-C",str(ROOT/"current"),"ls-tree","-r","--name-only","HEAD",ym],
        check=True,stdout=subprocess.PIPE).stdout.decode("utf-8", errors="replace")
    prefix = f"{ym}/{kind}_"
    rows = sorted(p for p in out.splitlines() if p.startswith(prefix) and p.endswith(".csv"))
    if not rows:
        raise RuntimeError(f"no {kind} csv under {ym}")
    return rows[-1]

BD="2026-06/basic-data_2026-06-06-13-55-21.csv"
RC="2026-06/record_2026-06-06-13-08-43.csv"
TV=latest_csv("top-videos")
LS=latest_csv("livestreams")
basic={r["VTuber ID"].strip():r for r in rd(show(BD)) if (r.get("VTuber ID") or "").strip()}
rec={r["VTuber ID"].strip():r for r in rd(show(RC)) if (r.get("VTuber ID") or "").strip()}
tl=[r for r in rd(show("DATA/TW_VTUBER_TRACK_LIST.csv")) if (r.get("ID") or "").strip() and not r["ID"].startswith("##")]
top_rows=rd(show(TV))
live_rows=rd(show(LS))

def pickcol(r,cols):
    for c in cols:
        if c in r:
            v=ii(r.get(c))
            if v is not None: return v
    return None
def recmed(r): return pickcol(r,["YouTube Recent Total Median View Count","YouTube Recent Median View Count"])
def rechigh(r): return pickcol(r,["YouTube Recent Total Highest View Count","YouTube Recent Highest View Count"])

best_top = {}
titles_by_id = defaultdict(list)
for r in top_rows:
    vid = (r.get("VTuber ID") or "").strip()
    if not vid:
        continue
    title = (r.get("Title") or "").strip()
    if title:
        titles_by_id[vid].append(title)
    vc = ii(r.get("View Count"))
    if vc is not None and (vid not in best_top or vc > best_top[vid]["vc"]):
        best_top[vid] = {"title":title, "vc":vc, "url":raw(r, "URL")}

for r in live_rows:
    vid = (r.get("VTuber ID") or "").strip()
    title = (r.get("Title") or "").strip()
    if vid and title:
        titles_by_id[vid].append(title)

dirc=[]
for t in tl:
    vid=t["ID"].strip()
    b=basic.get(vid)
    subs=ii(b.get("YouTube Subscriber Count")) if b else None
    views=ii(b.get("YouTube View Count")) if b else None
    fol=ii(b.get("Twitch Follower Count")) if b else None
    img=(raw(b,"YouTube Thumbnail URL") or raw(b,"Twitch Thumbnail URL")) if b else None
    rr=rec.get(vid,{})
    rm=recmed(rr) if vid in rec else None
    rh=rechigh(rr) if vid in rec else None
    gn=(t.get("Group Name") or "").strip()
    if subs is None and fol is None:   # no data → skip
        continue
    dirc.append({
        "id":vid,
        "n":(t.get("Display Name") or "").strip(),
        "a":(t.get("Alias Names") or "").strip(),
        "y":(t.get("Youtube Channel ID") or "").strip(),
        "t":(t.get("Twitch Channel Name") or "").strip(),
        "nat":(t.get("Nationality") or "").strip(),
        "g":1 if gn else 0,
        "d":(t.get("Debut Date") or "").strip(),
        "s":subs,"v":views,"f":fol,"r":rm,"rh":rh,
        "lm":ii(rr.get("YouTube Recent Livestream Median View Count")),
        "vm":ii(rr.get("YouTube Recent Video Median View Count")),
        "lh":ii(rr.get("YouTube Recent Livestream Highest View Count")),
        "vh":ii(rr.get("YouTube Recent Video Highest View Count")),
        "pop":ii(rr.get("YouTube Recent Total Popularity")),
        "lhu":raw(rr,"YouTube Recent Livestream Highest Viewed URL"),
        "vhu":raw(rr,"YouTube Recent Video Highest Viewed URL"),
        "thu":raw(rr,"YouTube Recent Total Highest Viewed URL"),
        "tr":ii(rr.get("Twitch Recent Median View Count")),
        "gn":gn,
        "ac":(t.get("Activity") or "").strip(),
        "img":img,
        "tv":best_top.get(vid),
        "cb":buckets(titles_by_id.get(vid, [])),
    })
out={
    "snapshot":"2026-06-06",
    "source":{"repo":"TaiwanVtuberData/TaiwanVtuberTrackingData","branch":"master"},
    "channels":dirc,
}
p=ROOT/"outputs"/"activity"/"locate_directory.json"
p.write_text(json.dumps(out,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
print("channels:",len(dirc),"bytes:",p.stat().st_size)
subs=sorted(c["s"] for c in dirc if c["s"]); fol=sorted(c["f"] for c in dirc if c["f"])
print("with subs:",len(subs),"median:",subs[len(subs)//2],"max:",subs[-1])
print("with twitch followers:",len(fol))
