# d11_stitch Data Catalog

## Overview

- **Database**: `d11_stitch`
- **Account**: 078210713173 (aws-d11-prod)
- **Region**: us-east-1
- **Total Tables**: 6,954
- **AWS Profile**: `dream2o`

## Access Configuration

```bash
# AWS SSO Login
aws configure sso --profile dream2o
# SSO Start URL: https://d-906750de58.awsapps.com/start/#
# SSO Region: us-east-1
# Account: 078210713173

# Verify access
aws sts get-caller-identity --profile dream2o

# Query via Athena
export AWS_PROFILE=dream2o
```

## Table Categories

| Prefix | Count | Description |
|--------|-------|-------------|
| `user_` | 160 | User-level data |
| `temp_` | 156 | Temporary tables |
| `mm_` | 146 | Match metrics |
| `ext_` | 144 | External/extended data |
| `mec_` | 127 | MEC-related |
| `home_` | 125 | Home screen data |
| `new_` | 112 | New features/tables |
| `test_` | 109 | Test tables |
| `postrl_` | 100 | Post-round level |
| `ipl_` | 100 | IPL-specific |
| `daily_` | 88 | Daily aggregations |
| `rewards_` | 91 | Rewards system |

---

## Core Watch/Stream Tables

### `day_user_stream_watchtime`
User-level watch time by stream and hour. **Primary table for user watch analysis.**

| Column | Type | Description |
|--------|------|-------------|
| eventdate | timestamp | Date of viewing |
| userid | string | User ID |
| streamid | string | Stream ID |
| hour_of_day | timestamp | Hour bucket |
| watch_seconds | bigint | Seconds watched |

**Sample Query:**
```sql
SELECT 
    eventdate,
    COUNT(DISTINCT userid) as unique_users,
    SUM(watch_seconds) / 60 as watch_minutes
FROM d11_stitch.day_user_stream_watchtime
WHERE eventdate >= DATE '2026-02-01'
GROUP BY eventdate
ORDER BY eventdate;
```

### `day_hour_watchtime`
Aggregated watch time by day and hour. **Best for time-series trends.**

| Column | Type | Description |
|--------|------|-------------|
| eventdate | timestamp | Date |
| hour_of_day | timestamp | Hour bucket |
| watch_seconds | bigint | Total seconds watched |

### `livestream_creator`
**Rich creator performance table** with engagement, revenue, and viewer metrics.

| Column | Type | Description |
|--------|------|-------------|
| streamstarttime | timestamp | Stream start time |
| viewercount | bigint | Total views |
| uniqueviewers | bigint | Unique viewers |
| roundname | string | Match/round name |
| creatorname | string | Creator name |
| stream_hours | decimal(21,1) | Stream duration in hours |
| watch_hours | decimal(21,1) | Total watch hours |
| id | bigint | Stream ID |
| debit_customers | bigint | Users who spent DB |
| goal_debit_customers | bigint | Group goal payers |
| super_chat_debit_customers | bigint | Superchat payers |
| debit_amount | bigint | Total DreamBucks spent |
| group_goal_debit | bigint | DB spent on group goals |
| super_chat_debit | bigint | DB spent on superchats |
| normal_chats | bigint | Normal chat count |
| superchats | bigint | Superchat count |
| prediction | bigint | Prediction count |
| reaction | bigint | Reaction count |
| groupgoal | bigint | Group goal count |
| distinct_users_chats | bigint | Unique chatters |
| distinct_users_superchats | bigint | Unique superchatters |
| distinct_users_prediction | bigint | Unique predictors |
| distinct_users_reaction | bigint | Unique reactors |
| distinct_users_groupgoal | bigint | Unique goal participants |
| avgconcurrentviewers | bigint | Avg concurrent viewers |
| maxconcurrentviewers | bigint | Peak concurrent viewers |
| paid_users | bigint | Users who paid |
| engaged_users | bigint | Users who engaged |

