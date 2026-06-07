#!/usr/bin/env python3
"""Generate sample aggregate-only SVG charts from public demo CSV files."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "derived" / "aggregate-summary.csv"
OUTPUT = ROOT / "charts" / "exports" / "sample-content-category-share.svg"
PLATFORM_INPUT = ROOT / "data" / "derived" / "platform-coverage-summary.csv"
PLATFORM_OUTPUT = ROOT / "charts" / "exports" / "platform-coverage-summary.svg"
SOURCE_INPUT = ROOT / "data" / "derived" / "source-coverage-summary.csv"
SOURCE_OUTPUT = ROOT / "charts" / "exports" / "source-coverage-summary.svg"
STATUS_INPUT = ROOT / "data" / "derived" / "public-status-summary.csv"
STATUS_OUTPUT = ROOT / "charts" / "exports" / "public-status-summary.svg"
QUARTERLY_INPUT = ROOT / "data" / "derived" / "quarterly-ecosystem-coverage.csv"
QUARTERLY_OUTPUT = ROOT / "charts" / "exports" / "quarterly-ecosystem-coverage.svg"

COLORS = {
    "music": "#2f6f73",
    "game": "#d08c3f",
    "talk": "#6b7280",
    "collab": "#8b5cf6",
}


def load_rows() -> list[dict[str, str]]:
    with INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_svg(rows: list[dict[str, str]]) -> str:
    chart_rows = [
        row
        for row in rows
        if row.get("metric") == "sample_content_category_count"
    ]
    max_count = max(int(row["aggregate_count"]) for row in chart_rows)
    baseline = 438
    max_height = 268
    bar_width = 112
    start_x = 126
    gap = 62

    bars: list[str] = []
    labels: list[str] = []
    values: list[str] = []

    for index, row in enumerate(chart_rows):
        category = row["category"]
        count = int(row["aggregate_count"])
        height = round((count / max_count) * max_height)
        x = start_x + index * (bar_width + gap)
        y = baseline - height
        center = x + bar_width / 2
        color = COLORS.get(category, "#334155")
        bars.append(f'  <rect x="{x}" y="{y}" width="{bar_width}" height="{height}" rx="4" fill="{color}"/>')
        labels.append(f'  <text x="{center:.0f}" y="462" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="#172033">{category}</text>')
        values.append(f'  <text x="{center:.0f}" y="{y - 14}" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="#172033">{count}</text>')

    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img" aria-labelledby="title desc">',
            '  <title id="title">Sample content category share chart</title>',
            '  <desc id="desc">A sample aggregate-only bar chart using fake demo data for Taiwan VTuber infographic planning.</desc>',
            '  <rect width="960" height="540" fill="#f8fafc"/>',
            '  <text x="72" y="72" font-family="Arial, sans-serif" font-size="28" font-weight="700" fill="#172033">Sample Content Category Share</text>',
            '  <text x="72" y="106" font-family="Arial, sans-serif" font-size="15" fill="#526071">Fake aggregate demo data. Not real tracking data.</text>',
            '  <line x1="72" y1="438" x2="840" y2="438" stroke="#cbd5e1" stroke-width="2"/>',
            '  <line x1="72" y1="170" x2="72" y2="438" stroke="#cbd5e1" stroke-width="2"/>',
            *bars,
            *labels,
            *values,
            '  <text x="72" y="506" font-family="Arial, sans-serif" font-size="13" fill="#64748b">Source: sample schema only. Last verified: 2026-06-07.</text>',
            "</svg>",
            "",
        ]
    )


def build_platform_svg(rows: list[dict[str, str]]) -> str:
    chart_rows = sorted(rows, key=lambda row: row["platform_category"])
    max_count = max(int(row["aggregate_count"]) for row in chart_rows)
    baseline = 438
    max_height = 268
    bar_width = 112
    start_x = 96
    gap = 58
    colors = {
        "no_public_platform_id": "#64748b",
        "twitch_only": "#8b5cf6",
        "youtube_and_twitch": "#2f6f73",
        "youtube_only": "#d08c3f",
    }
    labels = {
        "no_public_platform_id": "no id",
        "twitch_only": "twitch",
        "youtube_and_twitch": "both",
        "youtube_only": "youtube",
    }

    bars: list[str] = []
    axis_labels: list[str] = []
    values: list[str] = []
    for index, row in enumerate(chart_rows):
        category = row["platform_category"]
        count = int(row["aggregate_count"])
        height = round((count / max_count) * max_height)
        x = start_x + index * (bar_width + gap)
        y = baseline - height
        center = x + bar_width / 2
        bars.append(f'  <rect x="{x}" y="{y}" width="{bar_width}" height="{height}" rx="4" fill="{colors.get(category, "#334155")}"/>')
        axis_labels.append(f'  <text x="{center:.0f}" y="462" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="#172033">{labels.get(category, category)}</text>')
        values.append(f'  <text x="{center:.0f}" y="{y - 14}" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="#172033">{count}</text>')

    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img" aria-labelledby="title desc">',
            '  <title id="title">Taiwan VTuber platform coverage summary</title>',
            '  <desc id="desc">Aggregate platform field coverage derived from public upstream data. No names, IDs, or raw rows are published.</desc>',
            '  <rect width="960" height="540" fill="#f8fafc"/>',
            '  <text x="72" y="72" font-family="Arial, sans-serif" font-size="28" font-weight="700" fill="#172033">Platform Coverage Summary</text>',
            '  <text x="72" y="106" font-family="Arial, sans-serif" font-size="15" fill="#526071">Aggregate field presence only. No names, IDs, or individual rows.</text>',
            '  <line x1="72" y1="438" x2="840" y2="438" stroke="#cbd5e1" stroke-width="2"/>',
            '  <line x1="72" y1="170" x2="72" y2="438" stroke="#cbd5e1" stroke-width="2"/>',
            *bars,
            *axis_labels,
            *values,
            '  <text x="72" y="506" font-family="Arial, sans-serif" font-size="13" fill="#64748b">Source: TaiwanVtuberData/TaiwanVtuberTrackingData. Aggregate derived output.</text>',
            "</svg>",
            "",
        ]
    )


def build_source_coverage_svg(rows: list[dict[str, str]]) -> str:
    periods = sorted({row["aggregate_period"] for row in rows})
    families = ["basic-data", "youtube-livestreams", "twitch-livestreams", "other"]
    colors = {
        "basic-data": "#2f6f73",
        "youtube-livestreams": "#d08c3f",
        "twitch-livestreams": "#8b5cf6",
        "other": "#64748b",
    }
    counts = {
        (row["aggregate_period"], row["source_category"]): int(row["aggregate_count"])
        for row in rows
    }
    totals = {
        period: sum(counts.get((period, family), 0) for family in families)
        for period in periods
    }
    max_total = max(totals.values())
    baseline = 438
    max_height = 268
    chart_left = 94
    chart_width = 700
    gap = 18
    bar_width = max(28, round((chart_width - gap * (len(periods) - 1)) / len(periods)))

    bars: list[str] = []
    labels: list[str] = []
    totals_text: list[str] = []
    for index, period in enumerate(periods):
        x = chart_left + index * (bar_width + gap)
        current_y = baseline
        for family in families:
            count = counts.get((period, family), 0)
            if count == 0:
                continue
            height = round((count / max_total) * max_height)
            y = current_y - height
            bars.append(f'  <rect x="{x}" y="{y}" width="{bar_width}" height="{height}" fill="{colors[family]}"/>')
            current_y = y
        center = x + bar_width / 2
        labels.append(f'  <text x="{center:.0f}" y="462" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#172033">{period}</text>')
        totals_text.append(f'  <text x="{center:.0f}" y="{current_y - 10}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#172033">{totals[period]}</text>')

    legend: list[str] = []
    for index, family in enumerate(families):
        y = 170 + index * 28
        legend.extend(
            [
                f'  <rect x="820" y="{y - 12}" width="14" height="14" fill="{colors[family]}"/>',
                f'  <text x="842" y="{y}" font-family="Arial, sans-serif" font-size="13" fill="#172033">{family}</text>',
            ]
        )

    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img" aria-labelledby="title desc">',
            '  <title id="title">Source coverage summary</title>',
            '  <desc id="desc">Monthly aggregate count of public upstream snapshot files by file family. No raw CSV rows are copied.</desc>',
            '  <rect width="960" height="540" fill="#f8fafc"/>',
            '  <text x="72" y="72" font-family="Arial, sans-serif" font-size="28" font-weight="700" fill="#172033">Source Coverage Summary</text>',
            '  <text x="72" y="106" font-family="Arial, sans-serif" font-size="15" fill="#526071">Monthly file metadata counts from public upstream repo. No raw rows copied.</text>',
            '  <line x1="72" y1="438" x2="800" y2="438" stroke="#cbd5e1" stroke-width="2"/>',
            '  <line x1="72" y1="170" x2="72" y2="438" stroke="#cbd5e1" stroke-width="2"/>',
            *bars,
            *labels,
            *totals_text,
            *legend,
            '  <text x="72" y="506" font-family="Arial, sans-serif" font-size="13" fill="#64748b">Source: TaiwanVtuberData/TaiwanVtuberTrackingData repository metadata.</text>',
            "</svg>",
            "",
        ]
    )


def build_simple_bar_svg(
    rows: list[dict[str, str]],
    label_key: str,
    title: str,
    subtitle: str,
    desc: str,
    footer: str,
) -> str:
    chart_rows = sorted(rows, key=lambda row: row[label_key])
    max_count = max(int(row["aggregate_count"]) for row in chart_rows)
    baseline = 438
    max_height = 268
    bar_width = 112
    start_x = 96
    gap = 58
    palette = ["#2f6f73", "#d08c3f", "#8b5cf6", "#64748b", "#0f766e", "#b45309"]
    bars: list[str] = []
    labels: list[str] = []
    values: list[str] = []
    for index, row in enumerate(chart_rows):
        label = row[label_key]
        count = int(row["aggregate_count"])
        height = round((count / max_count) * max_height)
        x = start_x + index * (bar_width + gap)
        y = baseline - height
        center = x + bar_width / 2
        bars.append(f'  <rect x="{x}" y="{y}" width="{bar_width}" height="{height}" rx="4" fill="{palette[index % len(palette)]}"/>')
        labels.append(f'  <text x="{center:.0f}" y="462" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" fill="#172033">{label}</text>')
        values.append(f'  <text x="{center:.0f}" y="{y - 14}" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="#172033">{count}</text>')

    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img" aria-labelledby="title desc">',
            f'  <title id="title">{title}</title>',
            f'  <desc id="desc">{desc}</desc>',
            '  <rect width="960" height="540" fill="#f8fafc"/>',
            f'  <text x="72" y="72" font-family="Arial, sans-serif" font-size="28" font-weight="700" fill="#172033">{title}</text>',
            f'  <text x="72" y="106" font-family="Arial, sans-serif" font-size="15" fill="#526071">{subtitle}</text>',
            '  <line x1="72" y1="438" x2="840" y2="438" stroke="#cbd5e1" stroke-width="2"/>',
            '  <line x1="72" y1="170" x2="72" y2="438" stroke="#cbd5e1" stroke-width="2"/>',
            *bars,
            *labels,
            *values,
            f'  <text x="72" y="506" font-family="Arial, sans-serif" font-size="13" fill="#64748b">{footer}</text>',
            "</svg>",
            "",
        ]
    )


def build_quarterly_svg(rows: list[dict[str, str]]) -> str:
    totals: Counter[str] = Counter()
    for row in rows:
        totals[row["aggregate_period"]] += int(row["aggregate_count"])
    total_rows = [
        {"aggregate_period": period, "aggregate_count": str(count)}
        for period, count in sorted(totals.items())
    ]
    return build_simple_bar_svg(
        total_rows,
        "aggregate_period",
        "Quarterly Ecosystem Coverage",
        "Quarter-level aggregate count of public upstream snapshot metadata.",
        "Quarter-level aggregate source coverage from public upstream repository metadata.",
        "Source: TaiwanVtuberData/TaiwanVtuberTrackingData repository metadata.",
    )


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg(load_rows()), encoding="utf-8")
    if PLATFORM_INPUT.exists():
        with PLATFORM_INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
            platform_rows = list(csv.DictReader(handle))
        PLATFORM_OUTPUT.write_text(build_platform_svg(platform_rows), encoding="utf-8")
    if SOURCE_INPUT.exists():
        with SOURCE_INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
            source_rows = list(csv.DictReader(handle))
        SOURCE_OUTPUT.write_text(build_source_coverage_svg(source_rows), encoding="utf-8")
    if STATUS_INPUT.exists():
        with STATUS_INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
            status_rows = list(csv.DictReader(handle))
        STATUS_OUTPUT.write_text(
            build_simple_bar_svg(
                status_rows,
                "public_status_category",
                "Public Status Summary",
                "Aggregate of upstream Activity labels. Not real-time status.",
                "Aggregate status category chart derived from upstream public Activity labels.",
                "No names, IDs, raw rows, or individual timelines are published.",
            ),
            encoding="utf-8",
        )
    if QUARTERLY_INPUT.exists():
        with QUARTERLY_INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
            quarterly_rows = list(csv.DictReader(handle))
        QUARTERLY_OUTPUT.write_text(build_quarterly_svg(quarterly_rows), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    if PLATFORM_OUTPUT.exists():
        print(f"Wrote {PLATFORM_OUTPUT.relative_to(ROOT)}")
    if SOURCE_OUTPUT.exists():
        print(f"Wrote {SOURCE_OUTPUT.relative_to(ROOT)}")
    if STATUS_OUTPUT.exists():
        print(f"Wrote {STATUS_OUTPUT.relative_to(ROOT)}")
    if QUARTERLY_OUTPUT.exists():
        print(f"Wrote {QUARTERLY_OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
