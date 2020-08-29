-- cleanup_auth_txn_obl_data.sql
-- v2.00_2020-08-27
-- Kevin Jeffery
-- Example: CALL CLEANUP_AUTH_TXN_OBL_DATA(1000000, 3600, ?, ?, ?)

CREATE OR REPLACE PROCEDURE CLEANUP_AUTH_TXN_OBL_DATA (
    IN maxCount INT,
    IN sessionTimeout INT,
    OUT rowCount INT,
    OUT expiredCount INT,
    OUT cleanupCount INT)
LANGUAGE SQL
MODIFIES SQL DATA
AUTONOMOUS
BEGIN
DECLARE target TIMESTAMP;

SET target = CURRENT TIMESTAMP - sessionTimeout SECONDS;

SELECT count(*) INTO rowCount FROM AUTH_TXN_OBL_DATA;
SELECT count(*) INTO expiredCount FROM AUTH_TXN_OBL_DATA
WHERE rec_time < target;
SET cleanupCount = 0;
IF expiredCount < maxCount THEN
    SET maxCount = expiredCount;
END IF;

L0: WHILE (cleanupCount < maxCount) DO
    L1: FOR expireID AS
    SELECT TXN_ID
    FROM AUTH_TXN_OBL_DATA
    WHERE rec_time < target FETCH FIRST 1000 ROWS ONLY
    DO
        DELETE FROM AUTH_TXN_OBL_DATA WHERE TXN_ID = expireID.TXN_ID;
        SET cleanupCount = cleanupCount + 1;
        IF cleanupCount >= maxCount THEN
            LEAVE L1;
        END IF;
    END FOR;
    COMMIT;
END WHILE;

END
