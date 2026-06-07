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

## Sample Metrics

### Sample Content Category Share

- Dataset: `data/derived/aggregate-summary.csv`
- Chart: `charts/exports/sample-content-category-share.svg`
- Status: `sample`
- Privacy note: fake demo data only.

This remains in the repo only to demonstrate schema and chart generation.

## Candidate Next Metrics

### Content Category Summary

Potential dataset:

- `data/derived/monthly-content-category-summary.csv`

Potential method:

- not approved yet. Requires a safe way to classify content without publishing titles, URLs, individual rows, or fine-grained timelines.

Risk level:

- medium to high. Do not implement until methodology is clearer.
