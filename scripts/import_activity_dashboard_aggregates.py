#!/usr/bin/env python3
"""Import privacy-safe aggregate tables from a local activity dashboard artifact."""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
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


def public_count(value: object) -> object:
    try:
        count = float(value)
    except (TypeError, ValueError):
        return value
    return "" if 0 < abs(count) < 10 else value


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
    count_fields = {
        "tracked_channels",
        "recently_active_any",
        "recently_active_yt",
        "recently_active_twitch",
        "yt_tier_mega",
        "yt_tier_large",
        "yt_tier_mid",
        "yt_tier_small",
        "yt_live_streams",
        "yt_live_hosts",
        "tw_live_streams",
        "tw_live_hosts",
    }
    rows = []
    for item in act:
        row = row_base(item)
        row.update(
            {
                field: (
                    public_count(item.get(field, ""))
                    if field in count_fields
                    else item.get(field, "")
                )
                for field in fields
            }
        )
        rows.append(row)
    return rows


def cohort_rows(coh: dict[str, object]) -> list[dict[str, object]]:
    settled = [item for item in coh["series"] if not item.get("partial")]
    if not settled:
        return []

    nationality = Counter()
    groups = Counter()
    for item in settled:
        nat = item.get("nat", {})
        group = item.get("grp", {})
        nationality.update(nat)
        groups.update(group)

    return [
        {
            "aggregate_period": "all-settled",
            "partial": "false",
            "source_url": SOURCE_URL,
            "last_verified": LAST_VERIFIED,
            "debuts": public_count(sum(item.get("debuts", 0) for item in settled)),
            "graduations": public_count(
                sum(item.get("graduations", 0) for item in settled)
            ),
            "net": public_count(sum(item.get("net", 0) for item in settled)),
            "cumulative_active": public_count(settled[-1].get("cumulative_active", 0)),
            "debuts_tw": public_count(nationality["TW"]),
            "debuts_hk": public_count(nationality["HK"]),
            "debuts_my": public_count(nationality["MY"]),
            "debuts_other": public_count(
                sum(
                    value
                    for key, value in nationality.items()
                    if key not in {"TW", "HK", "MY"}
                )
            ),
            "debuts_indie": public_count(groups["indie"]),
            "debuts_group": public_count(groups["group"]),
        }
    ]


def content_rows(act: list[dict[str, object]]) -> list[dict[str, object]]:
    scopes = {
        "topvid_buckets": "top_videos",
        "yt_live_buckets": "youtube_livestreams",
        "tw_live_buckets": "twitch_livestreams",
    }
    rows = []
    for item in act:
        if item.get("partial"):
            continue
        for source_key, scope in scopes.items():
            buckets = item.get(source_key) or {}
            public_buckets: dict[str, int] = {}
            small_total = 0
            for category, raw_count in buckets.items():
                count = int(raw_count)
                if 0 < count < 10:
                    small_total += count
                elif count >= 10:
                    public_buckets[category] = count
            if small_total:
                merged_other = public_buckets.get("other", 0) + small_total
                if merged_other >= 10:
                    public_buckets["other"] = merged_other
            for category, count in sorted(public_buckets.items()):
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
