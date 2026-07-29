#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path, PurePosixPath

from scripts import validate_public_data as gate


def _dataset(item_id: str, path: str) -> dict[str, object]:
    return {
        "id": item_id,
        "title": f"Aggregate {item_id}",
        "path": path,
        "type": "csv",
        "status": "real-derived",
        "last_verified": "2026-07-29",
        "privacy_note": "Aggregate-only fixture.",
        "privacy_dimensions": ["aggregate_period", "category"],
    }


def _chart(item_id: str, path: str, source_dataset: str) -> dict[str, str]:
    return {
        "id": item_id,
        "title": f"Aggregate {item_id}",
        "path": path,
        "type": "svg",
        "status": "real-derived",
        "source_dataset": source_dataset,
        "privacy_note": "Aggregate-only fixture.",
    }


def _write_index(
    root: Path,
    *,
    datasets: list[dict[str, object]] | None = None,
    charts: list[dict[str, str]] | None = None,
    site_files: list[str] | None = None,
    public_roots: list[str] | None = None,
) -> Path:
    index_path = root / "data" / "derived" / "public-index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index = {
        "project": "privacy-gate-fixture",
        "generated_at": "2026-07-29",
        "privacy_scope": "aggregate-only fixture",
        "privacy_rules": {
            "version": "test",
            "minimum_group_size": 10,
            "reviewed_at": "2026-07-29",
        },
        "public_roots": public_roots or ["data/derived"],
        "site_files": site_files or [],
        "source_project_policy": "Public aggregate fixtures only.",
        "datasets": datasets or [],
        "charts": charts or [],
    }
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return index_path


def _safe_csv(count: int = 10, category: str = "music") -> str:
    return (
        "aggregate_period,category,aggregate_count,source_url,last_verified\n"
        f"2026-Q1,{category},{count},https://github.com/example/source,2026-07-29\n"
    )


