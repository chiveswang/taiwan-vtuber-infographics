#!/usr/bin/env python3
"""Fail-closed validation and staging for every public Pages artifact."""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import re
import shutil
import stat
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePath, PurePosixPath
from typing import Mapping
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
GENERIC_JSON_FIELDS = ALLOWED_CSV_FIELDS | {"count", "year"}
MANIFEST_TOP_LEVEL_FIELDS = {
    "project",
    "generated_at",
    "privacy_scope",
    "privacy_rules",
    "public_roots",
    "site_files",
    "source_project_policy",
    "datasets",
    "charts",
}
PRIVACY_RULE_FIELDS = {"version", "minimum_group_size", "reviewed_at"}
DATASET_FIELDS = {
    "id",
    "title",
    "path",
    "type",
    "status",
    "last_verified",
    "privacy_note",
    "privacy_dimensions",
}
CHART_FIELDS = {
    "id",
    "title",
    "path",
    "type",
    "status",
    "source_dataset",
    "privacy_note",
}
MANIFEST_JSON_FIELDS = (
    MANIFEST_TOP_LEVEL_FIELDS
    | PRIVACY_RULE_FIELDS
    | DATASET_FIELDS
    | CHART_FIELDS
)
SVG_ELEMENTS = {"svg", "title", "desc", "rect", "text", "line"}
SVG_ATTRIBUTES = {
    "width",
    "height",
    "viewBox",
    "role",
    "aria-labelledby",
    "id",
    "x",
    "y",
    "rx",
    "fill",
    "x1",
    "x2",
    "y1",
    "y2",
    "stroke",
    "stroke-width",
    "text-anchor",
    "font-family",
    "font-size",
    "font-weight",
}
VALUE_PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "phone": re.compile(
        r"(?<!\d)(?:(?:\+?886[- ]?9|09)\d{8}|"
        r"(?:\+?886[- ]?|0)(?:2|[3-8]\d)[- ]?\d{7,8})(?!\d)"
    ),
    "youtube channel id": re.compile(r"\bUC[A-Za-z0-9_-]{22}\b"),
    "creator channel URL": re.compile(
        r"https?://(?:www\.)?(?:"
        r"youtube\.com/(?:channel/|@|c/|user/)|"
        r"twitch\.tv/(?!directory(?:/|$)|videos(?:/|$))"
        r")[^\s\"'<>]+",
        re.I,
    ),
    "raw timestamp": re.compile(
        r"(?<!\d)(?:"
        r"\d{4}-\d{2}-\d{2}(?:[T _-])\d{2}(?:[:-])\d{2}(?:(?:[:-])\d{2})?"
        r"|\d{8}T\d{6}(?:Z|[+-]\d{4})?"
        r")(?!\d)"
    ),
    "individual name label": re.compile(r"\b(?:creator|channel)[_-]?name\s*[:=]", re.I),
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


def _schema_errors(
    label: str,
    value: object,
    allowed_fields: set[str],
    required_fields: set[str],
) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label}: must be an object"]
    errors = []
    unknown = sorted(set(value) - allowed_fields)
    if unknown:
        errors.append(f"{label}: fields not in schema allowlist: {', '.join(unknown)}")
    missing = sorted(required_fields - set(value))
    if missing:
        errors.append(f"{label}: missing required fields: {', '.join(missing)}")
    return errors


def validate_manifest(index: object, index_path: PurePath) -> list[str]:
    errors = _schema_errors(
        "public-index.json",
        index,
        MANIFEST_TOP_LEVEL_FIELDS,
        MANIFEST_TOP_LEVEL_FIELDS,
    )
    if not isinstance(index, dict):
        return errors
    errors.extend(
        _schema_errors(
            "public-index.json: privacy_rules",
            index.get("privacy_rules"),
            PRIVACY_RULE_FIELDS,
            PRIVACY_RULE_FIELDS,
        )
    )

    ids: list[tuple[str, str]] = []
    paths: list[tuple[str, str]] = [(index_path.as_posix(), "public index")]
    for position, item_path in enumerate(index.get("site_files", [])):
        if not isinstance(item_path, str) or not item_path:
            errors.append(f"public-index.json: site_files[{position}] must be a non-empty path")
            continue
        paths.append((item_path, f"site_files[{position}]"))

    for collection, allowed_fields, required_fields in (
        ("datasets", DATASET_FIELDS, DATASET_FIELDS - {"privacy_dimensions"}),
        ("charts", CHART_FIELDS, CHART_FIELDS),
    ):
        items = index.get(collection)
        if not isinstance(items, list):
            errors.append(f"public-index.json: {collection} must be an array")
            continue
        for position, item in enumerate(items):
            label = f"public-index.json: {collection}[{position}]"
            errors.extend(_schema_errors(label, item, allowed_fields, required_fields))
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            item_path = item.get("path")
            if isinstance(item_id, str) and item_id:
                ids.append((item_id, label))
            else:
                errors.append(f"{label}: id must be a non-empty string")
            if isinstance(item_path, str) and item_path:
                paths.append((item_path, label))
            else:
                errors.append(f"{label}: path must be a non-empty string")
            if collection == "datasets" and item.get("status") != "sample":
                dimensions = item.get("privacy_dimensions")
                if (
                    not isinstance(dimensions, list)
                    or not dimensions
                    or any(not isinstance(field, str) or not field for field in dimensions)
                    or len(set(dimensions)) != len(dimensions)
                ):
                    errors.append(
                        f"{label}: real-derived dataset requires unique non-empty "
                        "privacy_dimensions disclosure"
                    )

    for value, locations in _duplicates(ids).items():
        errors.append(
            f"public-index.json: duplicate public artifact id {value}: "
            f"{', '.join(locations)}"
        )
    for value, locations in _duplicates(paths).items():
        errors.append(
            f"public-index.json: duplicate publication path {value}: "
            f"{', '.join(locations)}"
        )
    return errors


