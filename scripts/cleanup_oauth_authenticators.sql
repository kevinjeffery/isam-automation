-- cleanup_oauth_authenticators.sql
-- v2.00_2020-08-27
-- Kevin Jeffery
-- Example: CALL CLEANUP_OAUTH_AUTHENTICATORS(1000000, ?, ?, ?)

CREATE OR REPLACE PROCEDURE CLEANUP_OAUTH_AUTHENTICATORS (
    IN maxCount INT,
    OUT rowCount INT,
    OUT expiredCount INT,
    OUT cleanupCount INT)
LANGUAGE SQL
MODIFIES SQL DATA
AUTONOMOUS
BEGIN

select count(*) INTO rowCount from OAUTH_AUTHENTICATORS;
select count(*) INTO expiredCount from OAUTH_AUTHENTICATORS
WHERE STATE_ID NOT IN (SELECT STATE_ID from OAUTH20_TOKEN_CACHE);
SET cleanupCount = 0;
IF expiredCount < maxCount THEN
    SET maxCount = expiredCount;
END IF;

L0: WHILE (cleanupCount < maxCount) DO
    L1: FOR expireID AS
    SELECT APP_INST_ID
    FROM OAUTH_AUTHENTICATORS
    WHERE STATE_ID NOT IN (SELECT STATE_ID FROM OAUTH20_TOKEN_CACHE) FETCH FIRST 1000 ROWS ONLY
    DO
        DELETE FROM OAUTH_AUTHENTICATORS WHERE APP_INST_ID = expireID.APP_INST_ID;
        SET cleanupCount = cleanupCount + 1;
        IF cleanupCount >= maxCount THEN
            LEAVE L1;
        END IF;
    END FOR;
    COMMIT;
END WHILE;

END
