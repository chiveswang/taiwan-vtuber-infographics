# Derived Data

此資料夾只放可公開的衍生資料與聚合資料。

不要放入：

- 原始 tracking data。
- 個別 VTuber 的完整活動時間序列。
- 未經 privacy review 的資料。
- 私人資訊或身份推測。

建議每份資料都包含：

- source_url 或來源說明。
- last_verified。
- aggregate_period。
- methodology note。

## Activity Dashboard Aggregate Imports

以下資料來自既有 `activity/vtuber_activity_dashboard.html` 的白名單聚合欄位：

- `activity-quarterly-summary.csv`
- `cohort-quarterly-summary.csv`

公開匯入會抑制小於 10 的創作者計數 cell，並把 cohort 的所有已結算季度合併成單一桶。內容項目數與精確最大觀看值不公開，因為它們不能證明至少 10 位不同貢獻者，且可能暴露離群值。不得加入頻道名稱、Channel ID、影片標題、直播網址、排行名單、個人搜尋結果或任何可回推個人的細粒度時間序列。
