#!/bin/bash

# Usage check — this script takes no arguments
if [ "$#" -ne 0 ]; then
    echo "Usage: organise.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MOCK_DIR="$SCRIPT_DIR/mock_grading"
SUBMISSIONS_DIR="$MOCK_DIR/submissions"
ROLL_LIST="$MOCK_DIR/roll_list"
ORGANISED_DIR="$SCRIPT_DIR/organised"

# Create the top-level organised/ directory
mkdir -p "$ORGANISED_DIR"

# For each roll number listed in roll_list:
#   1. Create a subdirectory organised/<roll>/
#   2. For every file in submissions/ whose name starts with that roll number,
#      create a RELATIVE symbolic link inside the student's directory.
#      The relative path from organised/<roll>/ back to submissions/ is
#      ../../mock_grading/submissions/
while IFS= read -r roll; do
    # Skip blank lines
    [ -z "$roll" ] && continue

    mkdir -p "$ORGANISED_DIR/$roll"

    # Find all files submitted by this student
    for filepath in "$SUBMISSIONS_DIR/${roll}"*; do
        # Guard: only process regular files (glob may not match anything)
        [ -f "$filepath" ] || continue

        filename=$(basename "$filepath")

        # ln -sf TARGET LINK
        # TARGET is relative to the directory that contains the link, i.e. organised/<roll>/
        ln -sf "../../mock_grading/submissions/$filename" \
               "$ORGANISED_DIR/$roll/$filename"
    done
done < "$ROLL_LIST"
