# Task: Show Located Channel Info in 開台作息 Sub-tab

## Problem

In `buildGrowth()` → `renderSched()`, the three charts (`gwHour`, `gwWeek`, `gwMonth`) include
datasets for the selected channel:

```js
{ label: "此頻道 YT%",  data: ytc ? pctArr(ytc.hours)   : [], ... }
{ label: "此頻道 Twitch%", data: twc ? pctArr(twc.hours) : [], ... }
```

`ytc = yt.channels[gwChannel.id]` — if the channel's ID doesn't match the key format in
`STM.yt.channels`, or if the channel has fewer streams than the minimum sample threshold,
`ytc` is `null` and the dataset is silently empty.

Additionally, the `gw_sched` sub-tab and the `s_locate` (定位你自己) section use **separate**
channel selection state (`gwChannel` vs `curChannel`). If a user locates a channel in s_locate
and then navigates to 成長與生命週期 → 開台作息, they have to re-enter the channel name in the
growth search bar.

## Required fixes

### Fix 1 — Explicit "no data" message when channel is selected but has no stream records

In `renderSched()`, after computing `ytc` and `twc`, add a visible note when the user has
selected a channel but neither `ytc` nor `twc` is available:

```js
const noStreamData = gwChannel && gwChannel.id && !ytc && !twc;
```

Insert a note above the charts (inside the `gw_sched` panel HTML) when `noStreamData` is true:

```html
<div class="note">
  「${escHtml(gwChannel.n || gwChannel.id)}」在直播作息資料中無足夠取樣（至少需 5 場），
  下方圖表僅顯示產業整體分布。
</div>
```

When `ytc` is not null but `ytc.n_streams` is very small (< 5), it was filtered at build time —
so the above null check is sufficient; no further threshold check needed in JS.

### Fix 2 — Sync channel from s_locate to growth section on tab switch

When the user clicks a channel link in `s_rank` (via `jumpLocate()`), it already sets both
`curChannel` and navigates to s_locate. Do the inverse: when `gwFind` or the growth section
detects the user navigated there with `curChannel` already set but `gwChannel` is null, pre-fill
the growth channel.

Add this at the **top of `buildGrowth()`** (before `show("gw_traj")`) and also at the top of
the `renderSched()` function — if `gwChannel` is null but `curChannel` is set, use `curChannel`:

```js
// in buildGrowth(), before show("gw_traj"):
if (!gwChannel && curChannel) {
  gwChannel = curChannel;
  const q = document.getElementById("gwQ");
  const st = document.getElementById("gwStatus");
  if (q) q.value = gwChannel.n || gwChannel.t || "";
  if (st) st.textContent = `已套用：${gwChannel.n || gwChannel.t || "未命名頻道"}`;
}
```

This means: the first time the user opens 成長與生命週期, if they already located a channel in
s_locate, that channel is automatically carried over.

**Do not** auto-sync in subsequent re-renders (`rebuildAll`) — only on first build (`!built[id]`
gate already handles this since `buildGrowth` is only called once).

### Fix 3 — Confirm key format alignment for STM channels

In `build_longitudinal.py`, the key used for `streaming.json` channels dict should be the same
VTuber ID as used in `locate_directory.json`. Inspect:

```python
import json
from pathlib import Path
stm = json.loads((Path("outputs/activity")/"streaming.json").read_text(encoding="utf-8"))
print("STM YT sample keys:", list(stm["yt"]["channels"].keys())[:5])
```

If the keys are YouTube channel IDs (`UCxxxx`) rather than VTuber IDs, and `locate_directory.json`
uses VTuber IDs as `c.id`, add a `yt_id_to_vid` lookup in `build_full_dashboard.py`:

```js
// build a map from YouTube channel ID → channel object
const ytIdMap = Object.fromEntries(
  DIRDATA.channels.filter(c => c.y).map(c => [c.y, c])
);
```

Then in `locStream()`:

```js
function locStream(o) {
  if (!o) return null;
  // try VTuber ID first, then YouTube channel ID
  return STM.yt.channels[o.id] || (o.y ? STM.yt.channels[o.y] : null);
}
```

Apply the same dual-lookup in `renderSched()` for `ytc` and `twc`.

## Verification

1. `python build_full_dashboard.py` → no error, JS parse OK
2. Open dashboard → 定位你自己 → find a channel with known streaming activity → click 定位
3. Switch to 成長與生命週期 → the channel name should pre-fill in the search box
4. Click 開台作息 tab:
   - If channel has stream data: `gwHour` and `gwWeek` show both industry and channel-specific bars
   - If channel has no stream data: a clear note explains this; industry-only bars shown
5. Test with a channel that has no Twitch presence — only YT dataset should appear (Twitch dataset empty is acceptable, no console error)
