-- cleanup_rba_device.sql
-- v2.00_2020-08-27
-- Kevin Jeffery
-- Example: CALL CLEANUP_RBA_DEVICE(1000000, 100, ?, ?, ?)

CREATE OR REPLACE PROCEDURE CLEANUP_RBA_DEVICE (
    IN maxCount INT,
    IN deviceExpirationTime INT,
    OUT rowCount INT,
    OUT expiredCount INT,
    OUT cleanupCount INT)
LANGUAGE SQL
MODIFIES SQL DATA
AUTONOMOUS
BEGIN
DECLARE target TIMESTAMP;

SET target = CURRENT TIMESTAMP;

SELECT count(*) INTO rowCount FROM RBA_DEVICE;
SELECT count(*) INTO expiredCount FROM RBA_DEVICE
WHERE timestampdiff(16, char(target - LAST_USED_TIME)) > deviceExpirationTime;
SET cleanupCount = 0;
IF expiredCount < maxCount THEN
    SET maxCount = expiredCount;
END IF;

L0: WHILE (cleanupCount < maxCount) DO
    L1: FOR expireID AS
    SELECT DEVICE_ID
    FROM RBA_DEVICE
    WHERE timestampdiff(16, char(target - LAST_USED_TIME)) > deviceExpirationTime FETCH FIRST 1000 ROWS ONLY
    DO
        DELETE FROM RBA_DEVICE WHERE DEVICE_ID = expireID.DEVICE_ID;
        SET cleanupCount = cleanupCount + 1;
        IF cleanupCount >= maxCount THEN
            LEAVE L1;
        END IF;
    END FOR;
    COMMIT;
END WHILE;

END
