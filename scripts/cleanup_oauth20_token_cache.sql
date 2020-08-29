-- cleanup_oauth20_token_cache.sql
-- v2.00_2020-08-27
-- Kevin Jeffery
-- Example: CALL CLEANUP_OAUTH20_TOKEN_CACHE(1000000, ${current_time_millis}, ?, ?, ?)

CREATE OR REPLACE PROCEDURE CLEANUP_OAUTH20_TOKEN_CACHE (
    IN maxCount INT,
    IN currentTimeSeconds BIGINT,
    OUT rowCount INT,
    OUT expiredCount INT,
    OUT cleanupCount INT)
LANGUAGE SQL
MODIFIES SQL DATA
AUTONOMOUS
BEGIN

select count(*) INTO rowCount from OAUTH20_TOKEN_CACHE;
select count(*) INTO expiredCount from OAUTH20_TOKEN_CACHE
WHERE LIFETIME < (currentTimeSeconds - DATE_CREATED/1000);
SET cleanupCount = 0;
IF expiredCount < maxCount THEN
    SET maxCount = expiredCount;
END IF;

L0: WHILE (cleanupCount < maxCount) DO
    L1: FOR expireID AS
    SELECT TOKEN_ID
    FROM OAUTH20_TOKEN_CACHE
    WHERE LIFETIME < (currentTimeSeconds - DATE_CREATED/1000) FETCH FIRST 1000 ROWS ONLY
    DO
        DELETE FROM OAUTH20_TOKEN_CACHE WHERE TOKEN_ID = expireID.TOKEN_ID;
        SET cleanupCount = cleanupCount + 1;
        IF cleanupCount >= maxCount THEN
            LEAVE L1;
        END IF;
    END FOR;
    COMMIT;
END WHILE;

END
