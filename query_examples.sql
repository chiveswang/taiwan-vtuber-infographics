-- Run from .codex-data/taiwan-vtuber:
-- sqlite3 -header -column vtuber_index.sqlite < query_examples.sql

-- File and CSV counts by source repo.
SELECT repo, COUNT(*) AS files, SUM(ext = '.csv') AS csv_files
FROM files
GROUP BY repo;

-- Snapshot coverage by data kind.
SELECT repo, kind, COUNT(*) AS snapshots, MIN(snapshot_at) AS first_snapshot, MAX(snapshot_at) AS latest_snapshot
FROM snapshots
GROUP BY repo, kind
ORDER BY repo, kind;

-- Current top channels by YouTube subscriber count.
SELECT
  t.display_name,
  b.youtube_subscriber_count,
  b.youtube_view_count,
  b.twitch_follower_count
FROM v_track_list t
JOIN v_latest_basic_data b
  ON b.repo = t.repo AND b.vtuber_id = t.id
WHERE t.repo = 'current'
ORDER BY COALESCE(b.youtube_subscriber_count, 0) DESC
LIMIT 20;

-- Search latest YouTube/Twitch video and livestream titles.
SELECT
  t.display_name,
  v.kind,
  v.video_type,
  v.publish_time,
  v.title,
  v.url
FROM v_latest_videos v
LEFT JOIN v_track_list t
  ON t.repo = v.repo AND t.id = v.vtuber_id
WHERE v.repo = 'current'
  AND v.title LIKE '%歌%'
ORDER BY v.publish_time DESC
LIMIT 50;

-- Inspect sampled CSV schemas.
SELECT repo, kind, sample_path, header_json
FROM schemas
ORDER BY repo, kind, sample_path;
