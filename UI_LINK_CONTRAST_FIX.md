# 工單：連結在深色底的對比修正

## 問題
事件吸粉（`gw_event`）選定頻道的事件清單、以及其他卡片內的連結，使用瀏覽器預設連結色——未點擊為深藍 `#0000EE`、點過為深紫——在深灰底（`--panel #181b24`）上看不清楚。

## 修正（`build_full_dashboard.py` 的 `<style>` 加全域規則）
```css
a, a:link, a:visited { color: var(--blue); text-decoration: none; }
a:hover { color: #7cc4ff; text-decoration: underline; }
```
- `--blue` = `#4aa8ff`，深底上清晰；`:visited` 一併指定，避免點過變深紫。
- 全域套用即可一次解決事件清單、FAQ、最熱影片/直播連結等所有連結。

## 驗收
- [ ] 事件清單連結未點擊/點擊後皆為亮藍、清楚可讀。
- [ ] hover 有底線回饋。
