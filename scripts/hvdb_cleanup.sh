#!/bin/ksh
#
# **************************************************************************
VERSION="hvdb_cleanup.sh - v1.05_2020-AUG-27"
# * 
# * Kevin Jeffery
# *
# * Cleanup HVDB
# *
# **************************************************************************

# Default setting of attributeCollection.sessionTimeout (seconds)
SESSION_TIMEOUT=1800
# Default setting of deviceRegistration.inactiveExpirationTime (days)
INACTIVE_EXPIRATION_TIME=100
# Current time in seconds since epoch
CURRENT_TIME_SECONDS=$(date +%s)
# Current time in milliseconds since epoch
CURRENT_TIME_MILLIS=$(date +%s%3N)
# Maximum rows to delete
MAX_ROWS=1000000

SCRIPT_HOME=$(dirname $0)
[[ "${SCRIPT_HOME}" == "." ]] && SCRIPT_HOME=$(pwd)
echo "**********************************************************************"
echo "*** $(date)"
echo "*** ${VERSION}"

function usage {
  echo "*** Usage: ${0} -s <schema_name>"
  echo "*"
  echo "*   -s Schema name of the HVDB user tables."
  echo "*   -t Attribute Collection Session timeout in seconds (attributeCollection.sessionTimeout Default: 1800)"
  echo "*   -d Device registration inactive expiration time in days (deviceRegistration.inactiveExpirationTime Default: 100)"
  echo "*   -r Maximum rows to delete (Default: 1,000,000)"
  case $1 in
   s) echo -e "*   Schema name missing\n"
      ;;
  esac
  exit 1
}

while getopts ":s:t:d:r:" option;
do
 case $option in
  s)
   typeset -u SCHEMA_NAME=${OPTARG}
   ;;
  t)
   typeset -i SESSION_TIMEOUT=${optarg}
   ;;
  d)
   typeset -i INACTIVE_EXPIRATION_TIME=${optarg}
   ;;
  r)
   typeset -i MAX_ROWS=${optarg}
   ;;
  :)
   echo "option -$OPTARG needs an argument"
   ;;
  *)
   echo "invalid option -$OPTARG" 
   ;;
 esac
done

[[ -z ${SCHEMA_NAME} ]] && usage s

. ~/sqllib/db2profile

db2 connect to HVDB
db2 set schema ${SCHEMA_NAME}

echo "*** Load stored procedures"
echo "*   cleanup_auth_txn_obl_data.sql"
db2 -tvf ${SCRIPT_HOME}/cleanup_auth_txn_obl_data.sql
echo "*   cleanup_rba_device.sql"
db2 -tvf ${SCRIPT_HOME}/cleanup_rba_device.sql
echo "*   cleanup_rba_user_attr_session.sql"
db2 -tvf ${SCRIPT_HOME}/cleanup_rba_user_attr_session.sql
echo "*   cleanup_dmap_entries.sql"
db2 -tvf ${SCRIPT_HOME}/cleanup_dmap_entries.sql
echo "*   cleanup_oauth20_token_cache.sql"
db2 -tvf ${SCRIPT_HOME}/cleanup_oauth20_token_cache.sql
echo "*   cleanup_oauth20_token_extra_attribute.sql"
db2 -tvf ${SCRIPT_HOME}/cleanup_oauth20_token_extra_attribute.sql
echo "*   cleanup_oauth_authenticators.sql"
db2 -tvf ${SCRIPT_HOME}/cleanup_oauth_authenticators.sql

echo "*** Start cleanup on RBA_DEVICE"
db2 "CALL CLEANUP_RBA_DEVICE(${MAX_ROWS}, ${INACTIVE_EXPIRATION_TIME}, ?, ?, ?)"

echo "*** Start cleanup on RBA_USER_ATTR_SESSION"
db2 "CALL CLEANUP_RBA_USER_ATTR_SESSION(${MAX_ROWS}, ${SESSION_TIMEOUT}, ?, ?, ?)"

echo "*** Start cleanup on AUTH_TXN_OBL_DATA"
db2 "CALL CLEANUP_AUTH_TXN_OBL_DATA(${MAX_ROWS}, ${SESSION_TIMEOUT}, ?, ?, ?)"

echo "*** Start cleanup on DMAP_ENTRIES"
db2 "CALL CLEANUP_DMAP_ENTRIES(${MAX_ROWS}, ${CURRENT_TIME_MILLIS}, ?, ?, ?)"

echo "*** Start cleanup on OAUTH20_TOKEN_CACHE"
db2 "CALL CLEANUP_OAUTH20_TOKEN_CACHE(${MAX_ROWS}, ${CURRENT_TIME_SECONDS}, ?, ?, ?)"

echo "*** Start cleanup on OAUTH20_TOKEN_EXTRA_ATTRIBUTE"
db2 "CALL CLEANUP_OAUTH20_TOKEN_EXTRA_ATTRIBUTE(${MAX_ROWS}, ?, ?, ?)"

echo "*** Start cleanup on OAUTH_AUTHENTICATORS"
db2 "CALL CLEANUP_OAUTH_AUTHENTICATORS(${MAX_ROWS}, ?, ?, ?)"

db2 commit
db2 terminate


