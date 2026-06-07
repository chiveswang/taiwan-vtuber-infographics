# Public Metrics Catalog

本文件列出此 repo 目前提供或規劃提供的公開指標。所有指標都必須是 aggregate-only，且不得公開 raw tracking rows、個人層級時間序列、個人排名或身份推測。

## Published Metrics

### Platform Coverage Summary

- Dataset: `data/derived/platform-coverage-summary.csv`
- Chart: `charts/exports/platform-coverage-summary.svg`
- Status: `real-derived`
- Source: `TaiwanVtuberData/TaiwanVtuberTrackingData`
- Method: count field presence for YouTube / Twitch platform fields.
- Privacy note: does not publish names, IDs, channel IDs, channel names, or raw rows.

This answers:

- How many upstream entries have YouTube-only, Twitch-only, both, or no public platform field coverage?

This does not answer:

- Which individual VTuber is on which platform.
- Who is larger, more active, or growing faster.

### Source Coverage Summary

- Dataset: `data/derived/source-coverage-summary.csv`
- Chart: `charts/exports/source-coverage-summary.svg`
- Status: `real-derived`
- Source: public GitHub repository file metadata.
- Method: count monthly upstream snapshot files by file family.
- Privacy note: does not copy raw CSV rows.

This answers:

- Which months have which upstream snapshot families?
- How dense is the available public source material by month?

This does not answer:

- Individual activity.
- Stream timing behavior.
- Any creator-level trend.

### Public Status Summary

- Dataset: `data/derived/public-status-summary.csv`
- Chart: `charts/exports/public-status-summary.svg`
- Status: `real-derived`
- Source: `TaiwanVtuberData/TaiwanVtuberTrackingData`
- Method: aggregate upstream `Activity` labels.
- Privacy note: this is not real-time status and does not publish names, IDs, or raw rows.

This answers:

- How many upstream entries are labeled active, preparing, graduated, or unknown?

This does not answer:

- Which individual VTuber has which status.
- Whether any status changed recently.
- Any real-time activity condition.

### Quarterly Ecosystem Coverage

- Dataset: `data/derived/quarterly-ecosystem-coverage.csv`
- Chart: `charts/exports/quarterly-ecosystem-coverage.svg`
- Status: `real-derived`
- Source: public GitHub repository file metadata.
- Method: quarter-level aggregate of monthly source snapshot metadata.
- Privacy note: no raw CSV rows are copied.

This answers:

- How much public source material exists by quarter?

This does not answer:

- Individual activity volume.
- Creator-level growth or popularity.

### Activity Quarterly Summary

- Dataset: `data/derived/activity-quarterly-summary.csv`
- Website: rendered with Chart.js in `site/`
- Status: `real-derived`
- Source: aggregate constants from the local activity dashboard artifact, derived from `TaiwanVtuberData/TaiwanVtuberTrackingData` and `TaiwanVtuberData/TaiwanVTuberTrackingDataArchive`.
- Method: whitelist quarter-level aggregate fields only: tracked channel count, recently active counts, activation rate, subscriber tier counts, top-10 aggregate shares, and livestream aggregate counts.
- Privacy note: does not publish channel names, IDs, rankings, search results, raw rows, or individual time series.

This answers:

- How has the overall tracked ecosystem changed by quarter?
- How do recent activity and activation rate move over time?
- How are subscriber tiers and top-level concentration changing at the industry level?

This does not answer:

- Which creator is active.
- Which channel ranks in the top group.
- Any individual creator growth, schedule, or performance trajectory.

### Cohort Quarterly Summary

- Dataset: `data/derived/cohort-quarterly-summary.csv`
- Website: rendered with Chart.js in `site/`
- Status: `real-derived`
- Source: aggregate constants from the local activity dashboard artifact.
- Method: whitelist quarter-level debut, graduation, net, cumulative, nationality-bucket, and group/indie aggregate counts.
- Privacy note: no creator rows, debut lists, graduation lists, or identity details are published.

This answers:

- When did debut volume peak?
- How does net active cohort growth change over time?
- How do public aggregate group/indie debut buckets change by quarter?

This does not answer:

- Who debuted or graduated in a period.
- Any creator-level lifecycle or private identity information.

### Content Category Quarterly Summary

- Dataset: `data/derived/content-category-quarterly-summary.csv`
- Website: rendered with Chart.js in `site/`
- Status: `real-derived`
- Source: aggregate constants from the local activity dashboard artifact.
- Method: whitelist quarter-level content-category counts for top videos, YouTube livestreams, and Twitch livestreams.
- Privacy note: does not publish titles, publish times, stream URLs, video URLs, channel names, creator IDs, or exact per-creator sequences.

This answers:

- Which content categories dominate latest aggregate top-video and livestream views?
- How does shorts share change over time at aggregate level?

This does not answer:

- Which creator made a specific video.
- Which stream title was classified into which category.
- Any live or per-person schedule.

## Sample Metrics

### Sample Content Category Share

- Dataset: `data/derived/aggregate-summary.csv`
- Chart: `charts/exports/sample-content-category-share.svg`
- Status: `sample`
- Privacy note: fake demo data only.

This remains in the repo only to demonstrate schema and chart generation.

## Candidate Next Metrics

### Individual Exploration From Internal Dashboard

The internal `activity/vtuber_activity_dashboard.html` contains useful exploration features, but the public repo should not copy these features directly:

- channel search / locate yourself
- FAQ answers for a selected channel
- ranking tables
- agency or group deep-dive tables when they expose specific group/member rows
- per-channel growth trajectories
- outlier scatterplots that can identify individual channels

Potential public replacements:

- coarser aggregate buckets
- percentiles without labels
- k-anonymous category summaries
- explanatory text about limitations

Risk level:

- medium to high. Do not implement unless the output remains aggregate-only and cannot be used as a lookup table.