def _duplicates(values: list[tuple[str, str]]) -> dict[str, list[str]]:
    locations: dict[str, list[str]] = {}
    for value, location in values:
        locations.setdefault(value, []).append(location)
    return {
        value: occurrences
        for value, occurrences in locations.items()
        if len(occurrences) > 1
    }


def publication_paths(index: dict[str, object], index_path: PurePath) -> set[PurePath]:
    paths = {index_path}
    paths.update(
        PurePosixPath(path)
        for path in index.get("site_files", [])
        if isinstance(path, str) and path
    )
    for collection in ("datasets", "charts"):
        paths.update(
            PurePosixPath(item["path"])
            for item in index.get(collection, [])
            if isinstance(item, dict)
            and isinstance(item.get("path"), str)
            and item.get("path")
        )
    return paths


def find_orphans(allowed: set[PurePath], published: set[PurePath]) -> list[str]:
    return [
        f"{path.as_posix()}: public artifact is not listed in public-index.json"
        for path in sorted(published - allowed, key=lambda item: item.as_posix())
    ]


def _normalize_escapes(text: str) -> str:
    normalized = text
    for _ in range(3):
        previous = normalized
        normalized = html.unescape(normalized).replace("\\/", "/")
        normalized = re.sub(
            r"\\x([0-9A-Fa-f]{2})",
            lambda match: chr(int(match.group(1), 16)),
            normalized,
        )
        normalized = re.sub(
            r"\\u([0-9A-Fa-f]{4})",
            lambda match: chr(int(match.group(1), 16)),
            normalized,
        )
        normalized = re.sub(
            r"\\u\{([0-9A-Fa-f]{1,6})\}",
            lambda match: chr(int(match.group(1), 16)),
            normalized,
        )
        if normalized == previous:
            break
    return normalized


def _scan_values(path: PurePath, text: str) -> list[str]:
    errors = []
    normalized = _normalize_escapes(text)
    for label, pattern in VALUE_PATTERNS.items():
        if pattern.search(normalized):
            errors.append(f"{path.as_posix()}: prohibited value pattern: {label}")
    return errors


def _is_group_size_field(field: str) -> bool:
    field = field.lower()
    return (
        field in {"count", "net", "cumulative_active", "tracked_channels"}
        or field.endswith("_count")
        or field.startswith("recently_active")
        or field.endswith(("_channels", "_hosts", "_streams"))
        or field in {"debuts", "graduations"}
        or field.startswith(("debuts_", "graduations_", "yt_tier_"))
    )


def _group_size_error(
    path: PurePath,
    field: str,
    value: object,
    minimum_group_size: int,
    location: str = "",
) -> list[str]:
    if not minimum_group_size or not _is_group_size_field(field):
        return []
    if isinstance(value, bool):
        return []
    try:
        count = float(value)
    except (TypeError, ValueError):
        return []
    if 0 < abs(count) < minimum_group_size:
        prefix = f"{path.as_posix()}{location}"
        return [
            f"{prefix}: {field}={value} is below "
            f"privacy_rules.minimum_group_size={minimum_group_size}"
        ]
    return []


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
            errors.extend(_scan_values(path, value))
            errors.extend(
                _group_size_error(
                    path,
                    field or "",
                    value,
                    minimum_group_size,
                    f":{row_number}",
                )
            )
    return errors


