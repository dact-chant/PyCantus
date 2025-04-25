#!/bin/bash

# For all genre from list in "static/genre.csv" file we collect
# associated Cantus IDs into cids_lists_by_genre folder with
# name in format GENRE.txt


# Define genre file
CSV_FILE="static/genre.csv"
# Output folder
FOLDER_NAME="cids_lists_by_genre"

# Extract the second column, remove duplicates, and iterate over them
cut -d',' -f2 "$CSV_FILE" | tail -n +2 | sort -u | while read -r genre; do
    FILE_PATH="${FOLDER_NAME}/${genre}.txt"

    # Check if file already exists
    if [ ! -f "$FILE_PATH" ]; then
        python scrape_cid_values.py -g "$genre" -o "$FILE_PATH"
    else
        echo "Skipping: $FILE_PATH already exists."
    fi
done