**Sample Query - Top Creators:**
```sql
SELECT 
    creatorname,
    SUM(debit_amount) as total_debit_spent,
    SUM(watch_hours) as total_watch_hours,
    COUNT(DISTINCT id) as total_streams,
    SUM(paid_users) as total_paid_users
FROM d11_stitch.livestream_creator
WHERE creatorname IS NOT NULL
GROUP BY creatorname
ORDER BY total_debit_spent DESC
LIMIT 10;
```

### `livestream_watch_time`
Stream-level watch time by hour.

| Column | Type | Description |
|--------|------|-------------|
| streamid | string | Stream ID |
| hour | int | Hour of day |
| watch_seconds | bigint | Total seconds |

### `ls_user_stream_date`
Alternative user-stream watch time table.

| Column | Type | Description |
|--------|------|-------------|
| eventdate | date | Date |
| userid | string | User ID |
| streamid | string | Stream ID |
| hour | int | Hour |
| watch_seconds | bigint | Seconds watched |

### `sportan_livestream_watchtime`
SPORTAN (internal) users watch time - for exclusion in public metrics.

| Column | Type | Description |
|--------|------|-------------|
| eventdate | timestamp | Date |
| userid | string | User ID |
| streamid | string | Stream ID |
| hour_of_day | timestamp | Hour bucket |
| watch_seconds | bigint | Seconds watched |

---

## Watch Party Tables

### `user_watch_party_time_spent_daily`
**User-level granular watch party data.** Use this for user-specific analysis.

| Column | Type | Description |
|--------|------|-------------|
| event_date | date | Date of watch party |
| userid | string | User ID |
| topic_id | string | Topic/match ID |
| room_id | string | Watch party room ID |
| watch_party_ts | bigint | Time spent (seconds, raw) |
| adjusted_watch_party_ts | bigint | Adjusted time spent (seconds) |
| percentile_value | double | User's percentile ranking |

**Location**: `s3://d11-data-stitch/prod/user_watch_party_time_spent_daily`

**Sample Query - User Time Spent:**
```sql
SELECT 
    userid,
    SUM(watch_party_ts) as total_time_spent,
    COUNT(DISTINCT topic_id) as topics_joined
FROM d11_stitch.user_watch_party_time_spent_daily
WHERE event_date >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY userid
ORDER BY total_time_spent DESC
LIMIT 100;
```

### `watch_party_time_spent_daily_summary`
**Daily aggregated watch party metrics with percentile distributions.** Use this for trend analysis.

| Column | Type | Description |
|--------|------|-------------|
| event_date | date | Date |
| total_watch_party_ts | bigint | Total time spent (all users, seconds) |
| total_users | bigint | User count |
| avg_watch_party_ts | double | Average time per user (seconds) |
| tf_watch_party_ts | bigint | **TF**: Lower percentile threshold (seconds) |
| med_watch_party_ts | bigint | **Median**: 50th percentile (seconds) |
| sf_watch_party_ts | bigint | **SF**: Mid-lower percentile (seconds) |
| nt_watch_party_ts | bigint | **NT**: 90th percentile / Upper (seconds) |
| nn_watch_party_ts | bigint | **NN**: 99th percentile / Top users (seconds) |
| avg_user_topic_ts | double | Avg time per user per topic |
| total_topics | bigint | Total topics/matches |
| avg_topics | double | Avg topics per user |
| med_topics | bigint | Median topics per user |
| avg_rooms | double | Avg rooms per user |
| med_rooms | bigint | Median rooms per user |

#### Percentile Metric Definitions

| Metric | Column | Description |
|--------|--------|-------------|
| **TF** | `tf_watch_party_ts` | Top Floor - Lower percentile threshold |
| **Median** | `med_watch_party_ts` | 50th percentile (typical user) |
| **SF** | `sf_watch_party_ts` | Second Floor - Mid-lower percentile |
| **NT** | `nt_watch_party_ts` | Ninety - 90th percentile (engaged users) |
| **NN** | `nn_watch_party_ts` | Ninety-Nine - 99th percentile (power users) |

