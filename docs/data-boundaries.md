# Data Boundaries

## 允許欄位

- public_name
- public_group_name
- public_platform
- public_url
- source_url
- last_verified
- content_category
- public_status_category
- aggregate_period
- aggregate_count
- notes_for_methodology

## 禁止欄位

- real_name
- home_address
- school
- workplace
- private_email
- phone_number
- private_account
- offline_identity_guess
- identity_actor_guess
- private_relationship
- exact_birthdate
- real_time_status
- raw_activity_timestamp
- individual_sensitive_time_series

## 需聚合後才能發布的欄位

- activity_frequency
- stream_frequency
- upload_frequency
- follower_or_subscriber_growth
- view_count_trends
- collaboration_network
- active_time_distribution
- debut_or_graduation_trends
- content_category_distribution

## 聚合建議

- 時間粒度以 month、quarter、year 為優先。
- 類別樣本太小時應合併或不發布。
- 不發布可直接比較個人的敏感排名。
- 不發布可反推個人生活節奏的細節。

## 優先公開資訊產品

- source coverage summary。
- platform coverage summary。
- monthly content category summary。
- quarterly ecosystem summary。

## 不做的資訊產品

- 個人排行榜。
- 個人活躍時間分析。
- 個人訂閱數或觀看數成長曲線。
- 個人合作網絡圖。
- 即時追蹤 dashboard。
