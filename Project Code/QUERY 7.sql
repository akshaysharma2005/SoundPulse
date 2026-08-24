-- ============================================================
-- QUERY 7: GET THE LONGEST AND SHORTEST SONG IN EACH SESSION
-- ============================================================
-- No bug fixes required for this query. Converted from .txt to .sql.
-- ============================================================

SELECT
    SONG_NAME,
    ARTIST_NAME,
    SESSION_ID,
    SONG_LENGTH_IN_SECONDS,
    USER_ID,
    FIRST_VALUE(SONG_NAME) OVER (PARTITION BY SESSION_ID ORDER BY SONG_LENGTH_IN_SECONDS DESC) AS LONGEST_SONG,
    FIRST_VALUE(SONG_NAME) OVER (PARTITION BY SESSION_ID ORDER BY SONG_LENGTH_IN_SECONDS ASC)  AS SHORTEST_SONG
FROM EVENTS
WHERE SONG_NAME IS NOT NULL
  AND SONG_PLAYED = 'NextSong'
ORDER BY SESSION_ID;