**Sample Query - Daily Trends:**
```sql
SELECT 
    event_date,
    total_users,
    ROUND(avg_watch_party_ts / 60, 1) as avg_minutes,
    ROUND(med_watch_party_ts / 60, 1) as median_minutes,
    ROUND(nt_watch_party_ts / 60, 1) as p90_minutes,
    ROUND(nn_watch_party_ts / 60, 1) as p99_minutes
FROM d11_stitch.watch_party_time_spent_daily_summary
WHERE event_date >= CURRENT_DATE - INTERVAL '7' DAY
ORDER BY event_date DESC;
```

**Key Insight**: On high-volume days (100K+ users), median stays ~25-30 seconds while NN (top 1%) reaches 7-10 minutes. On low-volume days, power users can spend 2+ hours (NN > 150 minutes).

#### How `watch_party_time_spent_daily_summary` is built

The summary is derived from `user_watch_party_time_spent_daily`. Aggregation flow:

1. **Innermost**: Per user, per topic, per day — sum `adjusted_watch_party_ts` and count distinct `room_id`.
2. **Middle**: Per user, per day — sum topic-level time, count distinct topics, avg rooms.
3. **Outer**: Per day — aggregate across users: totals, counts, and **APPROX_PERCENTILE** for TF/med/SF/NT/NN.

Percentile columns map to these quantiles:

| Column | APPROX_PERCENTILE(..., q) | Quantile |
|--------|---------------------------|----------|
| tf_watch_party_ts | 0.25 | 25th percentile |
| med_watch_party_ts | 0.5 | 50th (median) |
| sf_watch_party_ts | 0.75 | 75th percentile |
| nt_watch_party_ts | 0.9 | 90th percentile |
| nn_watch_party_ts | 0.99 | 99th percentile |

**Source query (creation logic):**
```sql
SELECT
  event_date,
  SUM(total_user_topic_ts) AS total_watch_party_ts,
  COUNT(DISTINCT userid) AS total_users,
  AVG(total_user_topic_ts) AS avg_watch_party_ts,
  APPROX_PERCENTILE(total_user_topic_ts, 0.25) AS tf_watch_party_ts,
  APPROX_PERCENTILE(total_user_topic_ts, 0.5)  AS med_watch_party_ts,
  APPROX_PERCENTILE(total_user_topic_ts, 0.75) AS sf_watch_party_ts,
  APPROX_PERCENTILE(total_user_topic_ts, 0.9)  AS nt_watch_party_ts,
  APPROX_PERCENTILE(total_user_topic_ts, 0.99) AS nn_watch_party_ts,
  AVG(avg_user_topic_ts) AS avg_user_topic_ts,
  SUM(topics) AS total_topics,
  AVG(topics) AS avg_topics,
  APPROX_PERCENTILE(topics, 0.5) AS med_topics,
  AVG(total_rooms) AS avg_rooms,
  APPROX_PERCENTILE(total_rooms, 0.5) AS med_rooms
FROM
(
  SELECT
    event_date,
    userid,
    SUM(user_topic_daily_ts) AS total_user_topic_ts,
    AVG(user_topic_daily_ts) AS avg_user_topic_ts,
    AVG(avg_user_room_ts) AS avg_user_room_ts,
    COUNT(DISTINCT topic_id) AS topics,
    AVG(rooms) AS avg_rooms,
    SUM(rooms) AS total_rooms
  FROM
  (
    SELECT
      event_date,
      userid,
      topic_id,
      SUM(adjusted_watch_party_ts) AS user_topic_daily_ts,
      AVG(adjusted_watch_party_ts) AS avg_user_room_ts,
      COUNT(DISTINCT room_id) AS rooms
    FROM d11_stitch.user_watch_party_time_spent_daily
    GROUP BY 1, 2, 3
  )
  GROUP BY 1, 2
)
GROUP BY 1;
```

### `watch_party_user_reactions`
User-level watch party reaction data.

