import argparse
import csv
import io
import json
import math
import sqlite3
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB = ROOT / "vtuber_index.sqlite"
OUT = ROOT / "outputs" / "activity"
CACHE = ROOT / "outputs" / "longitudinal"
REPO = {"archive": ROOT / "archive", "current": ROOT / "current"}

EVENT_KW = {
    "debut": ["初配信", "初配", "出道配信", "debut"],
    "3d": ["3d", "3D披露", "3d披露", "3d お披露目"],
    "anniversary": ["周年", "週年", "anniversary", "1st", "2nd", "3rd"],
    "birthday": ["生日", "生誕", "誕生日", "birthday"],
    "outfit": ["新衣装", "新衣裝", "new outfit", "お披露目"],
}

WEEKDAY_NUM = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
MAX_STREAM_AGE_H = 24


def nh(name):
    return name.strip().lstrip("\ufeff").split("##", 1)[-1]


def rd(data):
    rows = csv.DictReader(io.StringIO(data.decode("utf-8-sig", errors="replace"), newline=""))
    if rows.fieldnames:
        rows.fieldnames = [nh(f) for f in rows.fieldnames]
    return list(rows)


def ii(v):
    if v is None:
        return None
    s = str(v).replace(",", "").strip()
    if not s:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def median(vals):
    vals = sorted(v for v in vals if v is not None and math.isfinite(v))
    if not vals:
        return None
    n = len(vals)
    mid = n // 2
    return vals[mid] if n % 2 else (vals[mid - 1] + vals[mid]) / 2


def pctl(vals, q):
    vals = sorted(v for v in vals if v is not None and math.isfinite(v))
    if not vals:
        return None
    i = (len(vals) - 1) * q
    lo = math.floor(i)
    hi = math.ceil(i)
    if lo == hi:
        return vals[lo]
    return vals[lo] * (hi - i) + vals[hi] * (i - lo)


def show(repo, path):
    local = REPO[repo] / path
    if local.exists():
        return local.read_bytes()
    return subprocess.run(["git", "-C", str(REPO[repo]), "show", "HEAD:" + path],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def daily_latest(kinds):
    qs = ",".join("?" for _ in kinds)
    sql = f"""
    WITH ranked AS (
      SELECT repo,path,kind,snapshot_at,date(snapshot_at) d,blob_oid,
        ROW_NUMBER() OVER (
          PARTITION BY kind,date(snapshot_at)
          ORDER BY CASE repo WHEN 'current' THEN 1 ELSE 0 END DESC, snapshot_at DESC
        ) rn
      FROM files
      WHERE kind IN ({qs}) AND snapshot_at IS NOT NULL
    )
    SELECT repo,path,kind,snapshot_at,d,blob_oid FROM ranked WHERE rn=1 ORDER BY kind,d
    """
    with sqlite3.connect(DB) as conn:
        return [dict(zip(["repo", "path", "kind", "snapshot_at", "date", "blob_oid"], r)) for r in conn.execute(sql, kinds)]


def monthly_latest(kinds):
    qs = ",".join("?" for _ in kinds)
    sql = f"""
    WITH ranked AS (
      SELECT repo,path,kind,snapshot_at,date(snapshot_at) d,substr(snapshot_at,1,7) m,blob_oid,
        ROW_NUMBER() OVER (
          PARTITION BY kind,substr(snapshot_at,1,7)
          ORDER BY CASE repo WHEN 'current' THEN 1 ELSE 0 END DESC, snapshot_at DESC
        ) rn
      FROM files
      WHERE kind IN ({qs}) AND snapshot_at IS NOT NULL
    )
    SELECT repo,path,kind,snapshot_at,d,blob_oid FROM ranked WHERE rn=1 ORDER BY kind,d
    """
    with sqlite3.connect(DB) as conn:
        return [dict(zip(["repo", "path", "kind", "snapshot_at", "date", "blob_oid"], r)) for r in conn.execute(sql, kinds)]


def parse_weekdays(raw):
    if not raw:
        return None
    vals = [x.strip().lower() for x in raw.split(",") if x.strip()]
    if vals == ["all"] or "all" in vals:
        return list(WEEKDAY_NUM)
    bad = [x for x in vals if x not in WEEKDAY_NUM]
    if bad:
        raise ValueError(f"bad weekday values: {','.join(bad)}")
    return vals


def iter_contents(entries):
    by_repo = defaultdict(list)
    for e in entries:
        by_repo[e["repo"]].append(e)
    for repo, rows in by_repo.items():
        rows = [r for r in rows if r.get("blob_oid")]
        for start in range(0, len(rows), 100):
            chunk = rows[start:start + 100]
            oids = ("".join(r["blob_oid"] + "\n" for r in chunk)).encode("ascii")
            got = subprocess.run(["git", "-C", str(REPO[repo]), "cat-file", "--batch"],
                input=oids, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
            stream = io.BytesIO(got)
            for r in chunk:
                header = stream.readline().decode("ascii", errors="replace").strip()
                parts = header.split()
                if len(parts) < 3 or parts[1] != "blob":
                    raise RuntimeError(f"bad cat-file header for {r['path']}: {header}")
                size = int(parts[2])
                data = stream.read(size)
                stream.read(1)
                yield r, data


def track_list():
    rows = rd(show("current", "DATA/TW_VTUBER_TRACK_LIST.csv"))
    out = {}
    for r in rows:
        vid = (r.get("ID") or "").strip()
        if not vid or vid.startswith("##"):
            continue
        out[vid] = {
            "n": (r.get("Display Name") or "").strip(),
            "nat": (r.get("Nationality") or "").strip(),
            "g": 1 if (r.get("Group Name") or "").strip() else 0,
            "gn": (r.get("Group Name") or "").strip(),
            "d": (r.get("Debut Date") or "").strip(),
            "grad": (r.get("Graduation Date") or "").strip(),
            "ac": (r.get("Activity") or "").strip(),
        }
    return out


def parse_time(s):
    if not s:
        return None
    t = str(s).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(t)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=8)))


