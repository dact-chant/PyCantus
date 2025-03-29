#!/bin/bash

# Intended usage:
# ./scrape_ci_jsons.sh FILE_WITH_CIDS TARGET_DIR SLEEP_TIME FORCE_REFRESH


# URL that serves Cantus Index JSON dumps.
CID_URL_PREFIX=https://cantusindex.org/json-cid

# URL on which to ask for Cantus Index to refresh its CSV file.
REFRESH_URL_SUFFIX='?nocache=$(date +%s)'
REFRESH_URL_PREFIX=https://cantusindex.org/json-cid

# List of chants to scrape in cantuscorpus-like CSV format. First column is Cantus ID.
FILE_WITH_CIDS=../all_ci_introits_list.csv
if [ ! -z $1 ]; then
  FILE_WITH_CIDS=$1
fi
if [ ! -f $FILE_WITH_CIDS ]; then
  echo "ERROR: $FILE_WITH_CIDS does not exist"
  exit 1
fi

# Directory into which to save the JSON files.
TARGET_DIR=.
if [ ! -z $2 ]; then
  TARGET_DIR=$2
fi
if [ ! -d $TARGET_DIR ]; then
  echo "ERROR: $TARGET_DIR does not exist"
  exit 2
fi

SLEEP_TIME=1
if [ ! -z $3 ]; then
  SLEEP_TIME=$3
fi

FORCE_REFRESH=
if [ ! -z $4 ]; then
  FORCE_REFRESH=$4
fi

### Now we have parameters loaded, execution starts.

# Create the target directory if it doesn't exist
mkdir -p ${TARGET_DIR}

for CID in `cut -d ',' -f 1 $FILE_WITH_CIDS`; do
  CID=$(echo "$CID" | sed 's/\r$//')
  
  echo "Processing CID ${CID}"

  # Force Cantus Index refresh>
  if [ ! -z $FORCE_REFRESH ]; then
    REFRESH_URL="${REFRESH_URL_PREFIX}/${CID}${REFRESH_URL_SUFFIX}"
    echo "...Refreshing ${CID} with ${REFRESH_URL}"
    curl -k $REFRESH_URL > /dev/null
  fi

  # Get JSON dump from after the refresh
	PREFIX=`echo $CID | cut -c1-3`
  # ${PREFIX}/${CID}/all.json"
	URL="${CID_URL_PREFIX}/${CID}"

	echo $URL
	echo "...Downloading ${CID} from ${URL}"
	curl -k $URL > ${TARGET_DIR}/${CID}.json


  if [ ! -s ${TARGET_DIR}/${CID}.json ]; then
    echo "ERROR: ${TARGET_DIR}/${CID}.json is empty -- could not download JSON for CID ${CID}"
  fi

	# Delay to prevent overloading Cantus Index
	sleep $SLEEP_TIME
done