| Column | Type | Description |
|--------|------|-------------|
| event_date | date | Date |
| userid | string | User ID |
| topic_id | string | Topic ID |
| watch_party_name | string | Party name |
| wp_type | string | Party type (public/private) |
| db_type | string | DreamBucks type |
| total_db_spent | double | DB spent |
| reaction_sent | bigint | Reactions sent |

### `watch_party_overlap_dialy_summary`
User overlap between watch party and other features.

| Column | Type | Description |
|--------|------|-------------|
| event_date | date | Date |
| app_openers | bigint | App openers |
| livestream_users | bigint | Livestream users |
| moments_users | bigint | Moments users |
| livestream_moments_users | bigint | Users in both livestream & moments |
| cj_users | bigint | CJ users |
| wp_users | bigint | Watch party users |
| wp_hpl_overlap | bigint | WP + HPL overlap |
| wp_livestream_overlap | bigint | WP + Livestream overlap |
| wp_moments_overlap | bigint | WP + Moments overlap |
| wp_livstream_moments_overlap | bigint | WP + Livestream + Moments |
| wp_fantasy_overlap | bigint | WP + Fantasy overlap |

### `watch_party_user_funnel`
Watch party funnel metrics by event.

| Column | Type | Description |
|--------|------|-------------|
| event_date | date | Date |
| eventname | string | Funnel event name |
| overall_users | bigint | Total users |
| overall_hits | bigint | Total hits |
| public_users | bigint | Public party users |
| public_hits | bigint | Public party hits |
| private_users | bigint | Private party users |
| private_hits | bigint | Private party hits |

### `watch_party_reaction_summary`
Daily reaction summary by party type.

| Column | Type | Description |
|--------|------|-------------|
| event_date | date | Date |
| wp_type | string | Party type |
| db_type | string | DB type |
| total_db_spent | double | Total DB spent |
| total_reaction_sent | bigint | Total reactions |
| reactions_users | bigint | Users who reacted |

---

## Retention Tables

All retention tables follow a cohort-based structure:

### Standard Retention Schema
| Column | Type | Description |
|--------|------|-------------|
| week_start / join_week | date/timestamp | Cohort week |
| feature | string | Feature name |
| feature_users | bigint | Users in cohort |
| w1_users | bigint | Week 1 retained |
| w2_users | bigint | Week 2 retained |
| w3_users | bigint | Week 3 retained |
| w4_users | bigint | Week 4 retained |
| w1_retn | decimal | Week 1 retention % |
| w2_retn | decimal | Week 2 retention % |
| w3_retn | decimal | Week 3 retention % |
| w4_retn | decimal | Week 4 retention % |

**Retention Tables:**
- `retention_daulivestream` - Daily livestream retention
- `retention_watchalongweeklyh` - Weekly watch-along retention
- `retention_watchtimeusers` - Watch time retention
- `stream_retn` - Stream feature retention
- `auto_option_stream_retn` - Auto option retention
- `profile_icon_stream_retn` - Profile icon retention
- `scorecard_stream_retn` - Scorecard retention
- `scrubber_stream_retn` - Scrubber retention
- `share_icon_stream_retn` - Share icon retention

---

## Moment Tables

### `moment_raw`
Daily moments uploaded.

| Column | Type | Description |
|--------|------|-------------|
| day_ist | date | Date (IST) |
| new_moments_daily | bigint | New moments |
| new_duration_sec_daily | double | Duration (seconds) |

### `moment_interaction`
User interactions with moments.

### `timespentonmoment`
Time spent on moments by hour.

| Column | Type | Description |
|--------|------|-------------|
| day_ist | timestamp | Date (IST) |
| hour_bucket | timestamp | Hour bucket |
| total_watch_min_cum | double | Cumulative watch minutes |

---

## Weekly MIS Tables

### `weekly_mis_watchalong`
Weekly watch-along summary.

| Column | Type | Description |
|--------|------|-------------|
| week | date | Week start |
| users | bigint | User count |
| watch_minute | decimal | Total minutes |
| watch_minute_per_user | decimal | Avg min/user |
| p50_watch_minutes | float | Median |
| p75_watch_minutes | float | 75th percentile |
| p90_watch_minutes | float | 90th percentile |

