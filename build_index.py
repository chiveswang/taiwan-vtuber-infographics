import csv
import argparse
import io
import json
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "vtuber_index.sqlite"

REPOS = {
    "archive": {
        "github": "TaiwanVtuberData/TaiwanVTuberTrackingDataArchive",
        "path": ROOT / "archive",
    },
    "current": {
        "github": "TaiwanVtuberData/TaiwanVtuberTrackingData",
        "path": ROOT / "current",
    },
}

CSV_KIND_RE = re.compile(
    r"^(?P<kind>twitch-livestreams|basic-data|top-videos|livestreams|record)_"
    r"(?P<stamp>\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})\.csv$"
)


def run_git(repo_path: Path, *args: str, text: bool = True):
    proc = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if text:
        return proc.stdout.decode("utf-8", errors="replace")
    return proc.stdout


def normalize_header(name: str) -> str:
    name = name.strip().lstrip("\ufeff")
    return re.sub(r"^V\d+##", "", name)


def parse_csv_path(path: str):
    base = Path(path).name
    if path == "DATA/TW_VTUBER_TRACK_LIST.csv":
        return "track-list", None
    if path == "DATA/EXCLUDE_LIST.csv":
        return "exclude-list", None
    match = CSV_KIND_RE.match(base)
    if not match:
        return None, None
    stamp = match.group("stamp")
    snapshot_at = datetime.strptime(stamp, "%Y-%m-%d-%H-%M-%S").strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return match.group("kind"), snapshot_at


def iter_tree(repo_key: str, repo_path: Path):
    output = run_git(repo_path, "ls-tree", "-r", "HEAD")
    for line in output.splitlines():
        if "\t" not in line:
            continue
        meta, path = line.split("\t", 1)
        parts = meta.split()
        if len(parts) < 3:
            continue
        mode, obj_type, oid = parts[:3]
        size = None
        kind, snapshot_at = parse_csv_path(path)
        yield {
            "repo": repo_key,
            "path": path,
            "filename": Path(path).name,
            "ext": Path(path).suffix.lower(),
            "mode": mode,
            "object_type": obj_type,
            "blob_oid": oid,
            "blob_size": size,
            "kind": kind,
            "snapshot_at": snapshot_at,
            "year_month": path.split("/", 1)[0] if "/" in path else None,
        }


def git_show_text(repo_path: Path, path: str) -> str:
    data = run_git(repo_path, "show", f"HEAD:{path}", text=False)
    return data.decode("utf-8-sig", errors="replace")


def read_csv(repo_path: Path, path: str):
    text = git_show_text(repo_path, path)
    stream = io.StringIO(text, newline="")
    reader = csv.DictReader(stream)
    if reader.fieldnames:
        reader.fieldnames = [normalize_header(f) for f in reader.fieldnames]
    return list(reader), reader.fieldnames or []