def _validate_json(path: PurePath, text: str, minimum_group_size: int) -> list[str]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        return [f"{path.as_posix()}: invalid JSON: {error}"]

    errors = []
    allowed_fields = (
        MANIFEST_JSON_FIELDS
        if path.name == "public-index.json"
        else GENERIC_JSON_FIELDS
    )

    def visit(item: object, field: str | None = None) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if key.lower() in PROHIBITED_FIELDS:
                    errors.append(f"{path.as_posix()}: prohibited JSON field: {key}")
                elif key not in allowed_fields:
                    errors.append(
                        f"{path.as_posix()}: field not in schema allowlist: {key}"
                    )
                visit(child, key)
        elif isinstance(item, list):
            for child in item:
                visit(child, field)
        elif isinstance(item, str):
            errors.extend(_scan_values(path, item))
            if field:
                errors.extend(
                    _group_size_error(path, field, item, minimum_group_size)
                )
        elif field and isinstance(item, (int, float)) and not isinstance(item, bool):
            errors.extend(_group_size_error(path, field, item, minimum_group_size))

    visit(value)
    return errors


def _validate_svg(path: PurePath, text: str) -> list[str]:
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as error:
        return [f"{path.as_posix()}: invalid SVG: {error}"]
    errors = []
    for element in root.iter():
        element_name = element.tag.rsplit("}", 1)[-1]
        if element_name.lower() == "metadata":
            errors.append(f"{path.as_posix()}: SVG <metadata> is not allowed")
        elif element_name not in SVG_ELEMENTS:
            errors.append(
                f"{path.as_posix()}: SVG element not in schema allowlist: {element_name}"
            )
        for attribute in element.attrib:
            attribute_name = attribute.rsplit("}", 1)[-1]
            if attribute_name not in SVG_ATTRIBUTES:
                errors.append(
                    f"{path.as_posix()}: SVG attribute not in schema allowlist: "
                    f"{attribute_name}"
                )
    errors.extend(_scan_values(path, text))
    return errors


def validate_text(path: PurePath, text: str, minimum_group_size: int) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _validate_csv(path, text, minimum_group_size)
    if suffix == ".json":
        return _validate_json(path, text, minimum_group_size)
    if suffix == ".svg":
        return _validate_svg(path, text)
    if suffix in {".html", ".js", ".css"}:
        return _scan_values(path, text)
    return [f"{path.as_posix()}: unsupported public artifact type"]


def _safe_relative(path: PurePath) -> bool:
    return not path.is_absolute() and ".." not in path.parts


def _resolved_path_within_root(
    root: Path,
    relative: PurePath,
    *,
    regular_file: bool,
) -> tuple[Path | None, str | None]:
    if not _safe_relative(relative):
        return None, f"{relative.as_posix()}: path must stay within the repository"
    resolved_root = root.resolve()
    candidate = resolved_root.joinpath(*relative.parts)
    current = resolved_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return None, f"{relative.as_posix()}: symbolic link is not a public artifact"
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        return None, f"{relative.as_posix()}: listed public artifact does not exist: {error}"
    if resolved != resolved_root and resolved_root not in resolved.parents:
        return None, f"{relative.as_posix()}: path is outside resolved repository root"
    try:
        mode = resolved.stat().st_mode
    except OSError as error:
        return None, f"{relative.as_posix()}: cannot stat public artifact: {error}"
    expected = stat.S_ISREG(mode) if regular_file else stat.S_ISDIR(mode)
    if not expected:
        kind = "regular file" if regular_file else "directory"
        return None, f"{relative.as_posix()}: public artifact must be a {kind}"
    return resolved, None


def _dataset_rows(path: PurePath, text: str) -> list[dict[str, object]] | None:
    if path.suffix.lower() == ".csv":
        return [dict(row) for row in csv.DictReader(io.StringIO(text))]
    if path.suffix.lower() == ".json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return None
        if isinstance(value, list) and all(isinstance(row, dict) for row in value):
            return value
    return None


def validate_dimension_intersections(
    index: dict[str, object],
    artifact_text: Mapping[PurePath, str],
) -> list[str]:
    disclosed: list[tuple[PurePath, tuple[str, ...], list[dict[str, object]]]] = []
    errors = []
    for item in index.get("datasets", []):
        if not isinstance(item, dict) or item.get("status") == "sample":
            continue
        item_path = item.get("path")
        dimensions = item.get("privacy_dimensions")
        if (
            not isinstance(item_path, str)
            or not isinstance(dimensions, list)
            or not dimensions
            or any(not isinstance(field, str) or not field for field in dimensions)
        ):
            continue
        path = PurePosixPath(item_path)
        rows = _dataset_rows(path, artifact_text.get(path, ""))
        if rows is None:
            errors.append(
                f"{path.as_posix()}: privacy dimension disclosure requires "
                "a CSV or top-level JSON row array"
            )
            continue
        missing = sorted(
            {
                dimension
                for dimension in dimensions
                for row in rows
                if dimension not in row or str(row.get(dimension, "")).strip() == ""
            }
        )
        if missing:
            errors.append(
                f"{path.as_posix()}: privacy_dimensions missing from row data: "
                f"{', '.join(missing)}"
            )
            continue
        disclosed.append((path, tuple(dimensions), rows))

    for left_index, (left_path, left_dimensions, left_rows) in enumerate(disclosed):
        for right_path, right_dimensions, right_rows in disclosed[left_index + 1 :]:
            shared = tuple(sorted(set(left_dimensions) & set(right_dimensions)))
            if len(shared) < 2:
                continue
            left_signatures = Counter(
                tuple(str(row[field]) for field in shared)
                for row in left_rows
            )
            right_signatures = Counter(
                tuple(str(row[field]) for field in shared)
                for row in right_rows
            )
            unique_intersections = sum(
                left_signatures[signature] == 1
                and right_signatures.get(signature) == 1
                for signature in left_signatures
            )
            if unique_intersections:
                errors.append(
                    f"{left_path.as_posix()} + {right_path.as_posix()}: "
                    "cross-artifact unique dimension intersection "
                    f"({', '.join(shared)}; {unique_intersections} signature(s))"
                )
    return errors


