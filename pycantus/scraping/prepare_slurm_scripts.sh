#!/usr/bin/env bash
# Prepare SLURM scripts for scraping Cantus Index JSON dumps
# for one file with CIDs.
#
# Intended usage:
# ./prepare_slurm_scripts.sh
#     GENRE_NAME
#     FILE_WITH_CIDS
#     N_CIDS_PER_JOB
#
# GENRE_NAME: abbreviation of the genre, e.g. "In" for introits. This script should
#             only be run once with a given GENRE_NAME, as it creates a subdirectory
#             and chunk numbering for the genre.
# FILE_WITH_CIDS: path to the file with CIDs of the given genre to scrape.
# N_CIDS_PER_JOB: number of CIDs per one SLURM job.
#
# All three parameters are required.
#
# Example usage:
#
# ./prepare_slurm_scripts.sh In cid_lists_by_genre/In.txt 100

# Configuration of the scrape_ci_jsons.sh script:
_CONF_TARGET_DIR='jsons'
_CONF_SLEEP_TIME=5
_CONF_FORCE_REFRESH=1
_CONF_STDOUT_LOG='log-scrape-ci-jsons.out'
_CONF_STDERR_LOG='log-scrape-ci-jsons.err'

# Make sure there are at least the three required parameters.
if [ -z $3 ]; then
  echo "ERROR: Not enough parameters"
  exit 1
fi

GENRE_NAME=$1
FILE_WITH_CIDS=$2
N_CIDS_PER_JOB=$3

# Check that file with CIDs exists.
if [ ! -f $FILE_WITH_CIDS ]; then
  echo "ERROR: $FILE_WITH_CIDS does not exist"
  exit 2
fi

# Check that the genre directory does not exist yet.
_TARGET_DIR_ROOT_NAME='scrapers_by_genre/scraper_slurm_scripts'
TARGET_DIR=${_TARGET_DIR_ROOT_NAME}__${GENRE_NAME}
if [ -d $TARGET_DIR ]; then
  echo "ERROR: $TARGET_DIR already exists"
  exit 3
fi

# Create target directory that will contain the prepared scripts.
mkdir -p $TARGET_DIR

# Count the number of CIDs in the file.
N_CIDS=`wc -l $FILE_WITH_CIDS | cut -d ' ' -f 1`
echo "Found $N_CIDS CIDs in $FILE_WITH_CIDS"

# Calculate the number of chunks.
N_CHUNKS=$((N_CIDS / N_CIDS_PER_JOB))
if [ $((N_CIDS % N_CIDS_PER_JOB)) -ne 0 ]; then
  N_CHUNKS=$((N_CHUNKS + 1))
fi
echo "Will create $N_CHUNKS chunks"

# Each chunk gets processed in its own subdirectory.
# Create that subdirectory and save the corresponding chunk of CIDs there.
for ((i=0; i<N_CHUNKS; i++)); do
  CHUNK_DIR=${TARGET_DIR}/chunk_${i}
  mkdir -p $CHUNK_DIR
  START=$((i * N_CIDS_PER_JOB + 1))
  END=$((START + N_CIDS_PER_JOB - 1))
  if [ $END -gt $N_CIDS ]; then
    END=$N_CIDS
  fi
  sed -n "${START},${END}p" $FILE_WITH_CIDS > ${CHUNK_DIR}/cids.txt
  echo "Created ${CHUNK_DIR}/cids.txt with CIDs ${START}-${END} out of $N_CIDS with `wc -l ${CHUNK_DIR}/cids.txt` lines."
done

# For each chunk, copy the scrape_ci_jsons.sh script into its directory.
# This is preventative: if we change the directory structure of this scraping process,
# we won't have to worry about depending on any relative paths between this directory
# and the chunk scripts.
for ((i=0; i<N_CHUNKS; i++)); do
  CHUNK_DIR=${TARGET_DIR}/chunk_${i}
  cp scrape_ci_jsons.sh ${CHUNK_DIR}
  chmod +x ${CHUNK_DIR}/scrape_ci_jsons.sh
done

_ABS_TARGET_DIR=`realpath $TARGET_DIR`

# For each chunk, create a SLURM wrapper that runs the scrape_ci_jsons.sh script
# in its subdirectory. The generated script is supposed to be run *from its own directory*.
for ((i=0; i<N_CHUNKS; i++)); do
  CHUNK_DIR=${TARGET_DIR}/chunk_${i}
  SLURM_SCRIPT=${CHUNK_DIR}/slurm_wrapper.sh
  echo "#!/usr/bin/env bash" > $SLURM_SCRIPT
  echo "#SBATCH --job-name=ci_scrape_${GENRE_NAME}_${i}" >> $SLURM_SCRIPT
  echo "#SBATCH --partition=cpu-troja" >> $SLURM_SCRIPT
  echo "#SBATCH --output=wrapper_logs/log-cid-scrape-wrapper.%x.%j.out" >> $SLURM_SCRIPT
  echo "#SBATCH --error=wrapper_logs/log-cid-scrape-wrapper.%x.%j.err" >> $SLURM_SCRIPT
  echo "#SBATCH --time=24:00:00" >> $SLURM_SCRIPT
  echo "#SBATCH --mem=1G" >> $SLURM_SCRIPT
  echo "" >> $SLURM_SCRIPT
  echo "cd ${_ABS_TARGET_DIR}/chunk_${i}" >> $SLURM_SCRIPT
  echo "mkdir -p ${_CONF_TARGET_DIR}" >> $SLURM_SCRIPT
  echo "./scrape_ci_jsons.sh cids.txt ${_CONF_TARGET_DIR} ${_CONF_SLEEP_TIME} ${_CONF_FORCE_REFRESH} >${_CONF_STDOUT_LOG} 2>${_CONF_STDERR_LOG}" >> $SLURM_SCRIPT
done
