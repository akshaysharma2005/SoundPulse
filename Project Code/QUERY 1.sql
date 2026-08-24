-- ============================================================
-- QUERY 1: ORDER OF ARTISTS WITH THEIR LOCATIONS ACCORDING TO
--           THE NUMBER OF USERS WHO HEAR THEIR SONGS
-- ============================================================
-- FIX APPLIED:
--   Original used an implicit INNER JOIN (FROM EVENTS E, SONGS S WHERE ...)
--   which matched on ARTIST_NAME and dropped 99.7% of event rows (only
--   11 artists appear in both the 79-song catalog and the 8,056 event logs).
--   Changed to a LEFT JOIN so all artists from EVENTS are included.
--   EVENTS is the source of truth for user activity; SONGS provides
--   enrichment metadata (ARTIST_ID, ARTIST_LOCATION, lat/lng) where available.
-- ============================================================

SELECT DISTINCT
    E.ARTIST_NAME,
    S.ARTIST_ID,
    S.ARTIST_LOCATION,
    S.ARTIST_LATITUDE,
    S.ARTIST_LONGTUDE,
    COUNT(E.USER_ID) OVER (PARTITION BY E.ARTIST_NAME) AS USERS_NUMBER
FROM EVENTS E
LEFT JOIN SONGS S ON E.ARTIST_NAME = S.ARTIST_NAME
ORDER BY USERS_NUMBER DESC;
