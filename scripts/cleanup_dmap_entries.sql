-- cleanup_dmap_entries.sql
-- v2.00_2020-08-27
-- Kevin Jeffery
-- Example: CALL CLEANUP_DMAP_ENTRIES(1000000, ${current_time_millis} ,?, ?, ?)

CREATE OR REPLACE PROCEDURE CLEANUP_DMAP_ENTRIES (
    IN maxCount INT,
    IN currentTimeMillis BIGINT,
    OUT rowCount INT,
    OUT expiredCount INT ,
    OUT cleanupCount INT)
LANGUAGE SQL
MODIFIES SQL DATA
AUTONOMOUS
BEGIN

SELECT count(*) INTO rowCount FROM DMAP_ENTRIES;
SELECT count(*) INTO expiredCount FROM DMAP_ENTRIES
WHERE DMAP_EXPIRY < currentTimeMillis AND DMAP_EXPIRY <> 0;
SET cleanupCount = 0;
IF expiredCount < maxCount THEN
    SET maxCount = expiredCount;
END IF;

L0: WHILE (cleanupCount < maxCount) DO
    L1: FOR expireID AS
    SELECT DMAP_KEY, DMAP_PARTITION
    FROM DMAP_ENTRIES
    WHERE DMAP_EXPIRY < currentTimeMillis AND DMAP_EXPIRY <> 0 FETCH FIRST 1000 ROWS ONLY
    DO
        DELETE FROM DMAP_ENTRIES WHERE DMAP_KEY = expireID.DMAP_KEY AND DMAP_PARTITION = expireID.DMAP_PARTITION;
        SET cleanupCount = cleanupCount + 1;
        IF cleanupCount >= maxCount THEN
            LEAVE L1;
        END IF;
    END FOR;
    COMMIT;
END WHILE;

END
