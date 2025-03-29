#!/bin/bash

# Run prepare_slurm_scripts.sh for all genre


# Define genre file
CSV_FILE="static/genre.csv"

# Output folder
FOLDER_NAME="cids_lists_by_genre"

# Extract the second column, remove duplicates, and iterate over them
cut -d',' -f2 "$CSV_FILE" | tail -n +2 | sort -u | while read -r genre; do
    FILE_PATH="${FOLDER_NAME}/${genre}.txt"
    DIR_NAME="$scraper_slurm_scripts__$genre"

    # Check if file already exists
    #if [ ! -d "$DIR_NAME" ]; then
        bash prepare_slurm_scripts.sh "$genre" "$FILE_PATH" 100
    #else
    #    echo "Skipping: $genre scripts already exists."
    #fi
done