def valid_publish(dt, now=None):
    if dt is None:
        return False
    now = now or datetime.now(timezone(timedelta(hours=8)))
    return dt.year >= 2018 and dt <= now


def parse_snapshot_time(s):
    if not s:
        return None
    dt = datetime.fromisoformat(str(s).strip())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone(timedelta(hours=8)))


def build_panel(rebuild=False):
    p = CACHE / "panel_daily.json"
    if p.exists() and not rebuild:
        data = json.loads(p.read_text(encoding="utf-8"))
        if "tw_panel" in data:
            return data
        print("panel cache missing tw_panel; rebuilding")
    panel = defaultdict(dict)
    tw_panel = defaultdict(dict)
    views = defaultdict(dict)
    rows = daily_latest(["basic-data"])
    for i, (f, data) in enumerate(iter_contents(rows), 1):
        for r in rd(data):
            vid = (r.get("VTuber ID") or "").strip()
            if not vid:
                continue
            subs = ii(r.get("YouTube Subscriber Count"))
            fol = ii(r.get("Twitch Follower Count"))
            view = ii(r.get("YouTube View Count"))
            panel[vid][f["date"]] = subs if subs and subs > 0 else None
            tw_panel[vid][f["date"]] = fol if fol and fol > 0 else None
            if view and view > 0:
                views[vid][f["date"]] = view
        if i % 100 == 0:
            print("panel files", i, "/", len(rows))
    data = {"dates": sorted({d for s in panel.values() for d in s}), "panel": panel, "tw_panel": tw_panel, "views": views}
    p.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return data


def build_events_raw(rebuild=False):
    p = CACHE / "events_raw.json"
    if p.exists() and not rebuild:
        return json.loads(p.read_text(encoding="utf-8"))
    seen = {}
    rows = monthly_latest(["livestreams", "top-videos"])
    rows = sorted(rows, key=lambda r: (r["kind"], r["date"]))
    for i, (f, data) in enumerate(iter_contents(rows), 1):
        kind = f["kind"]
        for r in rd(data):
            url = (r.get("URL") or "").strip()
            vid = (r.get("VTuber ID") or "").strip()
            if not url or not vid:
                continue
            dt = parse_time(r.get("Publish Time"))
            if not dt:
                continue
            vc = ii(r.get("View Count"))
            cur = seen.get(url)
            item = {
                "kind": kind,
                "vid": vid,
                "title": (r.get("Title") or "").strip(),
                "time": dt.isoformat(),
                "date": dt.date().isoformat(),
                "hour": dt.hour,
                "weekday": dt.weekday(),
                "month": dt.strftime("%Y-%m"),
                "url": url,
                "view": vc,
            }
            if cur is None or (vc or 0) > (cur.get("view") or 0):
                seen[url] = item
        if i % 100 == 0:
            print("event files", i, "/", len(rows))
    data = list(seen.values())
    p.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return data