### `weekly_mis_stream_coverage`
Weekly stream coverage metrics.

| Column | Type | Description |
|--------|------|-------------|
| week | date | Week start |
| weekly_day_avg_streams | double | Avg daily streams |
| weekly_day_avg_coverage | decimal | Avg coverage |
| stream_minute | bigint | Total stream minutes |
| total_streams | bigint | Stream count |
| weekly_active_creator | bigint | Active creators |

---

## Key Metrics (as of Feb 2026)

### Total Watch Time
- **Total Watch Minutes**: 54.92 Million
- **Total Watch Hours**: 915,341
- **Total Watch Years**: ~104 years equivalent
- **Unique Users**: 7.5 Million
- **Data Range**: Dec 4, 2025 - Feb 19, 2026

### Top 5 Creators (by Total Debit Spent)
| Rank | Creator | Total DB | Streams | Watch Hours |
|------|---------|----------|---------|-------------|
| 1 | 13ishancriccrak | 5,566,000 | 76 | 111,714 |
| 2 | SPORTS YAARI | 5,064,460 | 93 | 73,501 |
| 3 | Ranjesh | 4,168,720 | 70 | 31,944 |
| 4 | Ravs1007 | 3,742,950 | 66 | 49,374 |
| 5 | AB CRIC INFO | 3,571,450 | 21 | 101,753 |

---

## Common Query Patterns

### Total Watch Minutes
```sql
SELECT 
    SUM(watch_seconds) / 60 as total_watch_minutes,
    COUNT(DISTINCT userid) as unique_users
FROM d11_stitch.day_user_stream_watchtime;
```

### Daily Trends
```sql
SELECT 
    DATE(eventdate) as day,
    SUM(watch_seconds) / 60 as watch_minutes,
    COUNT(DISTINCT userid) as users
FROM d11_stitch.day_user_stream_watchtime
GROUP BY DATE(eventdate)
ORDER BY day DESC;
```

### Creator Performance
```sql
SELECT 
    creatorname,
    SUM(debit_amount) as total_debit,
    SUM(watch_hours) as total_watch_hours,
    SUM(uniqueviewers) as total_viewers,
    COUNT(DISTINCT id) as streams
FROM d11_stitch.livestream_creator
GROUP BY creatorname
ORDER BY total_debit DESC
LIMIT 20;
```

### User Watch Time Distribution
```sql
SELECT 
    userid,
    SUM(watch_seconds) / 60 as watch_minutes
FROM d11_stitch.day_user_stream_watchtime
WHERE eventdate >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY userid
ORDER BY watch_minutes DESC
LIMIT 100;
```

---

## Related Databases

| Database | Account | Region | Description |
|----------|---------|--------|-------------|
| `d11_stitch` | 078210713173 | us-east-1 | Main data warehouse |
| `d11_stitch_plus` | 078210713173 | us-east-1 | Extended stitch data |
| `d11_home_personalisation` | 944380855954 | us-east-1 | Home personalization |
| `ds_stitch` | 078210713173 | us-east-1 | Data science stitch |
| `fc_stitch` | 078210713173 | us-east-1 | FC stitch data |

---

## Notes

1. **IST vs UTC**: Most metrics are in IST. Convert using `+ INTERVAL '330' MINUTE` or `AT TIME ZONE 'Asia/Kolkata'`

2. **SPORTAN Users**: Internal/test users. Exclude using `sportan_userid_new` or `sportan_livestream_watchtime`

3. **Grain**: 
   - Day-level tables: `eventdate`, `day_ist`
   - Hour-level tables: `hour_of_day`, `hour_bucket`
   - User-level tables: Include `userid` column

4. **DreamBucks (DB)**: Virtual currency. `debit_amount` = DB spent by users

5. **Data Freshness**: Tables typically updated daily, check `MAX(eventdate)` for latest data

---

*Last updated: February 2026*
