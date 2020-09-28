#!/bin/ksh
#
# **************************************************************************
VERSION="rowcounts.sh - v1.06_2020-SEP-27"
# * 
# * Kevin Jeffery
# *
# * HVDB Rowcounts for cleanup
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

echo "**********************************************************************"
echo "*** $(date)"
echo "*** ${VERSION}"

function usage {
  echo "*** Usage: ${0} -s (schema_name)"
  echo "*"
  echo "*   -s Schema name of the HVDB user tables."
  echo "*   -t Attribute Collection Session timeout in seconds (attributeCollection.sessionTimeout Default: 1800)"
  echo "*   -d Device registration inactive expiration time in days (deviceRegistration.inactiveExpirationTime Default: 100)"
  case $1 in
   s) echo -e "*   Schema name missing\n"
      ;;
  esac
  exit 1
}

while getopts ":s:t:d:" option;
do
 case $option in
  s)
   typeset -u schema_name=${OPTARG}
   ;;
  t)
   typeset -i SESSION_TIMEOUT=${optarg}
   ;;
  d)
   typeset -i INACTIVE_EXPIRATION_TIME=${optarg}
   ;;
  :)
   echo "option -$OPTARG needs an argument"
   ;;
  *)
   echo "invalid option -$OPTARG" 
   ;;
 esac
done

[[ -z ${schema_name} ]] && usage s

. ~/sqllib/db2profile

db2 connect to HVDB

echo "*** ${schema_name}.AUTH_TXN_OBL_DATA"
db2 "select count(*) as ROWCOUNT from ${schema_name}.AUTH_TXN_OBL_DATA"
db2 "select count(*) as EXPIRED from ${schema_name}.AUTH_TXN_OBL_DATA where REC_TIME < (CURRENT TIMESTAMP - ${SESSION_TIMEOUT} SECONDS)"

echo "*** ${schema_name}.RBA_DEVICE"
db2 "select count(*) as ROWCOUNT from ${schema_name}.RBA_DEVICE"
db2 "select count(*) as EXPIRED from ${schema_name}.RBA_DEVICE where LAST_USED_TIME < (CURRENT TIMESTAMP - ${INACTIVE_EXPIRATION_TIME} DAYS"

echo "*** ${schema_name}.RBA_USER_ATTR_SESSION"
db2 "select count(*) as ROWCOUNT from ${schema_name}.RBA_USER_ATTR_SESSION"
db2 "select count(*) as EXPIRED from ${schema_name}.RBA_USER_ATTR_SESSION where REC_TIME < (CURRENT TIMESTAMP - ${SESSION_TIMEOUT} SECONDS)"

echo "*** ${schema_name}.DMAP_ENTRIES"
db2 "select count(*) as ROWCOUNT from ${schema_name}.DMAP_ENTRIES"
db2 "select count(*) as EXPIRED from ${schema_name}.DMAP_ENTRIES where DMAP_EXPIRY < ${CURRENT_TIME_MILLIS} AND DMAP_EXPIRY <> 0"

echo "*** ${schema_name}.AUTH_SVC_SESSION_CACHE"
db2 "select count(*) as ROWCOUNT from ${schema_name}.AUTH_SVC_SESSION_CACHE"
db2 "select count(*) as EXPIRED from ${schema_name}.AUTH_SVC_SESSION_CACHE where EXPIRY  < ${CURRENT_TIME_MILLIS}"

echo "*** ${schema_name}.OAUTH20_TOKEN_CACHE"
db2 "select count(*) as ROWCOUNT from ${schema_name}.OAUTH20_TOKEN_CACHE"
db2 "select count(*) as EXPIRED from ${schema_name}.OAUTH20_TOKEN_CACHE where LIFETIME < (${CURRENT_TIME_SECONDS} - DATE_CREATED/1000)"

echo "*** ${schema_name}.OAUTH20_TOKEN_EXTRA_ATTRIBUTE"
db2 "select count(*) as ROWCOUNT from ${schema_name}.OAUTH20_TOKEN_EXTRA_ATTRIBUTE"
db2 "select count(*) as EXPIRED from ${schema_name}.OAUTH20_TOKEN_EXTRA_ATTRIBUTE where STATE_ID not in (select STATE_ID from ${schema_name}.OAUTH20_TOKEN_CACHE where LIFETIME > (${CURRENT_TIME_SECONDS} - DATE_CREATED/1000))"

echo "*** ${schema_name}.OAUTH_AUTHENTICATORS"
db2 "select count(*) as ROWCOUNT from ${schema_name}.OAUTH_AUTHENTICATORS"
db2 "select count(*) as EXPIRED from ${schema_name}.OAUTH_AUTHENTICATORS where STATE_ID not in (select STATE_ID from ${schema_name}.OAUTH20_TOKEN_CACHE where LIFETIME > (${CURRENT_TIME_SECONDS} - DATE_CREATED/1000))"

db2 terminate
