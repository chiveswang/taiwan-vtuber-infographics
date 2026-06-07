#!/usr/bin/env python3
"""Import privacy-safe aggregate tables from a local activity dashboard artifact."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "derived"
LAST_VERIFIED = "2026-06-07"
SOURCE_URL = (
    "https://github.com/TaiwanVtuberData/TaiwanVtuberTrackingData; "
    "https://github.com/TaiwanVtuberData/TaiwanVTuberTrackingDataArchive"
)


def read_json_constant(text: str, name: str):
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*", text)
    if not match:
        raise ValueError(f"missing JavaScript constant: {name}")
    decoder = json.JSONDecoder()
    value, _ = decoder.raw_decode(text[match.end() :])
    return value


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def row_base(item: dict[str, object]) -> dict[str, object]:
    return {
        "aggregate_period": item.get("quarter", ""),
        "partial": str(bool(item.get("partial", False))).lower(),
        "source_url": SOURCE_URL,
        "last_verified": LAST_VERIFIED,
    }


def activity_rows(act: list[dict[str, object]]) -> list[dict[str, object]]:
    fields = [
        "tracked_channels",
        "recently_active_any",
        "recently_active_yt",
        "recently_active_twitch",
        "activation_rate",
        "yt_subs_median",
        "yt_subs_p90",
        "yt_top10_share",
        "yt_view_top10_share",
        "yt_tier_mega",
        "yt_tier_large",
        "yt_tier_mid",
        "yt_tier_small",
        "yt_live_streams",
        "yt_live_hosts",
        "tw_live_streams",
        "tw_live_hosts",
        "topvid_view_median",
        "topvid_view_max",
    ]
    rows = []
    for item in act:
        row = row_base(item)
        row.update({field: item.get(field, "") for field in fields})
        rows.append(row)
    return rows


def cohort_rows(coh: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for item in coh["series"]:
        nat = item.get("nat", {})
        group = item.get("grp", {})
        row = row_base(item)
        row.update(
            {
                "debuts": item.get("debuts", ""),
                "graduations": item.get("graduations", ""),
                "net": item.get("net", ""),
                "cumulative_active": item.get("cumulative_active", ""),
                "debuts_tw": nat.get("TW", 0),
                "debuts_hk": nat.get("HK", 0),
                "debuts_my": nat.get("MY", 0),
                "debuts_other": sum(value for key, value in nat.items() if key not in {"TW", "HK", "MY"}),
                "debuts_indie": group.get("indie", 0),
                "debuts_group": group.get("group", 0),
            }
        )
        rows.append(row)
    return rows


def content_rows(act: list[dict[str, object]]) -> list[dict[str, object]]:
    scopes = {
        "topvid_buckets": "top_videos",
        "yt_live_buckets": "youtube_livestreams",
        "tw_live_buckets": "twitch_livestreams",
    }
    rows = []
    for item in act:
        for source_key, scope in scopes.items():
            buckets = item.get(source_key) or {}
            for category, count in sorted(buckets.items()):
                row = row_base(item)
                row.update(
                    {
                        "content_scope": scope,
                        "content_category": category,
                        "aggregate_count": count,
                    }
                )
                rows.append(row)
    return rows


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: import_activity_dashboard_aggregates.py <vtuber_activity_dashboard.html>")
        return 2

    source = Path(sys.argv[1])
    text = source.read_text(encoding="utf-8")
    act = read_json_constant(text, "ACT")
    coh = read_json_constant(text, "COH")

    write_csv(
        OUT_DIR / "activity-quarterly-summary.csv",
        activity_rows(act),
        [
            "aggregate_period",
            "partial",
            "tracked_channels",
            "recently_active_any",
            "recently_active_yt",
            "recently_active_twitch",
            "activation_rate",
            "yt_subs_median",
            "yt_subs_p90",
            "yt_top10_share",
            "yt_view_top10_share",
            "yt_tier_mega",
            "yt_tier_large",
            "yt_tier_mid",
            "yt_tier_small",
            "yt_live_streams",
            "yt_live_hosts",
            "tw_live_streams",
            "tw_live_hosts",
            "topvid_view_median",
            "topvid_view_max",
            "source_url",
            "last_verified",
        ],
    )
    write_csv(
        OUT_DIR / "cohort-quarterly-summary.csv",
        cohort_rows(coh),
        [
            "aggregate_period",
            "partial",
            "debuts",
            "graduations",
            "net",
            "cumulative_active",
            "debuts_tw",
            "debuts_hk",
            "debuts_my",
            "debuts_other",
            "debuts_indie",
            "debuts_group",
            "source_url",
            "last_verified",
        ],
    )
    write_csv(
        OUT_DIR / "content-category-quarterly-summary.csv",
        content_rows(act),
        [
            "aggregate_period",
            "partial",
            "content_scope",
            "content_category",
            "aggregate_count",
            "source_url",
            "last_verified",
        ],
    )
    print("Imported aggregate activity dashboard tables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
