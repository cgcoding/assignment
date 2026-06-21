#!/bin/bash

# Usage check
if [ "$#" -ne 2 ]; then
    echo "Usage: ./pdfWordCounter.sh <URL> <Word>"
    exit 1
fi

URL="$1"
WORD="$2"

# Derive a filename from the URL
FILENAME=$(basename "$URL")

# a. Download the PDF quietly
wget -q "$URL" -O "$FILENAME"

# b. Convert PDF to text (stdout only, no temp file) and count whole-word,
#    case-insensitive occurrences of WORD.
#    -o  : print only the matching part (one match per line)
#    -w  : whole-word match  (so "break." matches but "breakfast" does not)
#    -i  : case-insensitive
COUNT=$(pdftotext "$FILENAME" - | grep -owi "$WORD" | wc -l)

# c. Delete the downloaded PDF
rm -f "$FILENAME"

# d. Print the count
echo "$COUNT"
