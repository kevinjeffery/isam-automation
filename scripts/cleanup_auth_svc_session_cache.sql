-- cleanup_auth_svc_session_cache.sql
-- v2.00_2020-08-27
-- Kevin Jeffery
-- Example: CALL CLEANUP_AUTH_SVC_SESSION_CACHE(1000000, ${current_time_millis}, ?, ?, ?)

CREATE OR REPLACE PROCEDURE CLEANUP_AUTH_SVC_SESSION_CACHE (
    IN maxCount INT,
    IN currentTimeMillis BIGINT,
    OUT rowCount INT,
    OUT expiredCount INT,
    OUT cleanupCount INT)
LANGUAGE SQL
MODIFIES SQL DATA
AUTONOMOUS
BEGIN

select count(*) INTO rowCount from AUTH_SVC_SESSION_CACHE;
select count(*) INTO expiredCount from AUTH_SVC_SESSION_CACHE
WHERE EXPIRY  < currentTimeMillis;
SET cleanupCount = 0;
IF expiredCount < maxCount THEN
    SET maxCount = expiredCount;
END IF;

L0: WHILE (cleanupCount < maxCount) DO
    L1: FOR expireID AS
    SELECT STATE_ID
    FROM AUTH_SVC_SESSION_CACHE
    WHERE EXPIRY < currentTimeMillis FETCH FIRST 1000 ROWS ONLY
    DO
        DELETE FROM AUTH_SVC_SESSION_CACHE WHERE STATE_ID = expireID.STATE_ID and EXPIRY < currentTimeMillis;
        SET cleanupCount = cleanupCount + 1;
        IF cleanupCount >= maxCount THEN
            LEAVE L1;
        END IF;
    END FOR;
    COMMIT;
END WHILE;

END
