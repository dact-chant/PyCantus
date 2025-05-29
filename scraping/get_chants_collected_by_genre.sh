#!/bin/bash

# Run collect_slurm_results.sh for all genre


# Define genre file
CSV_FILE="static/genre.csv"

# Output folder
FOLDER_NAME="chants_by_genre"
mkdir -p $FOLDER_NAME

# Extract the second column, remove duplicates, and iterate over them
cut -d',' -f1 "$CSV_FILE" | tail -n +2 | sort -u | while read -r genre; do
    echo "$genre"

    bash collect_slurm_results.sh "$genre"
done
