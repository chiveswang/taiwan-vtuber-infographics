#!/usr/bin/env python3

import unittest
from pathlib import PurePosixPath

from scripts import validate_public_data as gate


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


if __name__ == "__main__":
    unittest.main()
