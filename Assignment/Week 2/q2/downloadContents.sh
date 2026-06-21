#!/bin/bash

# Usage check
if [ "$#" -ne 2 ]; then
    echo "Usage: ./downloadContents.sh <url> <directory_path>"
    exit 1
fi

URL="$1"
DIR="$2"

# Extract the domain (e.g. "www.example.com") from the URL
DOMAIN=$(echo "$URL" | awk -F/ '{print $3}')

# a. Recursively download pages reachable from URL, restricted to:
#    - same domain (--domains)
#    - no parent directories (--no-parent)
#    - page requisites like CSS/images even outside start dir (--page-requisites)
#    - convert all links to local paths (--convert-links)
#    All files land under DIR preserving the site structure.
wget -q \
    --recursive \
    --no-parent \
    --page-requisites \
    --convert-links \
    --domains "$DOMAIN" \
    --directory-prefix="$DIR" \
    "$URL"

# b. Store the directory tree in JSON format in urlReport.json
tree -J "$DIR" > "$DIR/urlReport.json"

# c. Print the md5sum of urlReport.json (hash only, no filename)
md5sum "$DIR/urlReport.json" | awk '{print $1}'

# d. Count '{' (open curly braces) using tr and print on a new line
#    tr -cd '{' keeps only '{' characters; wc -c counts them
COUNT=$(tr -cd '{' < "$DIR/urlReport.json" | wc -c)
echo "$COUNT"

# e. If a process with PID == COUNT exists, print its COMMAND column value
#    from ps aux; otherwise print "No such process"
PROC=$(ps aux | awk -v pid="$COUNT" 'NR>1 && $2==pid {print $11}')
if [ -z "$PROC" ]; then
    echo "No such process"
else
    echo "$PROC"
fi
