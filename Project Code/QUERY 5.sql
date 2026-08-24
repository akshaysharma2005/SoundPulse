-- ============================================================
-- QUERY 5: ORDER OF ARTISTS ACCORDING TO THE NUMBER OF SONGS THEY MADE
-- ============================================================
-- BUG FIXED:
--   Original had SONG_NAME in SELECT DISTINCT, which caused:
--     - 5,296 duplicate rows (one per unique artist+song combination)
--     - Empty ARTIST_NAME strings ranking #1 (no filter applied)
--   FIXES APPLIED:
--     1. Aggregate strictly on ARTIST_NAME only — remove SONG_NAME from SELECT.
--     2. Count DISTINCT songs per artist using COUNT(DISTINCT SONG_NAME).
--     3. Filter out empty artist name strings: WHERE ARTIST_NAME != ''
--        and ARTIST_NAME IS NOT NULL.
-- ============================================================

SELECT
    ARTIST_NAME,
    SONGS_NUMBER,
    DENSE_RANK() OVER (ORDER BY SONGS_NUMBER DESC) AS ARTIST_RANK
FROM (
    SELECT
        ARTIST_NAME,
        COUNT(DISTINCT SONG_NAME) AS SONGS_NUMBER
    FROM EVENTS
    WHERE ARTIST_NAME IS NOT NULL
      AND ARTIST_NAME != ''
      AND SONG_NAME IS NOT NULL
      AND SONG_PLAYED = 'NextSong'
    GROUP BY ARTIST_NAME
) SUB_QUERY
ORDER BY ARTIST_RANK;
