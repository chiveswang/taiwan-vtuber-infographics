#!/usr/bin/env python3
"""Generate low-risk aggregate derived data from public upstream metadata."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"
REPO_API = "https://api.github.com/repos/TaiwanVtuberData/TaiwanVtuberTrackingData/contents"
REPO_API_PATH = "repos/TaiwanVtuberData/TaiwanVtuberTrackingData/contents"
TRACK_LIST_URL = "https://raw.githubusercontent.com/TaiwanVtuberData/TaiwanVtuberTrackingData/master/DATA/TW_VTUBER_TRACK_LIST.csv"
SOURCE_PROJECT = "TaiwanVtuberData/TaiwanVtuberTrackingData"
LAST_VERIFIED = date.today().isoformat()


def fetch_json(url: str) -> object:
    if url.startswith(REPO_API):
        path = REPO_API_PATH + url.removeprefix(REPO_API)
        try:
            result = subprocess.run(
                ["gh", "api", path],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            return json.loads(result.stdout)
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
    with urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_csv(url: str) -> list[dict[str, str]]:
    with urlopen(url) as response:
        text = response.read().decode("utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_platform_coverage() -> None:
    rows = fetch_csv(TRACK_LIST_URL)
    counts: Counter[str] = Counter()
    for row in rows:
        has_youtube = bool(row.get("Youtube Channel ID", "").strip())
        has_twitch = bool(row.get("Twitch Channel ID", "").strip() or row.get("Twitch Channel Name", "").strip())
        if has_youtube and has_twitch:
            counts["youtube_and_twitch"] += 1
        elif has_youtube:
            counts["youtube_only"] += 1
        elif has_twitch:
            counts["twitch_only"] += 1
        else:
            counts["no_public_platform_id"] += 1

    output_rows = [
        {
            "aggregate_period": LAST_VERIFIED[:7],
            "platform_category": category,
            "aggregate_count": count,
            "source_project": SOURCE_PROJECT,
            "source_url": TRACK_LIST_URL,
            "last_verified": LAST_VERIFIED,
            "notes_for_methodology": "Derived from platform field presence only; no names, IDs, or raw rows published.",
        }
        for category, count in sorted(counts.items())
    ]
    write_csv(
        DERIVED / "platform-coverage-summary.csv",
        [
            "aggregate_period",
            "platform_category",
            "aggregate_count",
            "source_project",
            "source_url",
            "last_verified",
            "notes_for_methodology",
        ],
        output_rows,
    )


def generate_public_status_summary() -> None:
    rows = fetch_csv(TRACK_LIST_URL)
    counts: Counter[str] = Counter()
    for row in rows:
        status = (row.get("Activity") or "unknown").strip().lower() or "unknown"
        counts[status] += 1

    output_rows = [
        {
            "aggregate_period": LAST_VERIFIED[:7],
            "public_status_category": category,
            "aggregate_count": count,
            "source_project": SOURCE_PROJECT,
            "source_url": TRACK_LIST_URL,
            "last_verified": LAST_VERIFIED,
            "notes_for_methodology": "Aggregate of upstream Activity labels; not real-time status and no names, IDs, or raw rows published.",
        }
        for category, count in sorted(counts.items())
    ]
    write_csv(
        DERIVED / "public-status-summary.csv",
        [
            "aggregate_period",
            "public_status_category",
            "aggregate_count",
            "source_project",
            "source_url",
            "last_verified",
            "notes_for_methodology",
        ],
        output_rows,
    )


def quarter_for_period(period: str) -> str:
    year, month = period.split("-")
    quarter = (int(month) - 1) // 3 + 1
    return f"{year}-Q{quarter}"


def generate_source_coverage() -> None:
    root_items = fetch_json(REPO_API)
    month_names = sorted(
        item["name"]
        for item in root_items
        if item.get("type") == "dir" and re.fullmatch(r"\d{4}-\d{2}", item["name"])
    )
    rows: list[dict[str, object]] = []
    for month in month_names:
        items = fetch_json(f"{REPO_API}/{month}")
        family_counts: Counter[str] = Counter()
        latest_by_family: dict[str, str] = {}
        for item in items:
            name = item["name"]
            if name.startswith("basic-data_"):
                family = "basic-data"
            elif name.startswith("livestreams_"):
                family = "youtube-livestreams"
            elif name.startswith("twitch-livestreams_"):
                family = "twitch-livestreams"
            else:
                family = "other"
            family_counts[family] += 1
            latest_by_family[family] = max(latest_by_family.get(family, ""), name)

        for family, count in sorted(family_counts.items()):
            rows.append(
                {
                    "aggregate_period": month,
                    "source_project": SOURCE_PROJECT,
                    "source_category": family,
                    "aggregate_count": count,
                    "latest_snapshot_name": latest_by_family[family],
                    "source_url": f"https://github.com/{SOURCE_PROJECT}/tree/master/{month}",
                    "last_verified": LAST_VERIFIED,
                    "notes_for_methodology": "Derived from public repository file metadata only; raw CSV rows not copied.",
                }
            )

    write_csv(
        DERIVED / "source-coverage-summary.csv",
        [
            "aggregate_period",
            "source_project",
            "source_category",
            "aggregate_count",
            "latest_snapshot_name",
            "source_url",
            "last_verified",
            "notes_for_methodology",
        ],
        rows,
    )
    quarterly_counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        quarterly_counts[(quarter_for_period(str(row["aggregate_period"])), str(row["source_category"]))] += int(row["aggregate_count"])

    quarterly_rows = [
        {
            "aggregate_period": quarter,
            "source_project": SOURCE_PROJECT,
            "source_category": category,
            "aggregate_count": count,
            "source_url": f"https://github.com/{SOURCE_PROJECT}",
            "last_verified": LAST_VERIFIED,
            "notes_for_methodology": "Quarter-level aggregate from public repository file metadata; raw CSV rows not copied.",
        }
        for (quarter, category), count in sorted(quarterly_counts.items())
    ]
    write_csv(
        DERIVED / "quarterly-ecosystem-coverage.csv",
        [
            "aggregate_period",
            "source_project",
            "source_category",
            "aggregate_count",
            "source_url",
            "last_verified",
            "notes_for_methodology",
        ],
        quarterly_rows,
    )


def main() -> int:
    generate_platform_coverage()
    generate_public_status_summary()
    generate_source_coverage()
    print("Wrote real aggregate derived data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
