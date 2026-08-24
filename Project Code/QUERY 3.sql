-- ============================================================
-- QUERY 3: GET MOST PLAYED SONGS IN TOTAL SESSIONS ACCORDING TO
--           THE NUMBER OF USERS, WITH PAID STATUS, ARTIST NAME, AND RANK
-- ============================================================
-- No bug fixes required for this query. Converted from .txt to .sql.
-- ============================================================

SELECT *, DENSE_RANK() OVER (ORDER BY USERS_NUMBER DESC) AS SONG_RANK
FROM (
    SELECT DISTINCT
        SONG_NAME,
        ARTIST_NAME,
        SONG_LEVEL,
        COUNT(USER_ID) OVER (PARTITION BY SONG_NAME) AS USERS_NUMBER
    FROM EVENTS
    WHERE SONG_PLAYED = 'NextSong'
) SUB_QUERY_1
WHERE SONG_NAME IS NOT NULL;
