# Upstream Field Inventory

Inventory date: 2026-06-07

Source repo: [TaiwanVtuberData/TaiwanVtuberTrackingData](https://github.com/TaiwanVtuberData/TaiwanVtuberTrackingData)

This inventory reads upstream public CSV headers and file metadata only. Raw upstream rows are not copied into this repo.

## Current Repo Files Reviewed

| Upstream file | Rows including header | Header | Initial use decision |
| --- | ---: | --- | --- |
| `DATA/TW_VTUBER_TRACK_LIST.csv` | 4516 | `ID`, `Display Name`, `Alias Names`, `Youtube Channel ID`, `Twitch Channel ID`, `Twitch Channel Name`, `Debut Date`, `Graduation Date`, `Activity`, `Group Name`, `Nationality` | Use only for aggregate platform coverage in first real batch. Do not publish names or IDs. |
| `DATA/EXCLUDE_LIST.csv` | 1459 | `ID` | Do not publish. May be used only as upstream methodology context if needed. |
| `2026-06/basic-data_2026-06-07-11-58-27.csv` | 3036 | `VTuber ID`, `YouTube Subscriber Count`, `YouTube View Count`, `YouTube Thumbnail URL`, `Twitch Follower Count`, `Twitch Thumbnail URL` | High risk for individual ranking and growth analysis. Do not use in first real batch. |
| `2026-06/livestreams_2026-06-07-06-58-48.csv` | 628 | `VTuber ID`, `Video Type`, `Title`, `Publish Time`, `URL`, `Thumbnail URL` | High risk for individual activity timeline. Do not use in first real batch. |
| `2026-06/twitch-livestreams_2026-06-07-11-30-05.csv` | 46 | `VTuber ID`, `Video Type`, `Title`, `Publish Time`, `URL`, `Thumbnail URL` | High risk for real-time or fine-grained activity inference. Do not use in first real batch. |

## Field Risk Classification

### Safe For First Aggregate Batch

- presence of `Youtube Channel ID`
- presence of `Twitch Channel ID`
- presence of `Twitch Channel Name`
- upstream file counts by month and file family
- latest upstream snapshot timestamp by file family

These should be published only as counts, not as individual rows.

### Potentially Useful Later With Aggregation

- `Debut Date`
- `Graduation Date`
- `Activity`
- `Group Name`
- `Nationality`
- `Video Type`

These need category normalization, sample-size thresholds, and privacy review before publication.

### Do Not Publish As Public Derived Data

- `ID`
- `VTuber ID`
- `Display Name`
- `Alias Names`
- channel IDs or channel names as rows
- `Title`
- `URL`
- `Thumbnail URL`
- subscriber, follower, and view counts at individual level
- `Publish Time` at stream or video row level

## First Real Batch Decision

Proceed with:

- `platform-coverage-summary.csv`
- `source-coverage-summary.csv`

Do not proceed yet with:

- livestream frequency charts
- subscriber / follower growth charts
- individual channel lists
- title or URL based content classification
