#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <outputB> <semester> <year>" >&2
  exit 1
fi

output_b="$1"
semester="$2"
year="$3"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$output_b" ] && [ -f "$script_dir/resources/$output_b" ]; then
  output_b="$script_dir/resources/$output_b"
fi

# Header lines (separator, column names, separator) pass through unchanged
head -n 3 "$output_b"

# Filter data lines, sort filtered output by course code
tail -n +4 "$output_b" | awk \
  -v sem="$semester" \
  -v yr="$year" '
BEGIN { ESC = sprintf("%c", 27) }

function strip_ansi(s,    r, i, c, nc) {
  r = ""
  i = 1
  while (i <= length(s)) {
    c = substr(s, i, 1)
    if (c == ESC) {
      nc = substr(s, i+1, 1)
      if (nc == "[") {
        i += 2
        while (i <= length(s) && substr(s, i, 1) !~ /[A-Za-z]/) i++
        i++
      } else if (nc == "(") {
        i += 3
      } else {
        i += 2
      }
    } else {
      r = r c
      i++
    }
  }
  return r
}

function trim(s) {
  gsub(/^[[:space:]]+|[[:space:]]+$/, "", s)
  return s
}

function canon(s) {
  return toupper(trim(s))
}

{
  plain = strip_ansi($0)
  year_val = trim(substr(plain, 1, 20))
  sem_val = trim(substr(plain, 21, 20))
  code_val = trim(substr(plain, 41, 20))

  if (canon(year_val) == canon(yr) && canon(sem_val) == canon(sem)) {
    printf "%s\t%s\n", code_val, $0
  }
}
' | LC_ALL=C sort -t$'\t' -k1,1 | cut -f2-
