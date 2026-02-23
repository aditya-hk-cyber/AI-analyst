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

### `watch_party_time_spent_daily_summary`
Daily aggregated watch party metrics.

| Column | Type | Description |
|--------|------|-------------|
| event_date | date | Date |
| total_watch_party_ts | bigint | Total time spent |
| total_users | bigint | User count |
| avg_watch_party_ts | double | Avg time per user |
| tf_watch_party_ts | bigint | Top percentile |
| med_watch_party_ts | bigint | Median |
| total_topics | bigint | Topic count |
| avg_topics | double | Avg topics/user |

### `watch_party_user_reactions`
User-level watch party reaction data.

| Column | Type | Description |
|--------|------|-------------|
| event_date | date | Date |
| userid | string | User ID |
| topic_id | string | Topic ID |
| watch_party_name | string | Party name |
| wp_type | string | Party type |
| db_type | string | DB type |
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
| wp_users | bigint | Watch party users |
| wp_livestream_overlap | bigint | WP + Livestream |
| wp_fantasy_overlap | bigint | WP + Fantasy |

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