class PublicDataGateTests(unittest.TestCase):
    def test_rejects_identifiers_hidden_in_each_public_format(self) -> None:
        cases = {
            "neutral.csv": (
                "aggregate_period,aggregate_count,source_url,last_verified\n"
                "2026-Q1,UCabcdefghijklmnopqrstuv,https://github.com/example/source,2026-07-29\n"
            ),
            "payload.json": '{"label":"creator@example.com"}',
            "chart.svg": (
                "<svg xmlns='http://www.w3.org/2000/svg'>"
                "<metadata>Creator Name</metadata><title>Aggregate chart</title></svg>"
            ),
            "index.html": (
                "<!doctype html><div data-tooltip='https://youtube.com/channel/"
                "UCabcdefghijklmnopqrstuv'>Aggregate</div>"
            ),
            "app.js": "const label = 'creator@example.com';",
            "timeline.json": '{"seen_at":"2026-07-29T12:34:56"}',
        }
        validate_text = getattr(gate, "validate_text", lambda _path, _text, _minimum: [])
        for path, text in cases.items():
            with self.subTest(path=path):
                self.assertTrue(validate_text(PurePosixPath(path), text, 10))

    def test_missing_minimum_group_size_fails_closed(self) -> None:
        validate_rules = getattr(gate, "validate_rules", lambda _rules: [])
        errors = validate_rules(
            {"version": "1.0", "minimum_group_size": None, "reviewed_at": "2026-07-29"}
        )
        self.assertTrue(any("minimum_group_size" in error for error in errors))

    def test_small_positive_aggregate_cell_is_rejected(self) -> None:
        text = (
            "aggregate_period,aggregate_count,source_url,last_verified\n"
            "2026-Q1,3,https://github.com/example/source,2026-07-29\n"
        )
        validate_text = getattr(gate, "validate_text", lambda _path, _text, _minimum: [])
        errors = validate_text(PurePosixPath("summary.csv"), text, 10)
        self.assertTrue(any("minimum_group_size" in error for error in errors))

    def test_manifest_is_the_publication_allowlist(self) -> None:
        index = {
            "site_files": ["index.html", "app.js"],
            "datasets": [{"path": "summary.csv"}],
            "charts": [{"path": "summary.svg"}],
        }
        publication_paths = getattr(gate, "publication_paths", lambda _index, _path: set())
        paths = publication_paths(index, PurePosixPath("public-index.json"))
        self.assertEqual(
            {
                PurePosixPath("app.js"),
                PurePosixPath("index.html"),
                PurePosixPath("public-index.json"),
                PurePosixPath("summary.csv"),
                PurePosixPath("summary.svg"),
            },
            paths,
        )

        find_orphans = getattr(gate, "find_orphans", lambda _allowed, _published: [])
        errors = find_orphans(paths, paths | {PurePosixPath("orphan.json")})
        self.assertTrue(any("not listed in public-index.json" in error for error in errors))

    def test_rejects_symlinked_artifact_even_when_target_is_a_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "repo"
            data = root / "data" / "derived"
            data.mkdir(parents=True)
            outside = base / "outside.csv"
            outside.write_text(_safe_csv(), encoding="utf-8")
            linked = data / "linked.csv"
            try:
                linked.symlink_to(outside)
            except OSError as error:
                self.skipTest(f"symlink fixture unavailable: {error}")
            index_path = _write_index(
                root,
                datasets=[_dataset("linked", "data/derived/linked.csv")],
            )

            errors, _, _ = gate.validate_publication(root, index_path)

            self.assertTrue(
                any(
                    "symbolic link" in error
                    or "outside resolved repository root" in error
                    for error in errors
                ),
                errors,
            )

    def test_rejects_duplicate_ids_and_paths_before_manifest_deduplication(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data" / "derived"
            data.mkdir(parents=True)
            shared = data / "shared.csv"
            shared.write_text(_safe_csv(), encoding="utf-8")
            index_path = _write_index(
                root,
                datasets=[_dataset("same-id", "data/derived/shared.csv")],
                charts=[
                    _chart(
                        "same-id",
                        "data/derived/shared.csv",
                        "data/derived/shared.csv",
                    )
                ],
                site_files=["data/derived/public-index.json"],
            )

            errors, _, _ = gate.validate_publication(root, index_path)

            self.assertTrue(any("duplicate public artifact id" in error for error in errors), errors)
            self.assertGreaterEqual(
                sum("duplicate publication path" in error for error in errors),
                2,
                errors,
            )

    def test_rejects_canonical_path_alias_without_lowering_k_size(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data" / "derived"
            data.mkdir(parents=True)
            shared = data / "shared.csv"
            shared.write_text(_safe_csv(3), encoding="utf-8")
            sample_alias = _dataset("sample-alias", "data//derived/shared.csv")
            sample_alias["status"] = "sample"
            index_path = _write_index(
                root,
                datasets=[
                    _dataset("real", "data/derived/shared.csv"),
                    sample_alias,
                ],
            )

            errors, _, _ = gate.validate_publication(root, index_path)

            self.assertTrue(
                any("duplicate publication path data/derived/shared.csv" in error for error in errors),
                errors,
            )
            self.assertTrue(any("minimum_group_size" in error for error in errors), errors)

    def test_k_size_covers_net_recent_activity_and_json_counts_without_flagging_ratios(self) -> None:
        csv_cases = {
            "net.csv": (
                "aggregate_period,net,source_url,last_verified\n"
                "2026-Q1,-3,https://github.com/example/source,2026-07-29\n"
            ),
            "activity.csv": (
                "aggregate_period,recently_active_any,activation_rate,source_url,last_verified\n"
                "2026-Q1,4,0.04,https://github.com/example/source,2026-07-29\n"
            ),
        }
        for path, text in csv_cases.items():
            with self.subTest(path=path):
                errors = gate.validate_text(PurePosixPath(path), text, 10)
                self.assertTrue(any("minimum_group_size" in error for error in errors), errors)

        errors = gate.validate_text(
            PurePosixPath("counts.json"),
            '{"year":2026,"activation_rate":0.04,"count":3,"aggregate_count":12}',
            10,
        )
        self.assertTrue(any("count=3" in error for error in errors), errors)
        self.assertFalse(any("year=2026" in error for error in errors), errors)
        self.assertFalse(any("activation_rate=0.04" in error for error in errors), errors)

    def test_rejects_creator_url_in_source_url(self) -> None:
        text = (
            "aggregate_period,aggregate_count,source_url,last_verified\n"
            "2026-Q1,12,https://youtube.com/@individual_creator,2026-07-29\n"
        )
        errors = gate.validate_text(PurePosixPath("source.csv"), text, 10)
        self.assertTrue(any("creator channel URL" in error for error in errors), errors)

    def test_normalizes_percent_encoded_and_protocol_relative_creator_urls(self) -> None:
        cases = {
            "percent-encoded.csv": "https://youtube.com/%40creator",
            "protocol-relative.csv": "//youtube.com/@creator",
        }
        for path, source_url in cases.items():
            with self.subTest(path=path):
                text = (
                    "aggregate_period,aggregate_count,source_url,last_verified\n"
                    f"2026-Q1,12,{source_url},2026-07-29\n"
                )
                errors = gate.validate_text(PurePosixPath(path), text, 10)
                self.assertTrue(
                    any("creator channel URL" in error for error in errors),
                    errors,
                )

    def test_normalizes_html_json_and_js_escapes_and_compact_timestamps(self) -> None:
        cases = {
            "entity.html": "<p>creator&#64;example.com</p>",
            "escaped.json": '{"label":"creator\\u0040example.com"}',
            "escaped.js": "const contact = 'creator\\x40example.com';",
            "escaped-url.js": "const source = 'https:\\/\\/youtube.com\\/@creator';",
            "compact.json": '{"seen_at":"20260729T123456Z"}',
        }
        for path, text in cases.items():
            with self.subTest(path=path):
                errors = gate.validate_text(PurePosixPath(path), text, 10)
                self.assertTrue(errors, path)

    def test_rejects_svg_name_metadata_and_individual_labels(self) -> None:
        cases = {
            "name.svg": (
                "<svg xmlns='http://www.w3.org/2000/svg'>"
                "<text name='Alice'>Aggregate</text></svg>"
            ),
            "title.svg": (
                "<svg xmlns='http://www.w3.org/2000/svg'>"
                "<title>creator_name: Alice</title></svg>"
            ),
            "desc.svg": (
                "<svg xmlns='http://www.w3.org/2000/svg'>"
                "<desc>channel_name=Alice</desc></svg>"
            ),
        }
        for path, text in cases.items():
            with self.subTest(path=path):
                errors = gate.validate_text(PurePosixPath(path), text, 10)
                self.assertTrue(errors, path)

    def test_rejects_generic_name_in_json_without_a_reviewed_schema(self) -> None:
        errors = gate.validate_text(
            PurePosixPath("renamed.json"),
            '{"name":"Alice","aggregate_count":12}',
            10,
        )
        self.assertTrue(any("field not in schema allowlist: name" in error for error in errors), errors)

    def test_rejects_cross_artifact_unique_dimension_intersection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data" / "derived"
            data.mkdir(parents=True)
            first = data / "first.csv"
            second = data / "second.csv"
            first.write_text(_safe_csv(12, "music"), encoding="utf-8")
            second.write_text(_safe_csv(14, "music"), encoding="utf-8")
            index_path = _write_index(
                root,
                datasets=[
                    _dataset("first", "data/derived/first.csv"),
                    _dataset("second", "data/derived/second.csv"),
                ],
            )

            errors, _, _ = gate.validate_publication(root, index_path)

            self.assertTrue(
                any("cross-artifact unique dimension intersection" in error for error in errors),
                errors,
            )

    def test_rejects_unique_intersection_on_one_shared_dimension(self) -> None:
        first = _dataset("first", "data/derived/first.csv")
        second = _dataset("second", "data/derived/second.csv")
        first["privacy_dimensions"] = ["aggregate_period"]
        second["privacy_dimensions"] = ["aggregate_period"]
        errors = gate.validate_dimension_intersections(
            {"datasets": [first, second]},
            {
                PurePosixPath(first["path"]): (
                    "aggregate_period,aggregate_count,source_url,last_verified\n"
                    "2026-Q1,12,https://github.com/example/source,2026-07-29\n"
                ),
                PurePosixPath(second["path"]): (
                    "aggregate_period,aggregate_count,source_url,last_verified\n"
                    "2026-Q1,14,https://github.com/example/source,2026-07-29\n"
                ),
            },
        )

        self.assertTrue(
            any("cross-artifact unique dimension intersection" in error for error in errors),
            errors,
        )

    def test_rejects_under_disclosed_row_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data" / "derived"
            data.mkdir(parents=True)
            source = data / "summary.csv"
            source.write_text(
                "aggregate_period,category,aggregate_count,source_url,last_verified\n"
                "2026-Q1,music,12,https://github.com/example/source,2026-07-29\n"
                "2026-Q1,gaming,14,https://github.com/example/source,2026-07-29\n",
                encoding="utf-8",
            )
            dataset = _dataset("summary", "data/derived/summary.csv")
            dataset["privacy_dimensions"] = ["aggregate_period"]
            index_path = _write_index(root, datasets=[dataset])

            errors, _, _ = gate.validate_publication(root, index_path)

            self.assertTrue(
                any(
                    "privacy_dimensions under-discloses row dimensions: category" in error
                    for error in errors
                ),
                errors,
            )

    def test_normalizes_blank_dimensions_and_signature_values(self) -> None:
        blank = _dataset("blank", "data/derived/blank.csv")
        blank["privacy_dimensions"] = ["   "]
        errors = gate.validate_manifest(
            {
                "project": "privacy-gate-fixture",
                "generated_at": "2026-07-29",
                "privacy_scope": "aggregate-only fixture",
                "privacy_rules": {
                    "version": "test",
                    "minimum_group_size": 10,
                    "reviewed_at": "2026-07-29",
                },
                "public_roots": ["data/derived"],
                "site_files": [],
                "source_project_policy": "Public aggregate fixtures only.",
                "datasets": [blank],
                "charts": [],
            },
            PurePosixPath("data/derived/public-index.json"),
        )
        self.assertTrue(
            any("requires unique non-empty privacy_dimensions" in error for error in errors),
            errors,
        )

        first = _dataset("first", "data/derived/first.csv")
        second = _dataset("second", "data/derived/second.csv")
        first["privacy_dimensions"] = ["category"]
        second["privacy_dimensions"] = ["category"]
        errors = gate.validate_dimension_intersections(
            {"datasets": [first, second]},
            {
                PurePosixPath(first["path"]): _safe_csv(12, " music "),
                PurePosixPath(second["path"]): _safe_csv(14, "music"),
            },
        )
        self.assertTrue(
            any("cross-artifact unique dimension intersection" in error for error in errors),
            errors,
        )

    def test_stage_rejects_source_bytes_changed_after_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = root / "data" / "derived"
            data.mkdir(parents=True)
            source = data / "summary.csv"
            original = _safe_csv(12)
            source.write_text(original, encoding="utf-8")
            index_path = _write_index(
                root,
                datasets=[_dataset("summary", "data/derived/summary.csv")],
            )
            errors, index, validated = gate.validate_publication(root, index_path)
            self.assertEqual([], errors)

            source.write_text(_safe_csv(14), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed after validation"):
                gate.stage_publication(
                    root,
                    root / "_site",
                    validated,
                    index["privacy_rules"],
                )

            source.write_text(original, encoding="utf-8")
            errors, index, validated = gate.validate_publication(root, index_path)
            self.assertEqual([], errors)
            gate.stage_publication(
                root,
                root / "_site",
                validated,
                index["privacy_rules"],
            )
            self.assertEqual(
                source.read_bytes(),
                (root / "_site" / "data" / "derived" / "summary.csv").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