def stream_targets(kind, weekdays):
    rows = daily_latest([kind])
    allowed = {WEEKDAY_NUM[w] for w in weekdays}
    out = []
    for r in rows:
        d = datetime.fromisoformat(r["date"])
        if d.weekday() in allowed:
            out.append(r)
    return out


def build_streams_raw(kind, cache_name, weekdays, rebuild=False):
    p = CACHE / cache_name
    if p.exists() and not rebuild:
        data = json.loads(p.read_text(encoding="utf-8"))
    else:
        data = {"processed_paths": [], "streams": {}}
    targets = stream_targets(kind, weekdays)
    needs_age = any("min_age_h" not in v for v in (data.get("streams") or {}).values())
    processed = set() if needs_age else set(data.get("processed_paths") or [])
    pending = [r for r in targets if r["path"] not in processed]
    if pending:
        print(kind, "pending", len(pending), "/", len(targets))
    for i, (f, blob) in enumerate(iter_contents(pending), 1):
        snap_dt = parse_snapshot_time(f.get("snapshot_at"))
        for r in rd(blob):
            url = (r.get("URL") or "").strip()
            vid = (r.get("VTuber ID") or "").strip()
            if not url or not vid:
                continue
            dt = parse_time(r.get("Publish Time"))
            if not dt:
                continue
            age_h = None
            if snap_dt:
                age_h = (snap_dt - dt).total_seconds() / 3600
            prev = data["streams"].get(url, {})
            min_age = prev.get("min_age_h")
            if age_h is not None and age_h >= 0 and (min_age is None or age_h < min_age):
                min_age = round(age_h, 3)
            data["streams"][url] = {
                "kind": kind,
                "vid": vid,
                "title": (r.get("Title") or "").strip(),
                "time": dt.isoformat(),
                "date": dt.date().isoformat(),
                "hour": dt.hour,
                "weekday": dt.weekday(),
                "month": dt.strftime("%Y-%m"),
                "url": url,
                "view": ii(r.get("View Count")),
                "min_age_h": min_age,
            }
        processed.add(f["path"])
        if i % 100 == 0:
            print(kind, "processed new", i, "/", len(pending))
            data["processed_paths"] = sorted(processed)
            data["coverage_weekdays"] = weekdays
            p.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    data["processed_paths"] = sorted(processed)
    data["coverage_weekdays"] = weekdays
    p.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return data


def month_diff(a, b):
    return (b.year - a.year) * 12 + b.month - a.month


def month_key(s):
    return str(s)[:7]


def closest_before(series, day):
    keys = sorted(k for k, v in series.items() if v is not None and k <= day)
    return series[keys[-1]] if keys else None


def closest_after(series, day):
    keys = sorted(k for k, v in series.items() if v is not None and k >= day)
    return series[keys[0]] if keys else None


