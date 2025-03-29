#!/usr/bin/env bash
# Runs the prepared slurm scripts for scraping Cantus Index JSONs.
# Intended to be run after prepare_slurm_scripts.sh, at a SLURM head node.
# Does nothing except running sbatch for each prepared script
# for a given genre.
#
# Intended usage:
# ./run_slurm_scripts.sh GENRE_NAME

# Make sure there is at least one parameter.
if [ -z $1 ]; then
  echo "ERROR: Not enough parameters"
  exit 1
fi

GENRE_NAME=$1
echo "Submitting SLURM scripts for genre: $GENRE_NAME"

# Make sure the genre subdirectory exists.
_TARGET_DIR_ROOT_NAME='scrapers_by_genre/scraper_slurm_scripts'
TARGET_DIR=${_TARGET_DIR_ROOT_NAME}__${GENRE_NAME}
if [ ! -d $TARGET_DIR ]; then
  echo "ERROR: $TARGET_DIR does not exist"
  exit 2
fi

# In the TARGET_DIR, there should be subdirectories chunk_0, chunk_1, etc.
# Run the prepared scripts in the chunk_${i} subdirectories.
for CHUNK_DIR in `ls ${TARGET_DIR} | grep chunk`; do
  SCRIPT=${TARGET_DIR}/${CHUNK_DIR}/slurm_wrapper.sh
  # Check that the wrapper script exists.
  if [ ! -f $SCRIPT ]; then
    echo "ERROR: $SCRIPT does not exist"
    exit 3
  fi
  echo "Submitting SLURM wrapper: $SCRIPT"
  sbatch $SCRIPT
done

# Check how many jobs are running.
squeue -u $USER

