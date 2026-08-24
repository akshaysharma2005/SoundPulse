-- ============================================================
-- QUERY 10: HOW LONG EACH USER SPENDS ON THE WEBSITE
--            (TOTAL LISTENING DURATION IN SECONDS)
-- ============================================================
-- BUG FIXED:
--   Original DENSE_RANK() OVER(ORDER BY USER_DURATION_IN_SECONDS DESC)
--   had no column alias, resulting in an unnamed column in query output.
--   FIX APPLIED:
--     Added AS USER_RANK alias to the DENSE_RANK() window function
--     in the outer SELECT for clear, named output.
-- ============================================================

SELECT
    USER_ID,
    DENSE_RANK() OVER (ORDER BY USER_DURATION_IN_SECONDS DESC) AS USER_RANK,
    USER_FIRST_NAME,
    USER_LAST_NAME,
    USER_DURATION_IN_SECONDS
FROM (
    SELECT DISTINCT
        USER_ID,
        USER_FIRST_NAME,
        USER_LAST_NAME,
        SUM(SONG_LENGTH_IN_SECONDS) OVER (PARTITION BY USER_ID) AS USER_DURATION_IN_SECONDS
    FROM EVENTS
    WHERE SONG_NAME IS NOT NULL
      AND SONG_PLAYED = 'NextSong'
) SUB_QUERY
ORDER BY USER_RANK;
