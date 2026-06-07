# Task: Replace Developer Jargon in 產業報告 (s_report)

## Problem

The `s_report` section (`buildReport()` in `build_full_dashboard.py`) contains terms that read
like internal developer/data-pipeline language rather than industry-audience language. The page is
intended for use in live briefings and should read like a professional industry report.

## Terms to replace throughout `buildReport()` and related story/chapter copy

| Current (developer) | Replace with |
|---|---|
| `snapshot` | 資料截點 (or just omit where obvious) |
| `proxy` / `proxy 指標` | 估算指標 / 間接估算 |
| `track-list` | 追蹤名單 |
| `DIR` / `DIR.channels` | (internal JS — OK in JS, but not in visible copy) |
| `ACT` | (same — internal only) |
| `record` (data type name) | 近期數據 |
| `basic-data` (data type name) | 基本資料 |
| `top-videos` (data type name) | 熱門影片資料 |
| `livestreams` (data type name) | 直播資料 |
| `p90` in user-facing copy | 前 10% 門檻 / 前段頻道 |
| `cohort` | 世代 / 出道屆 |
| `KM curve` / `Kaplan-Meier` | 存活曲線 |
| `series` (data field) | (internal — OK in JS) |
| `mom_3m` / `cagr_yr` in copy | 近 3 月動能 / 年化成長率 |
| `delta` in copy | 淨增長 |

## Specific locations to fix in `build_full_dashboard.py`

### `buildReport()` — chapter body text (~line 689)

The four chapter `p` texts (the last string in each chapter array) currently reference:
- "直播用雙棲象限圖" — fine
- "track-list" appears in chapter texts — replace with "追蹤名單"
- "proxy" appears in chapter 4 — replace with "估算"
- "snapshot" appears in story cards or chapter notes — replace

### Story cards (~line 688)

```js
const story = [
  ["追蹤台V", fmt(cur.tracked_channels), `近期活躍 ...`],
  ...
  ["開台尖峰", peakH + " 時", `這是開台時間，不是同接尖峰`],
```

The fifth story card caption `這是開台時間，不是同接尖峰` is already good.
Review all five card captions for any developer-sounding sub-text and rewrite for clarity.

### `buildReport()` — the `txt` array (~line 690)

The `txt` array generates the copyable report paragraphs. Check every entry for:
- `track-list` → 追蹤名單
- `snapshot` → 資料截點
- `proxy` → 估算
- Any parenthetical `(含倖存者偏差)` — keep as-is, this is a legitimate data caveat

### `buildConc()` insight text (~line 126)

```
頭部集中度（前 10 大訂閱佔比）由 2022Q1 的 44% 一路降到約 14%，同時訂閱中位數由 ~460 升到 ~1,450 → 長尾變厚、中段創作者整體墊高。
```

This is fine. Do not change.

### `buildGrowth()` section sub-tabs and insight

The `buildGrowth()` insight at line 172 reads:
> 所有 proxy 都保留限制說明

Replace `proxy` → `估算指標`

### Footer / disclaimer text

The disclaimer at the bottom of `s_report`:
```
黏著度、事件 delta、作息皆為 proxy 或取樣統計
```
Replace with: `黏著度、事件淨增長、作息皆為估算指標或取樣統計`

### `s_locate` section insight (~line 217)

The text `預設用內建最新 snapshot（__GEN__）` — replace `snapshot` with `資料截點`.

## Scope

Only fix **user-visible strings** — text inside HTML template literals that appear in the browser.
Do NOT change JS variable names, field names in JSON, Python variable names, or internal comments.

## Verification

1. `python build_full_dashboard.py` → no error, JS parse OK
2. Ctrl-F in the generated HTML for: `proxy`, `snapshot`, `track-list`, `p90`, `basic-data`,
   `record`, `top-videos`, `livestreams` in visible text. Each hit should be in a data-caveat
   context or removed/replaced.
3. The `s_report` page copy should read cleanly as industry language when opened in a browser.
