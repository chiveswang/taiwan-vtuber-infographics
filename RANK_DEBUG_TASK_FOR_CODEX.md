# Task: Debug and Fix 排行榜 (s_rank)

## Problem

The rank leaderboard section (`s_rank`) in `build_full_dashboard.py` is reportedly non-functional.
Investigate and fix all rendering bugs so every board chip shows a populated horizontal bar chart
and table on first click.

## Diagnosis steps

### Step 1 — confirm key alignment

The rank `render()` function filters channels with `c.id`:

```js
const rows = DIRDATA.channels.filter(c => c.id && pass(c))
  .map(c => ({ c, v: b[2](c), e: bestEvent(c.id) }))
  .filter(x => x.v != null && isFinite(x.v))
```

`DIRDATA` comes from `locate_directory.json`; the `id` field there is the VTuber ID string
(the `t["ID"]` from `TW_VTUBER_TRACK_LIST.csv`, e.g. `"UCxxxxxxxxxx"`).

Several board score functions look up `GROW.channels[c.id]`, `EVT.channels[c.id]`,
`XPLAT.channels[c.id]`. Confirm the keys in those JSON files are also the same VTuber ID format
by inspecting a sample key from each:

```python
import json
from pathlib import Path
ACT = Path("outputs/activity")
grow = json.loads((ACT/"growth.json").read_text(encoding="utf-8"))
evt  = json.loads((ACT/"events.json").read_text(encoding="utf-8"))
xp   = json.loads((ACT/"crossplatform.json").read_text(encoding="utf-8"))
print("GROW sample keys:", list(grow["channels"].keys())[:5])
print("EVT  sample keys:", list(evt["channels"].keys())[:5])
print("XPLAT sample keys:", list(xp["channels"].keys())[:5])
d = json.loads((ACT/"locate_directory.json").read_text(encoding="utf-8"))
print("DIR  sample ids:", [c["id"] for c in d["channels"][:5]])
```

If the key formats differ (e.g. GROW uses YouTube channel ID `UCxxxx` while DIR uses VTuber ID),
add a mapping layer — derive it from the track-list where both IDs co-exist — and patch the
relevant board score functions so they look up by the correct key.

### Step 2 — fix the canvas reference after innerHTML

In `render()`:

```js
rankList.innerHTML = `...<canvas id="rankBar"></canvas>...`;
store.rankBar = new Chart(rankBar, {...});   // ← bare global reference
```

After a dynamic `innerHTML` assignment the element is in the DOM but `window.rankBar` may not
be refreshed in all execution contexts. Replace the bare `rankBar` reference with an explicit
lookup everywhere it appears in `buildRank`:

```js
store.rankBar = new Chart(document.getElementById("rankBar"), {...});
```

### Step 3 — validate basic subs board end-to-end

After the above fixes, confirm the default "訂閱 Top" board renders a horizontal bar chart with
at least 15 rows and the table is populated. Do this by opening the generated HTML in a browser
(or use the js-parse-check approach from the worklog) and verifying no console errors.

### Step 4 — guard against empty rows

If `rows.length === 0` after filtering, `rankList.innerHTML` currently still tries to insert a
`<canvas>` and call `new Chart(...)` with empty data. Add an early return with a note:

```js
if (!rows.length) {
  rankList.innerHTML = '<div class="note">此榜目前沒有符合篩選條件的頻道。</div>';
  return;
}
```

Place this check right after `rows` is computed and before the canvas insertion.

## Boards that intentionally show a note

`["tv","熱門影片 Top",...,"待資料"]` is intentionally disabled via the `startsWith("待")` guard —
**leave it as-is**.

The `"dual"` (雙棲最強) board should now work if XPLAT key alignment is confirmed in Step 1.

## Files to modify

- `build_full_dashboard.py` — `buildRank()` function (~lines 635–659)
- Possibly `build_longitudinal.py` or `build_locate_directory.py` if a key-mapping fix
  is needed at data generation time (preferred over a JS patch)

## Verification

After changes:
1. `python build_full_dashboard.py` → no error
2. JavaScript parse check passes
3. Open dashboard, click "排行榜" → bar chart and table render for "訂閱 Top", "總觀看 Top",
   "Twitch 追隨 Top", "最黏", "爆紅力" without console errors
4. Chips for "最規律開台" and "成長最快" produce either results or an appropriate empty-row note
