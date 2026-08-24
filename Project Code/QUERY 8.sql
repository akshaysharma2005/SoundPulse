-- ============================================================
-- QUERY 8: ANALYSIS OF THE PROBABILITY OF EACH USER SUCCESSFULLY
--           ACCESSING A SONG (HTTP 200) FROM ALL PLATFORM REQUESTS
-- ============================================================
-- BUG FIXED:
--   Original filtered WHERE SONG_PLAYED = 'NextSong', which ensures
--   SONG_STATUS is always 200 (NextSong events never return 404/307).
--   This produced a 100% success rate for every single user — hiding
--   all real HTTP errors that occur on other page interactions.
--   FIX APPLIED:
--     Removed the SONG_PLAYED = 'NextSong' filter so that ALL user
--     interactions (NextSong, Home, Error, Logout, etc.) are evaluated.
--     404 Not Found and 307 Temporary Redirect events are now included,
--     giving a true picture of platform reliability per user.
-- ============================================================

SELECT DISTINCT
    USER_ID,
    USER_FIRST_NAME,
    USER_LAST_NAME,
    NUMBER_OF_REQUESTS,
    SUCCESSFUL_REQUESTS,
    CAST(SUCCESSFUL_REQUESTS AS FLOAT) / NUMBER_OF_REQUESTS AS SUCCESS_PERCENTAGE
FROM (
    SELECT
        USER_ID,
        USER_FIRST_NAME,
        USER_LAST_NAME,
        COUNT(USER_ID)                                         OVER (PARTITION BY USER_ID) AS NUMBER_OF_REQUESTS,
        COUNT(CASE WHEN SONG_STATUS = 200 THEN 1 END)         OVER (PARTITION BY USER_ID) AS SUCCESSFUL_REQUESTS
    FROM EVENTS
    WHERE USER_ID IS NOT NULL
) SUB_QUERY
ORDER BY SUCCESS_PERCENTAGE ASC, USER_ID;
