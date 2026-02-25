-- Users who attended AB CRIC INFO's most recent stream
-- Run in Athena (d11_stitch database) with profile dream2o

-- Step 1: Get AB CRIC INFO's most recent stream ID (run this first to get stream_id)
SELECT 
    id AS stream_id,
    creatorname,
    streamstarttime,
    uniqueviewers,
    watch_hours
FROM d11_stitch.livestream_creator
WHERE LOWER(TRIM(creatorname)) LIKE '%ab cric info%'
ORDER BY streamstarttime DESC
LIMIT 1;

-- Step 2: List users who watched that stream (replace <STREAM_ID> with result from Step 1)
SELECT 
    userid,
    SUM(watch_seconds) AS total_watch_seconds,
    ROUND(SUM(watch_seconds) / 60.0, 1) AS watch_minutes,
    MIN(eventdate) AS first_seen,
    MAX(eventdate) AS last_seen
FROM d11_stitch.day_user_stream_watchtime
WHERE streamid = CAST(<STREAM_ID> AS VARCHAR)
GROUP BY userid
ORDER BY total_watch_seconds DESC;

-- Single-query version (no manual stream_id substitution):
WITH last_stream AS (
    SELECT id AS stream_id
    FROM d11_stitch.livestream_creator
    WHERE LOWER(TRIM(creatorname)) LIKE '%ab cric info%'
    ORDER BY streamstarttime DESC
    LIMIT 1
)
SELECT 
    w.userid,
    SUM(w.watch_seconds) AS total_watch_seconds,
    ROUND(SUM(w.watch_seconds) / 60.0, 1) AS watch_minutes,
    MIN(w.eventdate) AS first_seen,
    MAX(w.eventdate) AS last_seen
FROM d11_stitch.day_user_stream_watchtime w
CROSS JOIN last_stream l
WHERE w.streamid = CAST(l.stream_id AS VARCHAR)
GROUP BY w.userid
ORDER BY total_watch_seconds DESC;
