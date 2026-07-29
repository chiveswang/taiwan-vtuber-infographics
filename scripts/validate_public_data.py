#!/usr/bin/env python3
"""Fail-closed validation and staging for every public Pages artifact."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePath, PurePosixPath
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / "data" / "derived" / "public-index.json"
PUBLIC_EXTENSIONS = {".csv", ".json", ".svg", ".html", ".js", ".css"}
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
    "channel_id",
    "channel_url",
    "creator_name",
}
REQUIRED_CSV_FIELDS = {"source_url", "last_verified"}
ALLOWED_CSV_FIELDS = {
    "activation_rate",
    "aggregate_count",
    "aggregate_period",
    "category",
    "content_category",
    "content_scope",
    "cumulative_active",
    "debuts",
    "debuts_group",
    "debuts_hk",
    "debuts_indie",
    "debuts_my",
    "debuts_other",
    "debuts_tw",
    "graduations",
    "last_verified",
    "latest_snapshot_name",
    "metric",
    "net",
    "notes_for_methodology",
    "partial",
    "platform_category",
    "public_status_category",
    "recently_active_any",
    "recently_active_twitch",
    "recently_active_yt",
    "source_category",
    "source_project",
    "source_url",
    "topvid_view_max",
    "topvid_view_median",
    "tracked_channels",
    "tw_live_hosts",
    "tw_live_streams",
    "yt_live_hosts",
    "yt_live_streams",
    "yt_subs_median",
    "yt_subs_p90",
    "yt_tier_large",
    "yt_tier_mega",
    "yt_tier_mid",
    "yt_tier_small",
    "yt_top10_share",
    "yt_view_top10_share",
}
COUNT_FIELD = re.compile(
    r"(?:count|channels|hosts|streams|debuts|graduations|cumulative_active|tier_)"
)
VALUE_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "phone": re.compile(
        r"(?<!\d)(?:(?:\+?886[- ]?9|09)\d{8}|"
        r"(?:\+?886[- ]?|0)(?:2|[3-8]\d)[- ]?\d{7,8})(?!\d)"
    ),
    "youtube channel id": re.compile(r"\bUC[A-Za-z0-9_-]{22}\b"),
    "creator channel URL": re.compile(
        r"https?://(?:www\.)?(?:youtube\.com/(?:channel|@)|twitch\.tv/)[^\s\"'<>]+",
        re.I,
    ),
    "raw timestamp": re.compile(
        r"(?<!\d)\d{4}-\d{2}-\d{2}(?:[T _-])\d{2}(?:[:-])\d{2}(?:(?:[:-])\d{2})?"
    ),
}


def validate_rules(rules: object) -> list[str]:
    if not isinstance(rules, dict):
        return ["public-index.json: missing privacy_rules object"]
    errors = []
    if not rules.get("version"):
        errors.append("public-index.json: privacy_rules.version is required")
    minimum = rules.get("minimum_group_size")
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 2:
        errors.append(
            "public-index.json: privacy_rules.minimum_group_size must be an integer >= 2; "
            "publication remains fail closed until maintainers set it"
        )
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(rules.get("reviewed_at", ""))):
        errors.append("public-index.json: privacy_rules.reviewed_at must be YYYY-MM-DD")
    return errors


def publication_paths(index: dict[str, object], index_path: PurePath) -> set[PurePath]:
    paths = {index_path}
    paths.update(PurePosixPath(path) for path in index.get("site_files", []))
    for collection in ("datasets", "charts"):
        paths.update(
            PurePosixPath(item["path"])
            for item in index.get(collection, [])
            if isinstance(item, dict) and item.get("path")
        )
    return paths


def find_orphans(allowed: set[PurePath], published: set[PurePath]) -> list[str]:
    return [
        f"{path.as_posix()}: public artifact is not listed in public-index.json"
        for path in sorted(published - allowed, key=lambda item: item.as_posix())
    ]


def _scan_values(path: PurePath, text: str) -> list[str]:
    errors = []
    for label, pattern in VALUE_PATTERNS.items():
        if pattern.search(text):
            errors.append(f"{path.as_posix()}: prohibited value pattern: {label}")
    return errors


def _validate_csv(path: PurePath, text: str, minimum_group_size: int) -> list[str]:
    errors = []
    reader = csv.DictReader(io.StringIO(text))
    headers = set(reader.fieldnames or [])
    prohibited = sorted(headers & PROHIBITED_FIELDS)
    if prohibited:
        errors.append(f"{path.as_posix()}: prohibited fields: {', '.join(prohibited)}")
    unknown = sorted(headers - ALLOWED_CSV_FIELDS)
    if unknown:
        errors.append(f"{path.as_posix()}: fields not in schema allowlist: {', '.join(unknown)}")
    missing = sorted(REQUIRED_CSV_FIELDS - headers)
    if missing:
        errors.append(f"{path.as_posix()}: missing required fields: {', '.join(missing)}")

    for row_number, row in enumerate(reader, start=2):
        for field in REQUIRED_CSV_FIELDS & headers:
            if not (row.get(field) or "").strip():
                errors.append(f"{path.as_posix()}:{row_number}: empty required field: {field}")
        for field, value in row.items():
            value = value or ""
            if field != "source_url":
                errors.extend(_scan_values(path, value))
            if minimum_group_size and COUNT_FIELD.search(field or ""):
                try:
                    count = float(value)
                except ValueError:
                    continue
                if 0 < count < minimum_group_size:
                    errors.append(
                        f"{path.as_posix()}:{row_number}: {field}={value} is below "
                        f"privacy_rules.minimum_group_size={minimum_group_size}"
                    )
    return errors


def _validate_json(path: PurePath, text: str) -> list[str]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        return [f"{path.as_posix()}: invalid JSON: {error}"]

    errors = []

    def visit(item: object) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if key.lower() in PROHIBITED_FIELDS:
                    errors.append(f"{path.as_posix()}: prohibited JSON field: {key}")
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif isinstance(item, str):
            errors.extend(_scan_values(path, item))

    visit(value)
    return errors


def _validate_svg(path: PurePath, text: str) -> list[str]:
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as error:
        return [f"{path.as_posix()}: invalid SVG: {error}"]
    errors = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1].lower() == "metadata":
            errors.append(f"{path.as_posix()}: SVG <metadata> is not allowed")
    errors.extend(_scan_values(path, text))
    return errors


def validate_text(path: PurePath, text: str, minimum_group_size: int) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _validate_csv(path, text, minimum_group_size)
    if suffix == ".json":
        return _validate_json(path, text)
    if suffix == ".svg":
        return _validate_svg(path, text)
    if suffix in {".html", ".js", ".css"}:
        return _scan_values(path, text)
    return [f"{path.as_posix()}: unsupported public artifact type"]


def _safe_relative(path: PurePath) -> bool:
    return not path.is_absolute() and ".." not in path.parts


def validate_publication(root: Path, index_path: Path) -> tuple[list[str], dict[str, object], set[PurePath]]:
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{index_path}: cannot read public index: {error}"], {}, set()

    index_relative = PurePosixPath(index_path.resolve().relative_to(root.resolve()).as_posix())
    allowed = publication_paths(index, index_relative)
    errors = validate_rules(index.get("privacy_rules"))
    if any(not _safe_relative(path) for path in allowed):
        errors.append("public-index.json: all publication paths must stay within the repository")

    published: set[PurePath] = set()
    for public_root in index.get("public_roots", []):
        relative_root = PurePosixPath(public_root)
        if not _safe_relative(relative_root):
            errors.append(f"public-index.json: invalid public root: {public_root}")
            continue
        directory = root / relative_root
        if not directory.is_dir():
            errors.append(f"public-index.json: public root does not exist: {public_root}")
            continue
        published.update(
            PurePosixPath(path.relative_to(root).as_posix())
            for path in directory.rglob("*")
            if path.is_file() and path.suffix.lower() in PUBLIC_EXTENSIONS
        )
    errors.extend(find_orphans(allowed, published))

    minimum = index.get("privacy_rules", {}).get("minimum_group_size")
    minimum = minimum if isinstance(minimum, int) and not isinstance(minimum, bool) else 0
    status_by_path = {
        PurePosixPath(item["path"]): item.get("status")
        for collection in ("datasets", "charts")
        for item in index.get(collection, [])
        if isinstance(item, dict) and item.get("path")
    }
    for relative in sorted(allowed, key=lambda path: path.as_posix()):
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative.as_posix()}: listed public artifact does not exist")
            continue
        item_minimum = 0 if status_by_path.get(relative) == "sample" else minimum
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            errors.append(f"{relative.as_posix()}: cannot read public artifact: {error}")
            continue
        errors.extend(validate_text(relative, text, item_minimum))
    return sorted(set(errors)), index, allowed


def stage_publication(root: Path, destination: Path, allowed: set[PurePath], rules: dict[str, object]) -> None:
    resolved_root = root.resolve()
    resolved_destination = destination.resolve()
    if resolved_destination == resolved_root or resolved_root not in resolved_destination.parents:
        raise ValueError("--stage must be a child directory of --root")
    if destination.exists():
        shutil.rmtree(destination)
    for relative in allowed:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, target)
    report = {
        "rules_version": rules["version"],
        "minimum_group_size": rules["minimum_group_size"],
        "status": "passed",
        "passed_at": datetime.now(timezone.utc).isoformat(),
        "files": sorted(path.as_posix() for path in allowed),
    }
    (destination / "privacy-validation-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--stage", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    index_path = (args.index or root / "data/derived/public-index.json").resolve()

    errors, index, allowed = validate_publication(root, index_path)
    if errors:
        print("\n".join(errors))
        return 1
    if args.stage:
        stage_publication(root, args.stage, allowed, index["privacy_rules"])
    print(f"Validated {len(allowed)} public artifact(s) with privacy rules {index['privacy_rules']['version']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