def growth_json(panel_data, meta):
    months = sorted({d[:7] for d in panel_data["dates"]})
    channels = {}
    monthly_by_vid = {}
    tw_monthly_by_vid = {}
    for vid, days in panel_data["panel"].items():
        by_m = {}
        for d in sorted(days):
            by_m[d[:7]] = days[d]
        monthly_by_vid[vid] = by_m
        vals = [v for v in by_m.values() if v is not None]
        if not vals:
            continue
        first_m = next((m for m in months if by_m.get(m)), None)
        last_m = next((m for m in reversed(months) if by_m.get(m)), None)
        first = by_m.get(first_m)
        last = by_m.get(last_m)
        peak_m, peak = max(((m, v) for m, v in by_m.items() if v is not None), key=lambda x: x[1])
        span = months.index(last_m) - months.index(first_m) if first_m and last_m else 0
        cagr = ((last / first) ** (12 / span) - 1) if first and last and span > 0 else None
        m3 = months[max(0, months.index(last_m) - 3)] if last_m else None
        base3 = by_m.get(m3) if m3 else None
        mom3 = (last / base3 - 1) if last and base3 else None
        item = dict(meta.get(vid, {}))
        item.update({"subs_now": last, "peak": peak, "peak_m": peak_m,
            "cagr_yr": None if cagr is None else round(cagr, 4),
            "mom_3m": None if mom3 is None else round(mom3, 4),
            "drawdown": round((peak - last) / peak, 4) if peak else None})
        if len(vals) >= 6:
            item["series"] = [by_m.get(m) for m in months]
        tw_days = (panel_data.get("tw_panel") or {}).get(vid, {})
        tw_by_m = {}
        for d in sorted(tw_days):
            tw_by_m[d[:7]] = tw_days[d]
        tw_monthly_by_vid[vid] = tw_by_m
        tw_vals = [v for v in tw_by_m.values() if v is not None]
        if tw_vals:
            tw_first_m = next((m for m in months if tw_by_m.get(m)), None)
            tw_last_m = next((m for m in reversed(months) if tw_by_m.get(m)), None)
            tw_first = tw_by_m.get(tw_first_m)
            tw_last = tw_by_m.get(tw_last_m)
            tw_peak_m, tw_peak = max(((m, v) for m, v in tw_by_m.items() if v is not None), key=lambda x: x[1])
            tw_span = months.index(tw_last_m) - months.index(tw_first_m) if tw_first_m and tw_last_m else 0
            tw_cagr = ((tw_last / tw_first) ** (12 / tw_span) - 1) if tw_first and tw_last and tw_span > 0 else None
            tw_m3 = months[max(0, months.index(tw_last_m) - 3)] if tw_last_m else None
            tw_base3 = tw_by_m.get(tw_m3) if tw_m3 else None
            tw_mom3 = (tw_last / tw_base3 - 1) if tw_last and tw_base3 else None
            item.update({"tw_now": tw_last, "tw_peak": tw_peak,
                "tw_cagr_yr": None if tw_cagr is None else round(tw_cagr, 4),
                "tw_mom_3m": None if tw_mom3 is None else round(tw_mom3, 4),
                "tw_drawdown": round((tw_peak - tw_last) / tw_peak, 4) if tw_peak else None})
            if len(tw_vals) >= 6:
                item["series_tw"] = [tw_by_m.get(m) for m in months]
        channels[vid] = item

    life = defaultdict(list)
    for vid, mvals in monthly_by_vid.items():
        d = (meta.get(vid, {}).get("d") or "")[:10]
        try:
            debut = datetime.fromisoformat(d)
        except ValueError:
            continue
        first_sub = next((v for m, v in sorted(mvals.items()) if v), None)
        if not first_sub:
            continue
        for m, v in mvals.items():
            if not v:
                continue
            obs = datetime.fromisoformat(m + "-01")
            x = month_diff(debut, obs)
            if 0 <= x <= 48:
                life[x].append(v / first_sub)
    lx = list(range(49))
    lifecycle = {
        "x": lx,
        "median": [round(median(life[i]), 4) if life[i] else None for i in lx],
        "p25": [round(pctl(life[i], .25), 4) if life[i] else None for i in lx],
        "p75": [round(pctl(life[i], .75), 4) if life[i] else None for i in lx],
        "n_by_x": [len(life[i]) for i in lx],
    }
    return {"generated_at": datetime.now().isoformat(timespec="seconds"), "resolution": "monthly",
        "months": months, "channels": channels, "lifecycle": lifecycle}


def pctile_py(vals, v):
    vals = sorted(x for x in vals if x is not None and math.isfinite(x))
    if v is None or not vals:
        return None
    n = sum(1 for x in vals if x <= v)
    return round(n / len(vals) * 100, 1)


