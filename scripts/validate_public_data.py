#!/usr/bin/env python3
"""Validate public CSV files before publication."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


PROHIBITED_FIELDS = {
    "real_name",
    "home_address",
    "school",
    "workplace",
    "private_email",
    "phone_number",
    "private_account",
    "offline_identity_guess",
    "identity_actor_guess",
    "private_relationship",
    "exact_birthdate",
    "real_time_status",
    "raw_activity_timestamp",
    "individual_sensitive_time_series",
}

REQUIRED_FIELDS = {"source_url", "last_verified"}


def validate_csv(path: Path) -> list[str]:
    errors: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])

        prohibited = sorted(headers & PROHIBITED_FIELDS)
        if prohibited:
            errors.append(f"{path}: prohibited fields: {', '.join(prohibited)}")

        missing = sorted(REQUIRED_FIELDS - headers)
        if missing:
            errors.append(f"{path}: missing required fields: {', '.join(missing)}")

        for row_number, row in enumerate(reader, start=2):
            for field in REQUIRED_FIELDS & headers:
                if not (row.get(field) or "").strip():
                    errors.append(f"{path}:{row_number}: empty required field: {field}")

    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/derived")
    csv_paths = sorted(root.rglob("*.csv")) if root.exists() else []

    errors: list[str] = []
    for csv_path in csv_paths:
        errors.extend(validate_csv(csv_path))

    if errors:
        print("\n".join(errors))
        return 1

    print(f"Validated {len(csv_paths)} CSV file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
