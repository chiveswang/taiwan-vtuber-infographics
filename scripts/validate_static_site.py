#!/usr/bin/env python3
"""Validate static dashboard references."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "site" / "index.html"


def main() -> int:
    html = HTML.read_text(encoding="utf-8")
    refs = re.findall(r'(?:src|href)="([^"]+)"', html)
    errors: list[str] = []

    for ref in refs:
        if ref.startswith(("http://", "https://", "#")):
            continue
        target = (HTML.parent / ref).resolve()
        if not target.exists():
            errors.append(f"{HTML}: missing referenced file: {ref}")

    required = [
        ROOT / "data" / "derived" / "public-index.json",
        ROOT / "data" / "derived" / "platform-coverage-summary.csv",
        ROOT / "data" / "derived" / "public-status-summary.csv",
        ROOT / "data" / "derived" / "activity-quarterly-summary.csv",
        ROOT / "data" / "derived" / "cohort-quarterly-summary.csv",
        ROOT / "data" / "derived" / "content-category-quarterly-summary.csv",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing required dashboard data file: {path.relative_to(ROOT)}")

    if errors:
        print("\n".join(errors))
        return 1

    print("Validated static dashboard references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
