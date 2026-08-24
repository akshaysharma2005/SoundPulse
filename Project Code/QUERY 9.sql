-- ============================================================
-- QUERY 9: GET THE NUMBER OF PAID VS FREE SONGS FOR EACH USER
--           AND THE PERCENTAGE OF PAID INCOME CONTRIBUTION
-- ============================================================
-- No bug fixes required for this query. Converted from .txt to .sql.
-- ============================================================

SELECT
    USER_ID,
    USER_FIRST_NAME,
    USER_LAST_NAME,
    PAID_SONGS_NUMBER,
    FREE_SONGS_NUMBER,
    CAST(PAID_SONGS_NUMBER AS FLOAT) / (PAID_SONGS_NUMBER + FREE_SONGS_NUMBER) AS PAID_SONGS_PERCENTAGE
FROM (
    SELECT DISTINCT
        USER_ID,
        USER_FIRST_NAME,
        USER_LAST_NAME,
        COUNT(CASE SONG_LEVEL WHEN 'paid' THEN 1 END) OVER (PARTITION BY USER_ID) AS PAID_SONGS_NUMBER,
        COUNT(CASE SONG_LEVEL WHEN 'free' THEN 1 END) OVER (PARTITION BY USER_ID) AS FREE_SONGS_NUMBER
    FROM EVENTS
    WHERE SONG_NAME IS NOT NULL
      AND SONG_PLAYED = 'NextSong'
) SUB_QUERY
ORDER BY USER_ID;
