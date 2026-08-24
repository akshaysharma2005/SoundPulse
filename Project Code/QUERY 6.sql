-- ============================================================
-- QUERY 6: GET THE MOST ACTIVE USERS IN THE SYSTEM ACCORDING TO
--           THE NUMBER OF SONGS THEY HEARD ACROSS ALL SESSIONS
-- ============================================================
-- BUG FIXED:
--   Original used DENSE_RANK() OVER(ORDER BY SONGS_NUMBER) ASC (ascending),
--   which incorrectly ranked the LEAST active user as #1.
--   Also included SESSION_ID and SONG_NAME in the subquery, causing 6,786
--   duplicate rows (one per user × session × song combination).
--   FIXES APPLIED:
--     1. Changed to ORDER BY SONGS_NUMBER DESC so the most active user ranks #1.
--     2. Removed SESSION_ID and SONG_NAME — aggregate strictly by USER_ID,
--        USER_FIRST_NAME, USER_LAST_NAME, USER_GENDER to eliminate duplicates.
--     3. Switched from window COUNT to GROUP BY + plain COUNT for clean aggregation.
-- ============================================================

SELECT
    USER_RANK,
    USER_ID,
    USER_FIRST_NAME,
    USER_LAST_NAME,
    USER_GENDER,
    SONGS_NUMBER
FROM (
    SELECT
        USER_ID,
        USER_FIRST_NAME,
        USER_LAST_NAME,
        USER_GENDER,
        COUNT(SONG_NAME) AS SONGS_NUMBER,
        DENSE_RANK() OVER (ORDER BY COUNT(SONG_NAME) DESC) AS USER_RANK
    FROM EVENTS
    WHERE SONG_NAME IS NOT NULL
      AND SONG_PLAYED = 'NextSong'
    GROUP BY USER_ID, USER_FIRST_NAME, USER_LAST_NAME, USER_GENDER
) SUB_QUERY
ORDER BY USER_RANK;