def create_schema(conn: sqlite3.Connection):
    conn.executescript(
        """
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = NORMAL;

        DROP TABLE IF EXISTS repos;
        DROP TABLE IF EXISTS files;
        DROP TABLE IF EXISTS snapshots;
        DROP TABLE IF EXISTS schemas;
        DROP TABLE IF EXISTS track_list;
        DROP TABLE IF EXISTS exclude_list;
        DROP TABLE IF EXISTS latest_rows;
        DROP TABLE IF EXISTS metadata;

        CREATE TABLE repos (
            repo TEXT PRIMARY KEY,
            github TEXT NOT NULL,
            local_path TEXT NOT NULL,
            head TEXT NOT NULL,
            indexed_at TEXT NOT NULL
        );

        CREATE TABLE files (
            repo TEXT NOT NULL,
            path TEXT NOT NULL,
            filename TEXT NOT NULL,
            ext TEXT,
            mode TEXT,
            object_type TEXT,
            blob_oid TEXT,
            blob_size INTEGER,
            kind TEXT,
            snapshot_at TEXT,
            year_month TEXT,
            PRIMARY KEY (repo, path)
        );

        CREATE TABLE snapshots (
            repo TEXT NOT NULL,
            kind TEXT NOT NULL,
            snapshot_at TEXT NOT NULL,
            path TEXT NOT NULL,
            blob_size INTEGER,
            PRIMARY KEY (repo, kind, snapshot_at, path)
        );

        CREATE TABLE schemas (
            repo TEXT NOT NULL,
            kind TEXT NOT NULL,
            sample_path TEXT NOT NULL,
            header_json TEXT NOT NULL,
            sample_rows_json TEXT NOT NULL,
            PRIMARY KEY (repo, kind, sample_path)
        );

        CREATE TABLE track_list (
            repo TEXT NOT NULL,
            id TEXT NOT NULL,
            display_name TEXT,
            alias_names TEXT,
            youtube_channel_id TEXT,
            twitch_channel_id TEXT,
            twitch_channel_name TEXT,
            debut_date TEXT,
            graduation_date TEXT,
            activity TEXT,
            group_name TEXT,
            nationality TEXT,
            is_section INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (repo, id)
        );

        CREATE TABLE exclude_list (
            repo TEXT NOT NULL,
            id TEXT NOT NULL,
            PRIMARY KEY (repo, id)
        );

        CREATE TABLE latest_rows (
            repo TEXT NOT NULL,
            kind TEXT NOT NULL,
            snapshot_at TEXT NOT NULL,
            vtuber_id TEXT,
            title TEXT,
            url TEXT,
            publish_time TEXT,
            video_type TEXT,
            row_json TEXT NOT NULL
        );

        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE INDEX idx_files_kind_time ON files(repo, kind, snapshot_at);
        CREATE INDEX idx_files_year_month ON files(repo, year_month);
        CREATE INDEX idx_snapshots_kind_time ON snapshots(kind, snapshot_at);
        CREATE INDEX idx_track_name ON track_list(display_name);
        CREATE INDEX idx_latest_kind_id ON latest_rows(repo, kind, vtuber_id);
        CREATE INDEX idx_latest_title ON latest_rows(kind, title);
        CREATE INDEX idx_latest_url ON latest_rows(url);

        DROP VIEW IF EXISTS v_track_list;
        CREATE VIEW v_track_list AS
            SELECT *
            FROM track_list
            WHERE is_section = 0;

        DROP VIEW IF EXISTS v_latest_basic_data;
        CREATE VIEW v_latest_basic_data AS
            SELECT
                repo,
                snapshot_at,
                vtuber_id,
                CAST(NULLIF(json_extract(row_json, '$."YouTube Subscriber Count"'), '') AS INTEGER)
                    AS youtube_subscriber_count,
                CAST(NULLIF(json_extract(row_json, '$."YouTube View Count"'), '') AS INTEGER)
                    AS youtube_view_count,
                json_extract(row_json, '$."YouTube Thumbnail URL"') AS youtube_thumbnail_url,
                CAST(NULLIF(json_extract(row_json, '$."Twitch Follower Count"'), '') AS INTEGER)
                    AS twitch_follower_count,
                json_extract(row_json, '$."Twitch Thumbnail URL"') AS twitch_thumbnail_url
            FROM latest_rows
            WHERE kind = 'basic-data';

        DROP VIEW IF EXISTS v_latest_record;
        CREATE VIEW v_latest_record AS
            SELECT
                repo,
                snapshot_at,
                vtuber_id,
                CAST(NULLIF(json_extract(row_json, '$."YouTube Subscriber Count"'), '') AS INTEGER)
                    AS youtube_subscriber_count,
                CAST(NULLIF(json_extract(row_json, '$."YouTube View Count"'), '') AS INTEGER)
                    AS youtube_view_count,
                CAST(NULLIF(COALESCE(
                    json_extract(row_json, '$."YouTube Recent Total Median View Count"'),
                    json_extract(row_json, '$."YouTube Recent Median View Count"')
                ), '') AS INTEGER) AS youtube_recent_median_view_count,
                CAST(NULLIF(json_extract(row_json, '$."YouTube Recent Total Popularity"'), '') AS INTEGER)
                    AS youtube_recent_total_popularity,
                CAST(NULLIF(COALESCE(
                    json_extract(row_json, '$."YouTube Recent Total Highest View Count"'),
                    json_extract(row_json, '$."YouTube Recent Highest View Count"')
                ), '') AS INTEGER) AS youtube_recent_highest_view_count,
                COALESCE(
                    json_extract(row_json, '$."YouTube Recent Total Highest Viewed URL"'),
                    json_extract(row_json, '$."YouTube Recent Highest Viewed Video URL"')
                ) AS youtube_recent_highest_viewed_url,
                CAST(NULLIF(json_extract(row_json, '$."Twitch Follower Count"'), '') AS INTEGER)
                    AS twitch_follower_count,
                CAST(NULLIF(json_extract(row_json, '$."Twitch Recent Median View Count"'), '') AS INTEGER)
                    AS twitch_recent_median_view_count,
                CAST(NULLIF(json_extract(row_json, '$."Twitch Recent Popularity"'), '') AS INTEGER)
                    AS twitch_recent_popularity,
                CAST(NULLIF(json_extract(row_json, '$."Twitch Recent Highest View Count"'), '') AS INTEGER)
                    AS twitch_recent_highest_view_count,
                json_extract(row_json, '$."Twitch Recent Highest Viewed URL"')
                    AS twitch_recent_highest_viewed_url
            FROM latest_rows
            WHERE kind = 'record';

        DROP VIEW IF EXISTS v_latest_videos;
        CREATE VIEW v_latest_videos AS
            SELECT
                repo,
                kind,
                snapshot_at,
                vtuber_id,
                video_type,
                CAST(NULLIF(json_extract(row_json, '$."View Count"'), '') AS INTEGER) AS view_count,
                title,
                publish_time,
                url,
                json_extract(row_json, '$."Thumbnail URL"') AS thumbnail_url
            FROM latest_rows
            WHERE kind IN ('livestreams', 'top-videos', 'twitch-livestreams');
        """
    )


