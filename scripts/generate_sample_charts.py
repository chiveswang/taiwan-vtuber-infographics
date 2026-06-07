#!/usr/bin/env python3
"""Generate sample aggregate-only SVG charts from public demo CSV files."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "derived" / "aggregate-summary.csv"
OUTPUT = ROOT / "charts" / "exports" / "sample-content-category-share.svg"

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


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_svg(load_rows()), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
