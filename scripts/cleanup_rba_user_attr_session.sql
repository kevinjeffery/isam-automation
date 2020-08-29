-- cleanup_rba_user_attr_session.sql
-- v2.00_2020-08-27
-- Kevin Jeffery
-- Example: CALL CLEANUP_RBA_USER_ATTR_SESSION(1000000, 1800, ?, ?, ?)

CREATE OR REPLACE PROCEDURE CLEANUP_RBA_USER_ATTR_SESSION ( 
    IN maxCount INT,
    IN sessionTimeout INT,
    OUT rowCount INT;
    OUT expiredCount INT,
    OUT cleanupCount INT)
LANGUAGE SQL
MODIFIES SQL DATA
AUTONOMOUS
BEGIN
DECLARE target TIMESTAMP;

SET target = CURRENT TIMESTAMP - sessionTimeout SECONDS;

select count(*) INTO rowCount from RBA_USER_ATTR_SESSION;
select count(*) INTO expiredCount from RBA_USER_ATTR_SESSION
WHERE rec_time < target;
SET cleanupCount = 0;
IF expiredCount < maxCount THEN
    SET maxCount = expiredCount;
END IF;

L0: WHILE (cleanupCount < maxCount) DO
    L1: FOR expireID AS
    SELECT SESSION_ID
    FROM RBA_USER_ATTR_SESSION
    WHERE rec_time < target FETCH FIRST 1000 ROWS ONLY
    DO
        DELETE FROM RBA_USER_ATTR_SESSION_DATA WHERE SESSION_ID = expireID.SESSION_ID;
        DELETE FROM RBA_USER_ATTR_SESSION WHERE SESSION_ID = expireID.SESSION_ID;
        SET cleanupCount = cleanupCount + 1;
        IF cleanupCount >= maxCount THEN
            LEAVE L1;
        END IF;
    END FOR;
    COMMIT;
END WHILE;

END
