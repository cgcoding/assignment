#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <allCoursesTaken.csv>" >&2
  exit 1
fi

courses_file="$1"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
awk_script="$script_dir/viewWithoutColor.awk"

if [ ! -f "$courses_file" ] && [ -f "$script_dir/resources/$courses_file" ]; then
  courses_file="$script_dir/resources/$courses_file"
fi

if [ ! -f "$awk_script" ]; then
  echo "viewWithoutColor.awk not found at $awk_script" >&2
  exit 1
fi

if [ "${courses_file##*.}" = "xlsx" ]; then
  echo "Input must be a CSV text file, not .xlsx: $courses_file" >&2
  exit 1
fi

sed 's/\r$//' "$courses_file" | awk -f "$awk_script"
