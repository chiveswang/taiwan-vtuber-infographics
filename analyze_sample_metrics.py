import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SAMPLE_DIR = ROOT / "quarterly_samples"
CSV_DIR = SAMPLE_DIR / "csv"
OUT_DIR = SAMPLE_DIR / "metrics"

TITLE_KEYWORDS = {
    "singing": ["歌", "唱", "karaoke", "sing", "cover", "cover曲"],
    "chat": ["雜談", "閒聊", "聊天", "talk", "zatsu"],
    "game": ["遊戲", "game", "minecraft", "apex", "valorant", "lol", "原神"],
    "asmr": ["asmr", "助眠"],
    "collab": ["合作", "連動", "collab", "feat."],
    "shorts": ["shorts", "#shorts"],
    "announcement": ["公告", "告知", "重大", "初配信", "畢業", "新衣装", "新衣裝"],
}


def normalize_header(name: str) -> str:
    return name.strip().lstrip("\ufeff").split("##", 1)[-1]


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames:
            reader.fieldnames = [normalize_header(field) for field in reader.fieldnames]
        return list(reader)


def to_int(value):
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def median(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return int((values[mid - 1] + values[mid]) / 2)


def percentile(values, ratio):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    index = math.ceil(len(values) * ratio) - 1
    index = min(max(index, 0), len(values) - 1)
    return values[index]


def first_int(row, *names):
    for name in names:
        value = to_int(row.get(name))
        if value is not None:
            return value
    return None


def vtuber_id(row):
    return (row.get("VTuber ID") or "").strip()


def parse_sample_path(path: Path):
    kind = path.parent.name
    match = re.match(r"(?P<ym>\d{4}-\d{2})_", path.name)
    if not match:
        raise ValueError(f"Cannot parse sample month from {path}")
    return kind, match.group("ym")


def write_rows(path: Path, rows: list[dict], headers: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def activity_ratio(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 6)


def bucket_keywords(title):
    text = (title or "").lower()
    buckets = []
    for bucket, keywords in TITLE_KEYWORDS.items():
        if any(keyword.lower() in text for keyword in keywords):
            buckets.append(bucket)
    return buckets or ["other"]


def analyze_basic_data(path: Path, rows: list[dict]):
    kind, ym = parse_sample_path(path)
    ids = {vtuber_id(row) for row in rows if vtuber_id(row)}
    youtube_subs = [to_int(row.get("YouTube Subscriber Count")) for row in rows]
    youtube_views = [to_int(row.get("YouTube View Count")) for row in rows]
    twitch_followers = [to_int(row.get("Twitch Follower Count")) for row in rows]
    return {
        "kind": kind,
        "year_month": ym,
        "rows": len(rows),
        "unique_vtubers": len(ids),
        "youtube_channels_with_subs": sum(1 for value in youtube_subs if value and value > 0),
        "youtube_subscriber_total": sum(value or 0 for value in youtube_subs),
        "youtube_subscriber_median": median(youtube_subs),
        "youtube_subscriber_p90": percentile(youtube_subs, 0.9),
        "youtube_subscriber_top10_total": sum(sorted((value or 0 for value in youtube_subs), reverse=True)[:10]),
        "youtube_view_total": sum(value or 0 for value in youtube_views),
        "youtube_view_median": median(youtube_views),
        "twitch_channels_with_followers": sum(1 for value in twitch_followers if value and value > 0),
        "twitch_follower_total": sum(value or 0 for value in twitch_followers),
        "twitch_follower_median": median(twitch_followers),
        "twitch_follower_p90": percentile(twitch_followers, 0.9),
    }


def analyze_record(path: Path, rows: list[dict]):
    kind, ym = parse_sample_path(path)
    ids = {vtuber_id(row) for row in rows if vtuber_id(row)}
    youtube_subs = [to_int(row.get("YouTube Subscriber Count")) for row in rows]
    recent_total_median = [
        first_int(
            row,
            "YouTube Recent Total Median View Count",
            "YouTube Recent Median View Count",
        )
        for row in rows
    ]
    recent_total_popularity = [
        first_int(
            row,
            "YouTube Recent Total Popularity",
            "YouTube Recent Popularity",
        )
        for row in rows
    ]
    recent_video_median = [
        first_int(row, "YouTube Recent Video Median View Count") for row in rows
    ]
    recent_livestream_median = [
        first_int(row, "YouTube Recent Livestream Median View Count") for row in rows
    ]
    twitch_recent_median = [
        first_int(row, "Twitch Recent Median View Count") for row in rows
    ]
    active_youtube = sum(1 for value in recent_total_median if value and value > 0)
    active_twitch = sum(1 for value in twitch_recent_median if value and value > 0)
    return {
        "kind": kind,
        "year_month": ym,
        "rows": len(rows),
        "unique_vtubers": len(ids),
        "youtube_subscriber_total": sum(value or 0 for value in youtube_subs),
        "youtube_recent_total_median_view_median": median(recent_total_median),
        "youtube_recent_total_median_view_p90": percentile(recent_total_median, 0.9),
        "youtube_recent_total_popularity_total": sum(value or 0 for value in recent_total_popularity),
        "youtube_recent_video_median_view_median": median(recent_video_median),
        "youtube_recent_livestream_median_view_median": median(recent_livestream_median),
        "youtube_recent_active_channels": active_youtube,
        "youtube_recent_active_ratio": activity_ratio(active_youtube, len(ids)),
        "twitch_recent_median_view_median": median(twitch_recent_median),
        "twitch_recent_active_channels": active_twitch,
        "twitch_recent_active_ratio": activity_ratio(active_twitch, len(ids)),
    }


def analyze_video_rows(path: Path, rows: list[dict]):
    kind, ym = parse_sample_path(path)
    ids = {vtuber_id(row) for row in rows if vtuber_id(row)}
    view_counts = [to_int(row.get("View Count")) for row in rows]
    video_types = Counter((row.get("Video Type") or "").strip() or "(blank)" for row in rows)
    keyword_counts = Counter()
    for row in rows:
        for bucket in bucket_keywords(row.get("Title")):
            keyword_counts[bucket] += 1
    return {
        "kind": kind,
        "year_month": ym,
        "rows": len(rows),
        "unique_vtubers": len(ids),
        "items_with_views": sum(1 for value in view_counts if value is not None),
        "view_total": sum(value or 0 for value in view_counts),
        "view_median": median(view_counts),
        "view_p90": percentile(view_counts, 0.9),
        "video_types_json": json.dumps(dict(video_types.most_common()), ensure_ascii=False),
        "title_buckets_json": json.dumps(dict(keyword_counts.most_common()), ensure_ascii=False),
    }


def analyze_samples():
    rows_by_kind: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(CSV_DIR.glob("*/*.csv")):
        kind, _ = parse_sample_path(path)
        rows = read_csv(path)
        if kind == "basic-data":
            rows_by_kind[kind].append(analyze_basic_data(path, rows))
        elif kind == "record":
            rows_by_kind[kind].append(analyze_record(path, rows))
        else:
            rows_by_kind[kind].append(analyze_video_rows(path, rows))
    return rows_by_kind


def write_markdown(rows_by_kind: dict[str, list[dict]]):
    lines = [
        "# Quarterly Sample Metrics",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        "All metrics are computed from quarterly sampled CSV files only.",
        "",
    ]
    for kind, rows in sorted(rows_by_kind.items()):
        lines.extend([f"## {kind}", ""])
        if kind == "basic-data":
            lines.extend(
                [
                    "| Month | VTubers | YT subs total | YT subs median | YT top10 share | Twitch followers total |",
                    "| --- | ---: | ---: | ---: | ---: | ---: |",
                ]
            )
            for row in rows:
                top10_share = activity_ratio(
                    row["youtube_subscriber_top10_total"],
                    row["youtube_subscriber_total"],
                )
                lines.append(
                    f"| {row['year_month']} | {row['unique_vtubers']} | {row['youtube_subscriber_total']} | {row['youtube_subscriber_median'] or 0} | {top10_share or 0} | {row['twitch_follower_total']} |"
                )
        elif kind == "record":
            lines.extend(
                [
                    "| Month | VTubers | Recent YT median | Recent YT p90 | YT active ratio | Twitch active ratio |",
                    "| --- | ---: | ---: | ---: | ---: | ---: |",
                ]
            )
            for row in rows:
                lines.append(
                    f"| {row['year_month']} | {row['unique_vtubers']} | {row['youtube_recent_total_median_view_median'] or 0} | {row['youtube_recent_total_median_view_p90'] or 0} | {row['youtube_recent_active_ratio'] or 0} | {row['twitch_recent_active_ratio'] or 0} |"
                )
        else:
            lines.extend(
                [
                    "| Month | Rows | VTubers | View total | View median | Title buckets |",
                    "| --- | ---: | ---: | ---: | ---: | --- |",
                ]
            )
            for row in rows:
                lines.append(
                    f"| {row['year_month']} | {row['rows']} | {row['unique_vtubers']} | {row['view_total']} | {row['view_median'] or 0} | {row['title_buckets_json']} |"
                )
        lines.append("")
    (OUT_DIR / "metrics.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows_by_kind = analyze_samples()
    for kind, rows in sorted(rows_by_kind.items()):
        headers = list(rows[0].keys()) if rows else []
        write_rows(OUT_DIR / f"{kind}.csv", rows, headers)
    (OUT_DIR / "metrics.json").write_text(
        json.dumps(rows_by_kind, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_markdown(rows_by_kind)
    total = sum(len(rows) for rows in rows_by_kind.values())
    print(f"Wrote {total} quarterly metric rows to {OUT_DIR}")


if __name__ == "__main__":
    main()
