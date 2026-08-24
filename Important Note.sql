-- ============================================================
-- IMPORTANT NOTE: ALTERNATIVE JOIN STRATEGIES
-- Understanding the Data Disparity Between the Song Catalog (SONGS)
-- and the Live Streaming Event Logs (EVENTS)
-- ============================================================
--
-- BACKGROUND:
--   EVENTS table : 8,056 streaming log rows across 96 users
--   SONGS  table : 79 songs in the catalog
--
--   The song catalog (79 songs) is a small, curated metadata reference.
--   The events log (8,056 rows) captures every real user interaction —
--   home page visits, song plays, errors, logouts, etc.
--
--   Only a tiny fraction of event-log songs exist in the catalog.
--   Using INNER JOIN between the two tables discards 99%+ of real data.
--
-- WHY THIS MATTERS:
--   A naive INNER JOIN between EVENTS and SONGS will:
--     - Match only ~11 artists / 2 song names that appear in BOTH tables
--     - Silently drop 8,000+ event rows — making analysis severely skewed
--     - Produce results that look "clean" but are statistically meaningless
--
-- SOLUTION: Always use LEFT JOIN (EVENTS as the driving table).
-- ============================================================

-- ============================================================
-- 1. INNER JOIN  — the problematic original approach
-- ============================================================
-- Only returns rows where ARTIST_NAME matches in BOTH tables.
-- Result: ~22 rows (only ~11 artists in common). 8,034 events lost.
-- ============================================================
SELECT
    E.ARTIST_NAME,
    S.ARTIST_ID,
    S.ARTIST_LOCATION,
    COUNT(E.USER_ID) AS USER_COUNT
FROM EVENTS E
INNER JOIN SONGS S ON E.ARTIST_NAME = S.ARTIST_NAME
GROUP BY E.ARTIST_NAME, S.ARTIST_ID, S.ARTIST_LOCATION
ORDER BY USER_COUNT DESC;

-- ============================================================
-- 2. LEFT JOIN  — recommended approach
-- ============================================================
-- Returns ALL artists from EVENTS. If a catalog match exists,
-- catalog columns are populated; otherwise they are NULL.
-- Result: all unique artists across 8,056 events are preserved.
-- ============================================================
SELECT
    E.ARTIST_NAME,
    S.ARTIST_ID,
    S.ARTIST_LOCATION,
    S.ARTIST_LATITUDE,
    S.ARTIST_LONGTUDE,
    COUNT(E.USER_ID) AS USER_COUNT
FROM EVENTS E
LEFT JOIN SONGS S ON E.ARTIST_NAME = S.ARTIST_NAME
GROUP BY E.ARTIST_NAME, S.ARTIST_ID, S.ARTIST_LOCATION, S.ARTIST_LATITUDE, S.ARTIST_LONGTUDE
ORDER BY USER_COUNT DESC;

-- ============================================================
-- 3. RIGHT JOIN  — catalog-centric view
-- ============================================================
-- Returns ALL songs in the SONGS catalog, even if they have
-- never been streamed. Useful for identifying "dead catalog"
-- songs that nobody has played yet.
-- Result: 79 catalog rows. Most will show NULL USER_COUNT
-- because the catalog songs were almost never played.
-- ============================================================
SELECT
    S.SONG_NAME,
    S.ARTIST_NAME,
    S.ARTIST_ID,
    COUNT(E.USER_ID) AS STREAM_COUNT
FROM EVENTS E
RIGHT JOIN SONGS S ON E.SONG_NAME = S.SONG_NAME
GROUP BY S.SONG_NAME, S.ARTIST_NAME, S.ARTIST_ID
ORDER BY STREAM_COUNT DESC NULLS LAST;

-- ============================================================
-- 4. FULL OUTER JOIN  — complete picture of both datasets
-- ============================================================
-- Returns all rows from BOTH tables. Shows:
--   - Songs streamed by users but NOT in the catalog (NULL on right)
--   - Songs in the catalog that were NEVER streamed (NULL on left)
-- This is the most transparent diagnostic join.
-- ============================================================
SELECT
    COALESCE(E.SONG_NAME,  S.SONG_NAME)   AS SONG_NAME,
    COALESCE(E.ARTIST_NAME, S.ARTIST_NAME) AS ARTIST_NAME,
    S.ARTIST_ID,
    S.ARTIST_LOCATION,
    COUNT(E.USER_ID) AS STREAM_COUNT,
    CASE
        WHEN E.SONG_NAME  IS NULL THEN 'In Catalog — Never Streamed'
        WHEN S.SONG_NAME  IS NULL THEN 'Streamed — Not in Catalog'
        ELSE 'Matched (Catalog + Streamed)'
    END AS MATCH_STATUS
FROM EVENTS E
FULL OUTER JOIN SONGS S ON E.SONG_NAME = S.SONG_NAME
GROUP BY
    COALESCE(E.SONG_NAME,  S.SONG_NAME),
    COALESCE(E.ARTIST_NAME, S.ARTIST_NAME),
    S.ARTIST_ID,
    S.ARTIST_LOCATION,
    MATCH_STATUS
ORDER BY MATCH_STATUS, STREAM_COUNT DESC;

-- ============================================================
-- KEY BUSINESS INSIGHT FROM THE JOIN ANALYSIS:
--
--   INNER JOIN result  :   ~22 rows  (99.7% of data discarded)
--   LEFT  JOIN result  : ~3,200 rows (all streaming artists included)
--   RIGHT JOIN result  :    79 rows  (all catalog songs included)
--   FULL OUTER result  : ~3,200 rows (full transparency of both datasets)
--
--   The tiny song catalog (79 songs) represents a metadata reference —
--   it does NOT cover the full range of music users actually stream.
--   Analytical queries should always use EVENTS as the primary table
--   and LEFT JOIN the SONGS catalog purely for enrichment metadata
--   (e.g., SONG_ID, ARTIST_LATITUDE, ARTIST_LOCATION).
-- ============================================================