def crossplatform_json(growth):
    months = growth["months"]
    channels = growth["channels"]
    yt_vals = [c.get("subs_now") for c in channels.values() if c.get("subs_now")]
    tw_vals = [c.get("tw_now") for c in channels.values() if c.get("tw_now")]
    out = {}
    for vid, c in channels.items():
        if not c.get("subs_now") or not c.get("tw_now"):
            continue
        yp = pctile_py(yt_vals, c.get("subs_now"))
        tp = pctile_py(tw_vals, c.get("tw_now"))
        diff = (yp or 0) - (tp or 0)
        home = "均衡" if abs(diff) < 10 else ("YT" if diff > 0 else "TW")
        ym, tm = c.get("mom_3m"), c.get("tw_mom_3m")
        if ym is None or tm is None or abs(ym - tm) < 0.03:
            tilt = "持平"
        else:
            tilt = "往YT傾斜" if ym > tm else "往Twitch傾斜"
        out[vid] = {"n": c.get("n"), "nat": c.get("nat"), "d": c.get("d"),
            "yt_subs": c.get("subs_now"), "tw_fol": c.get("tw_now"),
            "yt_pct": yp, "tw_pct": tp, "home": home,
            "yt_mom": ym, "tw_mom": tm, "tilt": tilt}
    active_yt_only, active_tw_only, active_dual, yt_total, tw_total = [], [], [], [], []
    for i, m in enumerate(months):
        yo = to = dual = yt_sum = tw_sum = 0
        for c in channels.values():
            yv = c.get("series", [None] * len(months))[i] if c.get("series") else None
            tv = c.get("series_tw", [None] * len(months))[i] if c.get("series_tw") else None
            if yv:
                yt_sum += yv
            if tv:
                tw_sum += tv
            if yv and tv:
                dual += 1
            elif yv:
                yo += 1
            elif tv:
                to += 1
        active_yt_only.append(yo); active_tw_only.append(to); active_dual.append(dual)
        yt_total.append(yt_sum); tw_total.append(tw_sum)
    cohort = {}
    for c in channels.values():
        y = (c.get("d") or "")[:4]
        if not y:
            continue
        cohort.setdefault(y, {"yt_only": 0, "tw_present": 0})
        if c.get("tw_now"):
            cohort[y]["tw_present"] += 1
        else:
            cohort[y]["yt_only"] += 1
    return {"generated_at": datetime.now().isoformat(timespec="seconds"), "channels": out,
        "industry": {"months": months, "active_yt_only": active_yt_only,
            "active_tw_only": active_tw_only, "active_dual": active_dual,
            "yt_subs_total": yt_total, "tw_fol_total": tw_total,
            "debut_cohort_platform": cohort}}


def event_type(title):
    low = (title or "").lower()
    for typ, kws in EVENT_KW.items():
        if any(k.lower() in low for k in kws):
            return typ
    return None


def events_json(events, panel_data):
    cand = []
    for e in events:
        typ = event_type(e.get("title"))
        if typ:
            x = dict(e)
            x["type"] = typ
            cand.append(x)
    grouped = defaultdict(list)
    for e in cand:
        grouped[(e["vid"], e["type"])].append(e)
    channels = defaultdict(lambda: {"events": []})
    by_type = defaultdict(list)
    for (vid, typ), rows in grouped.items():
        rows = sorted(rows, key=lambda e: e["date"])
        kept = []
        for e in rows:
            ed = datetime.fromisoformat(e["date"])
            dup = next((k for k in kept if abs((ed - datetime.fromisoformat(k["date"])).days) <= 3), None)
            if dup:
                if (e.get("view") or 0) > (dup.get("view") or 0):
                    kept[kept.index(dup)] = e
            else:
                kept.append(e)
        for e in kept:
            day = datetime.fromisoformat(e["date"])
            before_day = (day - timedelta(days=1)).date().isoformat()
            after_day = (day + timedelta(days=14)).date().isoformat()
            series = panel_data["panel"].get(vid, {})
            before = closest_before(series, before_day)
            after = closest_after(series, after_day)
            delta = after - before if before is not None and after is not None else None
            delta_pct = delta / before if delta is not None and before else None
            item = {"type": typ, "date": e["date"], "title": e["title"], "url": e["url"],
                "before": before, "after": after, "delta": delta,
                "delta_pct": None if delta_pct is None else round(delta_pct, 4)}
            channels[vid]["events"].append(item)
            if delta is not None:
                by_type[typ].append((delta, delta_pct))
    summary = {}
    for typ, vals in by_type.items():
        summary[typ] = {"n": len(vals), "median_delta": median([v[0] for v in vals]),
            "median_delta_pct": round(median([v[1] for v in vals if v[1] is not None]) or 0, 4)}
    return {"generated_at": datetime.now().isoformat(timespec="seconds"),
        "channels": channels, "by_type": summary,
        "note": "delta is a 14-day rough estimate and does not remove organic growth; title matching is noisy."}


