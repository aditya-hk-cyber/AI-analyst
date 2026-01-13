-- raw sql results do not include filled-in values for 'total_watch_time.eventdate_date'


WITH total_watch_time AS (with s1 as(select cast(eventdate as timestamp) eventdate,sum(watch_seconds)*1.0000/60.00 as watch_minutes
            from d11_stitch.day_hour_watchtime
            where date(eventdate)>=date('2025-12-04')
            group by eventdate),
      s2 as(SELECT
                total_watch_min_cum,cast(day_ist as timestamp) day_ist
            FROM (
                SELECT
                    day_ist,
                    hour_bucket,
                    total_watch_min_cum,
                    row_number() OVER (
                        PARTITION BY day_ist
                        ORDER BY hour_bucket DESC
                    ) AS rn
                FROM d11_stitch.timespentonmoment
                where date(day_ist)>=date('2025-12-04')
            ) t
            WHERE rn = 1)
      select s1.watch_minutes,s2.total_watch_min_cum,(s1.watch_minutes+s2.total_watch_min_cum) total_watch_mins,cast(s1.eventdate as timestamp) eventdate
      from s1 left join s2 on
      s1.eventdate = s2.day_ist )
SELECT
    (DATE_FORMAT((total_watch_time.eventdate  AT TIME ZONE 'Asia/Kolkata'), '%Y-%m-%d')) AS "total_watch_time.eventdate_date",
    COALESCE(SUM(CAST( total_watch_time.total_watch_mins   AS DOUBLE)), 0) AS "total_watch_minutes",
    COALESCE(SUM(CAST( total_watch_time.watch_minutes   AS DOUBLE)), 0) AS "watch_minutes_watch_along",
    COALESCE(SUM(CAST( total_watch_time.total_watch_min_cum   AS DOUBLE)), 0) AS "moments_watchtime"
FROM total_watch_time
WHERE (total_watch_time.eventdate ) >= ((CAST(CAST((FORMAT_DATETIME(DATE_ADD('day', -7, CAST(CAST(DATE_TRUNC('DAY', (NOW() AT TIME ZONE 'Asia/Kolkata')) AS DATE) AS TIMESTAMP)), 'yyyy-MM-dd HH:mm:ss.SSS') || ' Asia/Kolkata') AS TIMESTAMP WITH TIME ZONE) AT TIME ZONE 'UTC' AS TIMESTAMP)))
GROUP BY
    1
ORDER BY
    1 DESC
LIMIT 500