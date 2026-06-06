"""Quarterly industry-activity series for Taiwan VTuber data.

Picks, for every calendar quarter-end month (Mar/Jun/Sep/Dec), the snapshot
closest to month-end (global MAX snapshot_at across archive + current repos),
then computes activity metrics from each CSV kind. The in-progress month is
kept but flagged partial (備註).
"""
import csv
import io
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "vtuber_index.sqlite"
OUT_DIR = ROOT / "outputs" / "activity"
REPO_PATH = {"archive": ROOT / "archive", "current": ROOT / "current"}
PARTIAL_YM = {"2026-06"}


def normalize_header(name):
    return name.strip().lstrip("﻿").split("##", 1)[-1]


def git_show(repo, path):
    proc = subprocess.run(
        ["git", "-C", str(REPO_PATH[repo]), "show", "HEAD:" + path],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.stdout


def read_csv_bytes(data):
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames:
        reader.fieldnames = [normalize_header(f) for f in reader.fieldnames]
    return list(reader)


def to_int(value):
    if value is None:
        return None
    t = str(value).replace(",", "").strip()
    if not t:
        return None
    try:
        return int(float(t))
    except ValueError:
        return None


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def pick_snapshots(conn):
    q = """
    WITH m AS (
      SELECT repo, kind, substr(snapshot_at,1,7) AS ym, snapshot_at, path,
             ROW_NUMBER() OVER (PARTITION BY kind, substr(snapshot_at,1,7)
                                ORDER BY snapshot_at DESC) AS rn
      FROM snapshots
      WHERE substr(snapshot_at,6,2) IN ('03','06','09','12'))
    SELECT kind, ym, repo, snapshot_at, path FROM m WHERE rn = 1 ORDER BY kind, ym
    """
    return list(conn.execute(q))


def metrics_basic(rows):
    subs = [to_int(r.get("YouTube Subscriber Count")) for r in rows]
    views = [to_int(r.get("YouTube View Count")) for r in rows]
    tw = [to_int(r.get("Twitch Follower Count")) for r in rows]
    ids = {(r.get("VTuber ID") or "").strip() for r in rows if (r.get("VTuber ID") or "").strip()}
    return {
        "tracked_channels": len(ids),
        "yt_channels_with_subs": sum(1 for v in subs if v and v > 0),
        "yt_subs_total": sum(v or 0 for v in subs),
        "yt_views_total": sum(v or 0 for v in views),
        "twitch_channels_with_followers": sum(1 for v in tw if v and v > 0),
        "twitch_followers_total": sum(v or 0 for v in tw),
    }


def metrics_record(rows):
    # Cross-era "recently active" = recent median view count > 0.
    # Column renamed from "YouTube Recent Median View Count" to
    # "YouTube Recent Total Median View Count" at the V5 schema (2023-09).
    YT = ["YouTube Recent Total Median View Count", "YouTube Recent Median View Count"]
    TW = ["Twitch Recent Median View Count"]

    def pos(r, cols):
        for c in cols:
            if c in r:
                v = to_int(r.get(c))
                if v is not None and v > 0:
                    return True
        return False

    yt_active = sum(1 for r in rows if pos(r, YT))
    tw_active = sum(1 for r in rows if pos(r, TW))
    any_active = sum(1 for r in rows if pos(r, YT) or pos(r, TW))
    ids = {(r.get("VTuber ID") or "").strip() for r in rows if (r.get("VTuber ID") or "").strip()}
    return {
        "record_tracked": len(ids),
        "recently_active_yt": yt_active,
        "recently_active_twitch": tw_active,
        "recently_active_any": any_active,
    }


def metrics_livestreams(rows, prefix):
    types = Counter((r.get("Video Type") or "").strip() or "(blank)" for r in rows)
    ids = {(r.get("VTuber ID") or "").strip() for r in rows if (r.get("VTuber ID") or "").strip()}
    return {prefix + "_streams": len(rows), prefix + "_hosts": len(ids), prefix + "_types": dict(types.most_common())}


def metrics_topvideos(rows, snapshot_dt):
    ids = {(r.get("VTuber ID") or "").strip() for r in rows if (r.get("VTuber ID") or "").strip()}
    cutoff = snapshot_dt - timedelta(days=90) if snapshot_dt else None
    recent, recent_ids = 0, set()
    for r in rows:
        pt = parse_dt(r.get("Publish Time"))
        if pt and cutoff and pt >= cutoff:
            recent += 1
            vid = (r.get("VTuber ID") or "").strip()
            if vid:
                recent_ids.add(vid)
    return {"topvideo_channels": len(ids), "topvideo_recent90d_videos": recent, "topvideo_recent90d_channels": len(recent_ids)}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        picks = pick_snapshots(conn)
    finally:
        conn.close()

    quarters, manifest = {}, []
    for kind, ym, repo, snapshot_at, path in picks:
        rows = read_csv_bytes(git_show(repo, path))
        snapshot_dt = parse_dt(snapshot_at.replace(" ", "T") + "+00:00")
        if kind == "basic-data":
            m = metrics_basic(rows)
        elif kind == "record":
            m = metrics_record(rows)
        elif kind == "livestreams":
            m = metrics_livestreams(rows, "yt_live")
        elif kind == "twitch-livestreams":
            m = metrics_livestreams(rows, "tw_live")
        elif kind == "top-videos":
            m = metrics_topvideos(rows, snapshot_dt)
        else:
            m = {}
        q = quarters.setdefault(ym, {"quarter": ym, "partial": ym in PARTIAL_YM, "snapshots": {}})
        q.update(m)
        q["snapshots"][kind] = {"repo": repo, "snapshot_at": snapshot_at}
        manifest.append({"kind": kind, "quarter": ym, "repo": repo, "snapshot_at": snapshot_at, "rows": len(rows), "path": path})

    series = [quarters[k] for k in sorted(quarters)]

    (OUT_DIR / "quarterly_activity.json").write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Quarter-end snapshots (global latest per quarter month across archive+current). "
                "Live-stream counts are instantaneous concurrent values at snapshot time (time-of-day sensitive). "
                "2026-06 is the in-progress quarter (data as of 2026-06-06), flagged partial.",
        "series": series,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    cols = ["quarter", "partial", "tracked_channels", "recently_active_any", "recently_active_yt",
            "recently_active_twitch", "yt_channels_with_subs", "yt_subs_total",
            "twitch_channels_with_followers", "twitch_followers_total",
            "yt_live_streams", "yt_live_hosts", "tw_live_streams", "tw_live_hosts",
            "topvideo_channels", "topvideo_recent90d_videos", "topvideo_recent90d_channels"]
    with (OUT_DIR / "quarterly_activity.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for s in series:
            w.writerow(s)

    with (OUT_DIR / "manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["kind", "quarter", "repo", "snapshot_at", "rows", "path"])
        w.writeheader()
        w.writerows(manifest)

    print("Quarters:", [s["quarter"] for s in series])
    print("Wrote", len(series), "quarters,", len(manifest), "extractions to", OUT_DIR)


if __name__ == "__main__":
    main()
