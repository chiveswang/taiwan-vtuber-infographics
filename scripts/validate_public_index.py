#!/usr/bin/env python3
"""Validate the public asset index consumed by downstream sites."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data" / "derived" / "public-index.json"

REQUIRED_TOP_LEVEL = {
    "project",
    "generated_at",
    "privacy_scope",
    "privacy_rules",
    "public_roots",
    "site_files",
    "source_project_policy",
    "license_policy",
    "datasets",
    "charts",
}
REQUIRED_DATASET_FIELDS = {
    "id", "title", "path", "type", "status", "last_verified", "license",
    "source_url", "provenance", "privacy_note",
}
REQUIRED_CHART_FIELDS = {
    "id", "title", "path", "type", "status", "source_dataset", "last_verified",
    "license", "source_url", "generator", "generator_version", "privacy_note",
}
KNOWN_CHART_GENERATORS = {"scripts/generate_sample_charts.py": "1.0"}


def main() -> int:
    errors: list[str] = []
    data = json.loads(INDEX.read_text(encoding="utf-8"))

    missing_top_level = sorted(REQUIRED_TOP_LEVEL - set(data))
    if missing_top_level:
        errors.append(f"{INDEX}: missing top-level fields: {', '.join(missing_top_level)}")

    policy = data.get("license_policy", {})
    expected_policy = {
        "code": "MIT",
        "derived_data": "CC-BY-4.0",
        "chart_exports": "CC-BY-4.0",
        "site_content": "CC-BY-4.0",
        "policy_url": "LICENSE-DATA.md",
    }
    for field, expected in expected_policy.items():
        if policy.get(field) != expected:
            errors.append(f"{INDEX}: license_policy.{field} must be {expected}")
    if not str(policy.get("attribution", "")).strip():
        errors.append(f"{INDEX}: license_policy.attribution must be non-empty")

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
            if item.get("license") != "CC-BY-4.0":
                errors.append(
                    f"{INDEX}:{collection_name}[{index}]: license must be CC-BY-4.0"
                )
            if collection_name == "charts":
                generator = item.get("generator")
                expected_version = KNOWN_CHART_GENERATORS.get(generator)
                if expected_version is None:
                    errors.append(
                        f"{INDEX}:{collection_name}[{index}]: unknown generator: {generator}"
                    )
                elif item.get("generator_version") != expected_version:
                    errors.append(
                        f"{INDEX}:{collection_name}[{index}]: generator_version must be "
                        f"{expected_version} for {generator}"
                    )

    if errors:
        print("\n".join(errors))
        return 1

    print("Validated public index.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
