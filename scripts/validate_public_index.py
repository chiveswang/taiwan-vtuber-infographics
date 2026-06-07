#!/usr/bin/env python3
"""Validate the public asset index consumed by downstream sites."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data" / "derived" / "public-index.json"

REQUIRED_TOP_LEVEL = {"project", "generated_at", "privacy_scope", "datasets", "charts"}
REQUIRED_DATASET_FIELDS = {"id", "title", "path", "type", "status", "last_verified", "privacy_note"}
REQUIRED_CHART_FIELDS = {"id", "title", "path", "type", "status", "source_dataset", "privacy_note"}


def main() -> int:
    errors: list[str] = []
    data = json.loads(INDEX.read_text(encoding="utf-8"))

    missing_top_level = sorted(REQUIRED_TOP_LEVEL - set(data))
    if missing_top_level:
        errors.append(f"{INDEX}: missing top-level fields: {', '.join(missing_top_level)}")

    for collection_name, required_fields in (
        ("datasets", REQUIRED_DATASET_FIELDS),
        ("charts", REQUIRED_CHART_FIELDS),
    ):
        for index, item in enumerate(data.get(collection_name, [])):
            missing = sorted(required_fields - set(item))
            if missing:
                errors.append(f"{INDEX}:{collection_name}[{index}]: missing fields: {', '.join(missing)}")

            item_path = item.get("path")
            if item_path and not (ROOT / item_path).exists():
                errors.append(f"{INDEX}:{collection_name}[{index}]: path does not exist: {item_path}")

    if errors:
        print("\n".join(errors))
        return 1

    print("Validated public index.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
