-- raw sql results do not include filled-in values for 'stream_day_level_details.day_ist_date'


WITH stream_day_level_details AS (WITH base AS (
          SELECT
              -- Convert UTC → IST
              streamstarttime + INTERVAL '330' MINUTE AS start_ist,
              streamendtime   + INTERVAL '330' MINUTE AS end_ist,
              id
          FROM d11_transactions.live_streaming_stream
          WHERE streamstatus = 'COMPLETED'
            AND streamstarttime IS NOT NULL
            AND streamendtime   IS NOT NULL
            and cast(influencerid as varchar) not in (select cast(id as varchar) from d11_transactions.dream11_userregistration where usertype = 'SPORTAN')
      ),
      per_day_streams AS (
          SELECT
              b.id,
              CAST(d AS DATE) AS day_ist,
              GREATEST(b.start_ist, d)                 AS day_start,
              LEAST(b.end_ist, d + INTERVAL '1' DAY)   AS day_end
          FROM base b
          CROSS JOIN UNNEST (
              SEQUENCE(
                  date_trunc('day', b.start_ist),
                  date_trunc('day', b.end_ist),
                  INTERVAL '1' DAY
              )
          ) AS t(d)
          WHERE b.end_ist   > d
            AND b.start_ist < d + INTERVAL '1' DAY
      ),
      daily_total AS (
          SELECT
              day_ist,
              SUM(date_diff('second', day_start, day_end)) AS total_stream_seconds
          FROM per_day_streams
          GROUP BY day_ist
      ),
      events AS (
          SELECT
              day_ist,
              day_start AS ts,
              1 AS delta
          FROM per_day_streams

          UNION ALL

          SELECT
              day_ist,
              day_end AS ts,
              -1 AS delta
          FROM per_day_streams
      ),
      events_with_active AS (
          SELECT
              day_ist,
              ts,
              SUM(delta) OVER (
                  PARTITION BY day_ist
                  ORDER BY ts
                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
              ) AS active_streams,
              LEAD(ts) OVER (
                  PARTITION BY day_ist
                  ORDER BY ts
              ) AS next_ts
          FROM events
      ),
      daily_covered AS (
          SELECT
              day_ist,
              SUM(
                  CASE
                      WHEN active_streams > 0 AND next_ts IS NOT NULL
                          THEN date_diff('second', ts, next_ts)
                      ELSE 0
                  END
              ) AS covered_seconds
          FROM events_with_active
          GROUP BY day_ist
      ),
      moment_uploads as (select * from d11_stitch.moment_raw)
      SELECT
          coalesce(cast(d.day_ist as timestamp),cast(e.day_ist as timestamp)) day_ist,
          d.total_stream_seconds / 60.0  AS total_stream_minutes,
          c.covered_seconds/ 3600.0 AS covered_hours,
          e.new_moments_daily,
          e.new_duration_sec_daily/60.0 as moment_uploads,
          f.distinct_streams,
          f.distinct_creators
      FROM daily_total d
      JOIN daily_covered c
        ON d.day_ist = c.day_ist
      full outer join moment_uploads e
      on d.day_ist = e.day_ist
      left join d11_stitch.daylevel_metric f
      on d.day_ist = f.eventdate
      and date(d.day_ist) >= date('2025-12-04')
      ORDER BY d.day_ist )
SELECT
    (DATE_FORMAT((stream_day_level_details.day_ist  AT TIME ZONE 'Asia/Kolkata'), '%Y-%m-%d')) AS "stream_day_level_details.day_ist_date",
    COALESCE(SUM(CAST( stream_day_level_details.covered_hours   AS DOUBLE)), 0) AS "covered_hours",
    COALESCE(SUM(CAST( stream_day_level_details.total_stream_minutes   AS DOUBLE)), 0) AS "total_stream_minutes",
    COALESCE(SUM(CAST( stream_day_level_details.distinct_creators   AS DOUBLE)), 0) AS "creators",
    COALESCE(SUM(CAST( stream_day_level_details.distinct_streams   AS DOUBLE)), 0) AS "active_streams",
    COALESCE(SUM(CAST( stream_day_level_details.new_moments_daily   AS DOUBLE)), 0) AS "moments_uploaded"
FROM stream_day_level_details
WHERE (stream_day_level_details.day_ist ) >= ((CAST(CAST((FORMAT_DATETIME(DATE_ADD('day', -7, CAST(CAST(DATE_TRUNC('DAY', (NOW() AT TIME ZONE 'Asia/Kolkata')) AS DATE) AS TIMESTAMP)), 'yyyy-MM-dd HH:mm:ss.SSS') || ' Asia/Kolkata') AS TIMESTAMP WITH TIME ZONE) AT TIME ZONE 'UTC' AS TIMESTAMP)))
GROUP BY
    1
ORDER BY
    1 DESC
LIMIT 500