import argparse
import csv
import io
import json
import shutil
import sqlite3
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "vtuber_index.sqlite"
ARCHIVE_PATH = ROOT / "archive"
OUT_DIR = ROOT / "quarterly_samples"


def normalize_header(name: str) -> str:
    return name.strip().lstrip("\ufeff").split("##", 1)[-1]


def run_git_show(path: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(ARCHIVE_PATH), "show", f"HEAD:{path}"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout


def read_csv_bytes(data: bytes):
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames:
        reader.fieldnames = [normalize_header(field) for field in reader.fieldnames]
    return list(reader), reader.fieldnames or []


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


def select_samples(conn: sqlite3.Connection, kinds: list[str] | None):
    kind_filter = ""
    params: list[str] = []
    if kinds:
        placeholders = ",".join("?" for _ in kinds)
        kind_filter = f"AND kind IN ({placeholders})"
        params.extend(kinds)

    rows = conn.execute(
        f"""
        WITH firsts AS (
            SELECT repo, kind, MIN(snapshot_at) AS first_snapshot
            FROM snapshots
            WHERE repo = 'archive' {kind_filter}
            GROUP BY repo, kind
        ),
        monthly AS (
            SELECT repo, kind, substr(snapshot_at, 1, 7) AS ym, MIN(snapshot_at) AS snapshot_at
            FROM snapshots
            WHERE repo = 'archive' {kind_filter}
            GROUP BY repo, kind, substr(snapshot_at, 1, 7)
        ),
        picked AS (
            SELECT
                m.repo,
                m.kind,
                m.ym,
                m.snapshot_at,
                ((CAST(substr(m.ym, 1, 4) AS INT) - CAST(substr(f.first_snapshot, 1, 4) AS INT)) * 12
                    + (CAST(substr(m.ym, 6, 2) AS INT) - CAST(substr(f.first_snapshot, 6, 2) AS INT))) AS month_offset
            FROM monthly m
            JOIN firsts f ON f.repo = m.repo AND f.kind = m.kind
        )
        SELECT p.kind, p.ym, p.snapshot_at, s.path
        FROM picked p
        JOIN snapshots s
          ON s.repo = p.repo AND s.kind = p.kind AND s.snapshot_at = p.snapshot_at
        WHERE p.month_offset % 3 = 0
        ORDER BY p.kind, p.ym
        """,
        params + params,
    ).fetchall()
    return rows


def summarize_rows(kind: str, rows: list[dict]):
    vtuber_ids = {
        (row.get("VTuber ID") or "").strip()
        for row in rows
        if (row.get("VTuber ID") or "").strip()
    }
    summary = {
        "rows": len(rows),
        "unique_vtubers": len(vtuber_ids),
    }

    if kind in {"record", "basic-data"}:
        youtube_subs = [to_int(row.get("YouTube Subscriber Count")) for row in rows]
        youtube_views = [to_int(row.get("YouTube View Count")) for row in rows]
        twitch_followers = [to_int(row.get("Twitch Follower Count")) for row in rows]
        summary.update(
            {
                "youtube_channels_with_subs": sum(1 for value in youtube_subs if value and value > 0),
                "youtube_subscriber_total": sum(value or 0 for value in youtube_subs),
                "youtube_subscriber_median": median(youtube_subs),
                "youtube_view_total": sum(value or 0 for value in youtube_views),
                "twitch_channels_with_followers": sum(
                    1 for value in twitch_followers if value and value > 0
                ),
                "twitch_follower_total": sum(value or 0 for value in twitch_followers),
                "twitch_follower_median": median(twitch_followers),
            }
        )
    else:
        view_counts = [to_int(row.get("View Count")) for row in rows]
        video_types = Counter((row.get("Video Type") or "").strip() or "(blank)" for row in rows)
        summary.update(
            {
                "items_with_views": sum(1 for value in view_counts if value is not None),
                "view_total": sum(value or 0 for value in view_counts),
                "view_median": median(view_counts),
                "video_types": dict(video_types.most_common()),
            }
        )
    return summary


def write_csv(path: Path, headers: list[str], rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(path: Path, records: list[dict]):
    headers = [
        "kind",
        "year_month",
        "snapshot_at",
        "source_path",
        "local_csv",
        "rows",
        "unique_vtubers",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def write_summary(path: Path, records: list[dict]):
    by_kind: dict[str, list[dict]] = {}
    for record in records:
        by_kind.setdefault(record["kind"], []).append(record)

    lines = [
        "# Quarterly Archive Sample Analysis",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Sampling rule: for each archive CSV kind, start at that kind's earliest available month and select the first snapshot in every third month.",
        "",
        f"Total sampled CSV files: {len(records)}",
        "",
    ]

    for kind, items in sorted(by_kind.items()):
        lines.extend(
            [
                f"## {kind}",
                "",
                f"- Sample count: {len(items)}",
                f"- Range: {items[0]['year_month']} to {items[-1]['year_month']}",
                f"- First snapshot: {items[0]['snapshot_at']}",
                f"- Latest sampled snapshot: {items[-1]['snapshot_at']}",
                "",
                "| Month | Rows | Unique VTubers | Main metric |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for item in items:
            summary = item["summary"]
            if kind in {"record", "basic-data"}:
                metric = summary.get("youtube_subscriber_total")
            else:
                metric = summary.get("view_total")
            lines.append(
                f"| {item['year_month']} | {summary['rows']} | {summary['unique_vtubers']} | {metric or 0} |"
            )
        lines.append("")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--kind",
        action="append",
        choices=[
            "basic-data",
            "record",
            "livestreams",
            "top-videos",
            "twitch-livestreams",
        ],
        help="Limit sampling to one kind. Repeat for multiple kinds.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not clear the output directory before writing new samples.",
    )
    args = parser.parse_args()

    if OUT_DIR.exists() and not args.keep_existing:
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        samples = select_samples(conn, args.kind)
    finally:
        conn.close()

    records = []
    for kind, year_month, snapshot_at, source_path in samples:
        data = run_git_show(source_path)
        rows, headers = read_csv_bytes(data)
        local_csv = OUT_DIR / "csv" / kind / f"{year_month}_{Path(source_path).name}"
        write_csv(local_csv, headers, rows)
        summary = summarize_rows(kind, rows)
        record = {
            "kind": kind,
            "year_month": year_month,
            "snapshot_at": snapshot_at,
            "source_path": source_path,
            "local_csv": str(local_csv.relative_to(ROOT)),
            "rows": summary["rows"],
            "unique_vtubers": summary["unique_vtubers"],
            "summary": summary,
        }
        records.append(record)

    write_manifest(OUT_DIR / "manifest.csv", records)
    (OUT_DIR / "summary.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_summary(OUT_DIR / "analysis.md", records)
    print(f"Wrote {len(records)} sampled CSV files to {OUT_DIR}")


if __name__ == "__main__":
    main()