def validate_publication(
    root: Path,
    index_path: Path,
) -> tuple[list[str], dict[str, object], dict[PurePath, bytes]]:
    root = root.resolve()
    try:
        index_relative = PurePosixPath(index_path.relative_to(root).as_posix())
    except ValueError:
        return [
            f"{index_path}: public index is outside resolved repository root"
        ], {}, {}
    resolved_index, index_error = _resolved_path_within_root(
        root,
        index_relative,
        regular_file=True,
    )
    if index_error:
        return [index_error], {}, {}
    try:
        index_bytes = resolved_index.read_bytes()
        index = json.loads(index_bytes.decode("utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return [f"{index_path}: cannot read public index: {error}"], {}, {}

    if not isinstance(index, dict):
        return ["public-index.json: top-level value must be an object"], {}, {}
    errors = validate_manifest(index, index_relative)
    allowed = publication_paths(index, index_relative)
    errors.extend(validate_rules(index.get("privacy_rules")))
    if any(not _safe_relative(path) for path in allowed):
        errors.append("public-index.json: all publication paths must stay within the repository")

    published: set[PurePath] = set()
    for public_root in index.get("public_roots", []):
        if not isinstance(public_root, str):
            errors.append("public-index.json: public root must be a string")
            continue
        relative_root = PurePosixPath(public_root)
        if not _safe_relative(relative_root):
            errors.append(f"public-index.json: invalid public root: {public_root}")
            continue
        directory, directory_error = _resolved_path_within_root(
            root,
            relative_root,
            regular_file=False,
        )
        if directory_error:
            errors.append(directory_error)
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
    validated: dict[PurePath, bytes] = {}
    artifact_text: dict[PurePath, str] = {}
    for relative in sorted(allowed, key=lambda path: path.as_posix()):
        path, path_error = _resolved_path_within_root(
            root,
            relative,
            regular_file=True,
        )
        if path_error:
            errors.append(path_error)
            continue
        item_minimum = 0 if status_by_path.get(relative) == "sample" else minimum
        try:
            content = path.read_bytes()
            text = content.decode("utf-8-sig")
        except (OSError, UnicodeError) as error:
            errors.append(f"{relative.as_posix()}: cannot read public artifact: {error}")
            continue
        validated[relative] = content
        artifact_text[relative] = text
        errors.extend(validate_text(relative, text, item_minimum))
    errors.extend(validate_dimension_intersections(index, artifact_text))
    return sorted(set(errors)), index, validated


def stage_publication(
    root: Path,
    destination: Path,
    validated: Mapping[PurePath, bytes],
    rules: dict[str, object],
) -> None:
    resolved_root = root.resolve()
    resolved_destination = destination.resolve()
    if resolved_destination == resolved_root or resolved_root not in resolved_destination.parents:
        raise ValueError("--stage must be a child directory of --root")
    for relative, expected in validated.items():
        source, source_error = _resolved_path_within_root(
            resolved_root,
            relative,
            regular_file=True,
        )
        if source_error:
            raise ValueError(source_error)
        if source.read_bytes() != expected:
            raise ValueError(
                f"{relative.as_posix()}: source bytes changed after validation"
            )
    if destination.exists():
        shutil.rmtree(destination)
    for relative, content in validated.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    report = {
        "rules_version": rules["version"],
        "minimum_group_size": rules["minimum_group_size"],
        "status": "passed",
        "passed_at": datetime.now(timezone.utc).isoformat(),
        "files": sorted(path.as_posix() for path in validated),
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

    errors, index, validated = validate_publication(root, index_path)
    if errors:
        print("\n".join(errors))
        return 1
    if args.stage:
        stage_publication(root, args.stage, validated, index["privacy_rules"])
    print(
        f"Validated {len(validated)} public artifact(s) "
        f"with privacy rules {index['privacy_rules']['version']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
