#!/usr/bin/env bash
# Collects the downloaded JSONs and creates the CantusCorpus format CSV file from
# them. Intended to be run from the directory in which this script resides!
#
# Intended usage:
# ./collect_slurm_results.sh
#     GENRE_NAME

# Make sure there is at least one parameter.
if [ -z $1 ]; then
  echo "ERROR: Not enough parameters"
  exit 1
fi

GENRE_NAME=$1

OUTPUT_DIR='chants_by_genre'
# Make sure the genre subdirectory exists.
_TARGET_DIR_ROOT_NAME='scrapers_by_genre/scraper_slurm_scripts'
TARGET_DIR=${_TARGET_DIR_ROOT_NAME}__${GENRE_NAME}
if [ ! -d $TARGET_DIR ]; then
  echo "ERROR: $TARGET_DIR does not exist"
  exit 2
fi

# Create the collected all_jsons directory in the genre's target dir if it doesn't exist.
mkdir -p ${TARGET_DIR}/all_jsons

# In the TARGET_DIR, there should be subdirectories chunk_0, chunk_1, etc.
# Collect the JSONs from the chunk_${i}/jsons subdirectories.
cp ${TARGET_DIR}/chunk_*/jsons/*.json ${TARGET_DIR}/all_jsons
# Check how many JSONs we got.
N_JSONS=`ls ${TARGET_DIR}/all_jsons | wc -l`
echo "Genre $GENRE_NAME: Collected $N_JSONS JSONs"

# Run the cantus_json_to_csv.py script to create the CantusCorpus CSV file.
# This script is one directory above this script.
CANTUS_JSON_TO_CSV_SCRIPT=cantus_json_to_csv.py
if [ ! -f $CANTUS_JSON_TO_CSV_SCRIPT ]; then
  echo "ERROR: $CANTUS_JSON_TO_CSV_SCRIPT does not exist"
  exit 3
fi

JSON_TO_CSV_OPTS="--treat_filenames_as_cid --allow_no_full_text --allow_no_volpiano -v"
python $CANTUS_JSON_TO_CSV_SCRIPT --input_dir ${TARGET_DIR}/all_jsons \
                                  --output_csv ${OUTPUT_DIR}/${GENRE_NAME}.csv \
                                  ${JSON_TO_CSV_OPTS}

# Check that the CSV file was created.
if [ ! -f ${OUTPUT_DIR}/${GENRE_NAME}.csv ]; then
  echo "ERROR: ${OUTPUT_DIR}/${GENRE_NAME}.csv was not created"
  exit 4
fi

# Check how many lines the CSV file has.
N_CSV_LINES=`wc -l ${OUTPUT_DIR}/${GENRE_NAME}.csv | cut -d ' ' -f 1`
echo "Genre $GENRE_NAME: Created CSV file with $N_CSV_LINES lines"

# Check the first few lines of the CSV file.
echo "First few lines of the CSV file:"
head -n 5 ${OUTPUT_DIR}/${GENRE_NAME}.csv

# Done.
echo "Collecting results for genre $GENRE_NAME: Done."
