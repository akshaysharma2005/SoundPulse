-- ============================================================
-- QUERY 4: GET THE RANK OF EACH SONG IN EACH SESSION ACCORDING
--           TO THE NUMBER OF USERS WHO HEARD THEM IN THAT SESSION
-- ============================================================
-- No bug fixes required for this query. Converted from .txt to .sql.
-- ============================================================

SELECT *
FROM (
    SELECT DISTINCT
        SESSION_ID,
        SONG_NAME,
        USERS_NUMBER,
        ARTIST_NAME,
        SONG_LEVEL,
        DENSE_RANK() OVER (PARTITION BY SESSION_ID ORDER BY USERS_NUMBER DESC) AS SONG_RANK
    FROM (
        SELECT
            SESSION_ID,
            SONG_NAME,
            COUNT(USER_ID) OVER (PARTITION BY SESSION_ID, SONG_NAME) AS USERS_NUMBER,
            ARTIST_NAME,
            SONG_LEVEL
        FROM EVENTS
        WHERE SONG_NAME IS NOT NULL
          AND SONG_PLAYED = 'NextSong'
    ) SUB_QUERY
) SUB_QUERY_2
GROUP BY SESSION_ID, SONG_NAME, SONG_LEVEL, USERS_NUMBER, ARTIST_NAME, SONG_RANK
ORDER BY SESSION_ID, SONG_RANK;