def stream_block(raw):
    ch = defaultdict(lambda: {"hours": [0] * 24, "weekday": [0] * 7, "dates": []})
    ind_hours = [0] * 24
    ind_week = [0] * 7
    by_month = Counter()
    hbw = [[0] * 24 for _ in range(7)]
    now = datetime.now(timezone(timedelta(hours=8)))
    raw_count = len(raw.get("streams") or {})
    invalid_time = 0
    stale = 0
    future_or_old = 0
    for e in (raw.get("streams") or {}).values():
        dt = parse_time(e.get("time"))
        if not valid_publish(dt, now):
            invalid_time += 1
            if dt is None or dt.year < 2018 or (dt and dt > now):
                future_or_old += 1
            continue
        min_age = e.get("min_age_h")
        if min_age is None or min_age < 0 or min_age >= MAX_STREAM_AGE_H:
            stale += 1
            continue
        c = ch[e["vid"]]
        c["hours"][e["hour"]] += 1
        c["weekday"][e["weekday"]] += 1
        c["dates"].append(e["date"])
        ind_hours[e["hour"]] += 1
        ind_week[e["weekday"]] += 1
        by_month[e["month"]] += 1
        hbw[e["weekday"]][e["hour"]] += 1
    out = {}
    for vid, c in ch.items():
        dates = sorted(set(c.pop("dates")))
        gaps = [(datetime.fromisoformat(b) - datetime.fromisoformat(a)).days for a, b in zip(dates, dates[1:])]
        weeks = {datetime.fromisoformat(d).strftime("%G-%V") for d in dates}
        c.update({"n_streams": sum(c["hours"]), "first": dates[0] if dates else None,
            "last": dates[-1] if dates else None, "active_weeks": len(weeks),
            "gap_max_days": max(gaps) if gaps else 0,
            "peak_hour": max(range(24), key=lambda h: c["hours"][h]) if dates else None,
            "peak_weekday": max(range(7), key=lambda w: c["weekday"][w]) if dates else None})
        out[vid] = c
    return {"channels": out,
        "industry": {"hours": ind_hours, "weekday": ind_week, "by_month": dict(sorted(by_month.items())),
            "hour_by_weekday": hbw},
        "coverage": {"weekdays": raw.get("coverage_weekdays") or [], "n_snapshots": len(raw.get("processed_paths") or []),
            "n_streams": sum(ind_hours), "raw_streams": raw_count, "filtered_invalid_time": invalid_time,
            "filtered_future_or_old": future_or_old, "filtered_stale_waiting_room": stale,
            "max_stream_age_h": MAX_STREAM_AGE_H}}


def streaming_json(yt_raw, tw_raw):
    return {"generated_at": datetime.now().isoformat(timespec="seconds"),
        "yt": stream_block(yt_raw),
        "tw": stream_block(tw_raw),
        "note": "streams are URL-deduped from staged weekday daily snapshots and filtered to valid publish_time plus min_age_h < 24h to remove stale waiting rooms."}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--streams-weekdays", default=None)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    meta = track_list()
    panel = build_panel(args.rebuild)
    events = build_events_raw(args.rebuild)
    weekdays = parse_weekdays(args.streams_weekdays) or ["sun", "thu"]
    yt_streams = build_streams_raw("livestreams", "streams_raw.json", weekdays, args.rebuild)
    tw_streams = build_streams_raw("twitch-livestreams", "twitch_streams_raw.json", weekdays, args.rebuild)
    growth = growth_json(panel, meta)
    outputs = {
        "growth.json": growth,
        "events.json": events_json(events, panel),
        "streaming.json": streaming_json(yt_streams, tw_streams),
        "crossplatform.json": crossplatform_json(growth),
    }
    for name, data in outputs.items():
        p = OUT / name
        p.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(name, p.stat().st_size)


if __name__ == "__main__":
    main()
