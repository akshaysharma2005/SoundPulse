-- ============================================================
-- QUERY 2: SONGS USERS HEAR THE MOST, ORDERED FROM MOST TO LEAST,
--           WITH ARTIST OF EACH SONG
-- ============================================================
-- FIX APPLIED:
--   1. Original used an implicit INNER JOIN which matched only 2 songs from
--      the 79-song catalog, dropping 99% of stream event data.
--      Changed to LEFT JOIN so all songs from EVENTS are included;
--      SONGS catalog provides enrichment metadata (SONG_ID, ARTIST_ID)
--      where a match exists.
--   2. Added DISTINCT to the outer query to eliminate duplicate rows caused
--      by the 1-to-many relationship between SONGS catalog and EVENTS rows.
-- ============================================================

SELECT DISTINCT
    E.SONG_NAME,
    S.SONG_ID,
    S.ARTIST_ID,
    E.ARTIST_NAME,
    E.SONG_LENGTH_IN_SECONDS,
    COUNT(E.USER_ID) OVER (PARTITION BY E.SONG_NAME) AS USERS_NUMBER
FROM EVENTS E
LEFT JOIN SONGS S ON E.SONG_NAME = S.SONG_NAME
WHERE E.SONG_PLAYED = 'NextSong'
  AND E.SONG_NAME IS NOT NULL
ORDER BY USERS_NUMBER DESC;
