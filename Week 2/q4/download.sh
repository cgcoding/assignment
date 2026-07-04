#!/bin/bash

# Usage check
if [ "$#" -ne 2 ]; then
    echo "Usage: ./download.sh <link to directory> <cut-dirs argument>"
    exit 1
fi

URL="$1"
CUT_DIRS="$2"

# Directory where this script lives — downloaded content goes here
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

ONLINE_DIR_NAME=$(basename "${URL%/}")

# Download into an isolated temporary tree under SCRIPT_DIR, then extract exactly
# the requested directory. This avoids fragile --cut-dirs path handling.
TMP_ROOT="$SCRIPT_DIR/.download_tmp_$$"
mkdir -p "$TMP_ROOT"

wget -q \
    --recursive \
    --no-parent \
    --reject "index.html*" \
    --reject "*.tmp" \
    -P "$TMP_ROOT" \
    "$URL/"

# Locate the downloaded target directory anywhere in wget's mirror tree.
DOWNLOADED_DIR=$(find "$TMP_ROOT" -type d -name "$ONLINE_DIR_NAME" -print | head -1)

if [ -z "$DOWNLOADED_DIR" ] || [ ! -d "$DOWNLOADED_DIR" ]; then
    rm -rf "$TMP_ROOT"
    echo "Download failed: could not locate '$ONLINE_DIR_NAME' in downloaded data"
    exit 1
fi

rm -rf "$SCRIPT_DIR/mock_grading"
mv "$DOWNLOADED_DIR" "$SCRIPT_DIR/mock_grading"
rm -rf "$TMP_ROOT"

# Keep CUT_DIRS accepted for compatibility with the original assignment CLI.
:
