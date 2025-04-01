#!/bin/bash

# Run collect_slurm_scripts.sh for all genre


# Define genre file
CSV_FILE="static/genre.csv"

# Output folder
FOLDER_NAME="chants_by_genre"

# Extract the second column, remove duplicates, and iterate over them
cut -d',' -f2 "$CSV_FILE" | tail -n +2 | sort -u | while read -r genre; do
    FILE_PATH="${FOLDER_NAME}/${genre}.txt"
    DIR_NAME="$scraper_slurm_scripts__$genre"

        bash collect_slurm_results.sh "$genre"
done