def insert_files(conn: sqlite3.Connection, rows):
    conn.executemany(
        """
        INSERT INTO files (
            repo, path, filename, ext, mode, object_type, blob_oid, blob_size,
            kind, snapshot_at, year_month
        ) VALUES (
            :repo, :path, :filename, :ext, :mode, :object_type, :blob_oid,
            :blob_size, :kind, :snapshot_at, :year_month
        )
        """,
        rows,
    )
    snapshot_rows = [
        {
            "repo": row["repo"],
            "kind": row["kind"],
            "snapshot_at": row["snapshot_at"],
            "path": row["path"],
            "blob_size": row["blob_size"],
        }
        for row in rows
        if row["ext"] == ".csv" and row["kind"] and row["snapshot_at"]
    ]
    conn.executemany(
        """
        INSERT INTO snapshots (repo, kind, snapshot_at, path, blob_size)
        VALUES (:repo, :kind, :snapshot_at, :path, :blob_size)
        """,
        snapshot_rows,
    )


def insert_schema_samples(conn: sqlite3.Connection, repo_key: str, repo_path: Path):
    kinds = [
        "basic-data",
        "record",
        "livestreams",
        "top-videos",
        "twitch-livestreams",
        "track-list",
        "exclude-list",
    ]
    for kind in kinds:
        paths = [
            row[0]
            for row in conn.execute(
                """
                SELECT path FROM files
                WHERE repo = ? AND kind = ?
                ORDER BY snapshot_at IS NULL, snapshot_at, path
                """,
                (repo_key, kind),
            ).fetchall()
        ]
        selected = []
        if paths:
            selected.append(paths[0])
            if paths[-1] != paths[0]:
                selected.append(paths[-1])
        for path in selected:
            rows, headers = read_csv(repo_path, path)
            conn.execute(
                """
                INSERT INTO schemas (
                    repo, kind, sample_path, header_json, sample_rows_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    repo_key,
                    kind,
                    path,
                    json.dumps(headers, ensure_ascii=False),
                    json.dumps(rows[:3], ensure_ascii=False),
                ),
            )


def insert_track_lists(conn: sqlite3.Connection, repo_key: str, repo_path: Path):
    path = "DATA/TW_VTUBER_TRACK_LIST.csv"
    rows, _ = read_csv(repo_path, path)
    for row in rows:
        id_value = (row.get("ID") or "").strip()
        if not id_value:
            continue
        conn.execute(
            """
            INSERT OR REPLACE INTO track_list (
                repo, id, display_name, alias_names, youtube_channel_id,
                twitch_channel_id, twitch_channel_name, debut_date,
                graduation_date, activity, group_name, nationality, is_section
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                repo_key,
                id_value,
                row.get("Display Name"),
                row.get("Alias Names"),
                row.get("Youtube Channel ID"),
                row.get("Twitch Channel ID"),
                row.get("Twitch Channel Name"),
                row.get("Debut Date"),
                row.get("Graduation Date"),
                row.get("Activity"),
                row.get("Group Name"),
                row.get("Nationality"),
                1 if id_value.startswith("##") else 0,
            ),
        )

    path = "DATA/EXCLUDE_LIST.csv"
    rows, _ = read_csv(repo_path, path)
    for row in rows:
        id_value = (row.get("ID") or "").strip()
        if not id_value:
            continue
        conn.execute(
            "INSERT OR REPLACE INTO exclude_list (repo, id) VALUES (?, ?)",
            (repo_key, id_value),
        )


