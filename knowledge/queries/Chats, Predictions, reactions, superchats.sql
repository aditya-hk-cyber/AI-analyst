WITH daylevel_metrics AS (select * from d11_stitch.daylevel_metric )
  ,  cjusers AS (select * from d11_stitch.cjusers )
  ,  engaged_paid AS (select * from d11_stitch.daylevel_engagedpaid )
SELECT
    (DATE_FORMAT((daylevel_metrics.eventdate  AT TIME ZONE 'Asia/Kolkata'), '%Y-%m-%d')) AS "daylevel_metrics.eventdate_date",
    daylevel_metrics.dau  AS "daylevel_metrics.dau",
    COALESCE(SUM(CAST( daylevel_metrics.dau   AS DOUBLE)), 0) AS "dau",
    COALESCE(SUM(CAST( daylevel_metrics.livestream_dau   AS DOUBLE)), 0) AS "dau_watch_along",
    COALESCE(SUM(CAST( daylevel_metrics.moment_dau   AS DOUBLE)), 0) AS "dau_moments",
    COALESCE(SUM(CAST( daylevel_metrics.fantasy_dau   AS DOUBLE)), 0) AS "dau_fantasy",
    COALESCE(SUM(CAST( daylevel_metrics.total_watch_min_cum   AS DOUBLE)), 0) AS "time_spent_on_moment_in_mins",
    COALESCE(SUM(CAST( daylevel_metrics.watch_minutes   AS DOUBLE)), 0) AS "watch_minutes_watch_along",
    COALESCE(SUM(CAST( daylevel_metrics.distinct_streams   AS DOUBLE)), 0) AS "total_streams",
    COALESCE(SUM(CAST( daylevel_metrics.distinct_creators   AS DOUBLE)), 0) AS "total_creators",
    COALESCE(SUM(CAST( daylevel_metrics.total_stream_minutes   AS DOUBLE)), 0) AS "total_stream_minutes",
    COALESCE(SUM(CAST( daylevel_metrics.public_db_spent   AS DOUBLE)), 0) AS "db_spent",
    COALESCE(SUM(CAST( daylevel_metrics.db_purchased   AS DOUBLE)), 0) AS "db_purchased",
    COALESCE(SUM(CAST( daylevel_metrics.public_users   AS DOUBLE)), 0) AS "users_db_spent",
    COALESCE(SUM(CAST( daylevel_metrics.customers   AS DOUBLE)), 0) AS "users_db_purchased",
    COALESCE(SUM(CAST( daylevel_metrics.normal_chats   AS DOUBLE)), 0) AS "total_chats",
    COALESCE(SUM(CAST( daylevel_metrics.reaction   AS DOUBLE)), 0) AS "total_reactions",
    COALESCE(SUM(CAST( daylevel_metrics.prediction   AS DOUBLE)), 0) AS "total_prediction_participation",
    COALESCE(SUM(CAST( daylevel_metrics.superchats   AS DOUBLE)), 0) AS "total_superchats",
    COALESCE(SUM(CAST( daylevel_metrics.groupgoal   AS DOUBLE)), 0) AS "total_groupgoal_participation",
    COALESCE(SUM(CAST( cjusers.users   AS DOUBLE)), 0) AS "cj_users",
    COALESCE(SUM(CAST( engaged_paid.engaged_users   AS DOUBLE)), 0) AS "engaged_users",
    COALESCE(SUM(CAST( engaged_paid.paid_users   AS DOUBLE)), 0) AS "paid_users"
FROM daylevel_metrics
INNER JOIN cjusers ON (DATE_FORMAT((daylevel_metrics.eventdate  AT TIME ZONE 'Asia/Kolkata'), '%Y-%m-%d')) = (DATE_FORMAT((cjusers.eventdate  AT TIME ZONE 'Asia/Kolkata'), '%Y-%m-%d'))
INNER JOIN engaged_paid ON (DATE_FORMAT((daylevel_metrics.eventdate  AT TIME ZONE 'Asia/Kolkata'), '%Y-%m-%d')) = (DATE_FORMAT((engaged_paid.day_ist  AT TIME ZONE 'Asia/Kolkata'), '%Y-%m-%d'))
WHERE (daylevel_metrics.eventdate ) >= ((CAST(CAST((FORMAT_DATETIME(DATE_ADD('day', -7, CAST(CAST(DATE_TRUNC('DAY', (NOW() AT TIME ZONE 'Asia/Kolkata')) AS DATE) AS TIMESTAMP)), 'yyyy-MM-dd HH:mm:ss.SSS') || ' Asia/Kolkata') AS TIMESTAMP WITH TIME ZONE) AT TIME ZONE 'UTC' AS TIMESTAMP)))
GROUP BY
    1,
    2
ORDER BY
    5
LIMIT 500