def latest_paths(conn: sqlite3.Connection, repo_key: str):
    rows = conn.execute(
        """
        SELECT s.kind, s.snapshot_at, s.path
        FROM snapshots s
        JOIN (
            SELECT repo, kind, MAX(snapshot_at) AS max_snapshot_at
            FROM snapshots
            WHERE repo = ?
            GROUP BY repo, kind
        ) m
        ON s.repo = m.repo
           AND s.kind = m.kind
           AND s.snapshot_at = m.max_snapshot_at
        WHERE s.repo = ?
        ORDER BY s.kind
        """,
        (repo_key, repo_key),
    ).fetchall()
    return rows


def insert_latest_rows(conn: sqlite3.Connection, repo_key: str, repo_path: Path):
    for kind, snapshot_at, path in latest_paths(conn, repo_key):
        rows, _ = read_csv(repo_path, path)
        for row in rows:
            vtuber_id = (row.get("VTuber ID") or "").strip() or None
            conn.execute(
                """
                INSERT INTO latest_rows (
                    repo, kind, snapshot_at, vtuber_id, title, url,
                    publish_time, video_type, row_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    repo_key,
                    kind,
                    snapshot_at,
                    vtuber_id,
                    row.get("Title"),
                    row.get("URL"),
                    row.get("Publish Time"),
                    row.get("Video Type"),
                    json.dumps(row, ensure_ascii=False),
                ),
            )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive-content",
        action="store_true",
        help="Also read archive CSV blobs for schema/list/latest-row imports.",
    )
    args = parser.parse_args()

    for db_file in ROOT.glob("vtuber_index.sqlite*"):
        db_file.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        create_schema(conn)
        indexed_at = datetime.now(timezone.utc).isoformat()
        for repo_key, config in REPOS.items():
            repo_path = config["path"]
            print(f"[{repo_key}] reading git tree", flush=True)
            head = run_git(repo_path, "rev-parse", "HEAD").strip()
            conn.execute(
                """
                INSERT INTO repos (repo, github, local_path, head, indexed_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (repo_key, config["github"], str(repo_path), head, indexed_at),
            )
            rows = list(iter_tree(repo_key, repo_path))
            insert_files(conn, rows)
            conn.commit()
            print(f"[{repo_key}] indexed {len(rows)} files", flush=True)

            should_read_content = repo_key == "current" or args.archive_content
            if should_read_content:
                print(f"[{repo_key}] reading CSV samples and latest snapshots", flush=True)
                insert_schema_samples(conn, repo_key, repo_path)
                insert_track_lists(conn, repo_key, repo_path)
                insert_latest_rows(conn, repo_key, repo_path)
                conn.commit()
                print(f"[{repo_key}] imported CSV content subset", flush=True)
            else:
                print(
                    f"[{repo_key}] skipped CSV blob reads; rerun with --archive-content if needed",
                    flush=True,
                )

        conn.execute(
            "INSERT INTO metadata (key, value) VALUES (?, ?)",
            ("indexed_at", indexed_at),
        )
        conn.commit()
    finally:
        conn.close()

    print(DB_PATH)


if __name__ == "__main__":
    main()
