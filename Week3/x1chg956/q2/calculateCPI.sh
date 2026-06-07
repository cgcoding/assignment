#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <allCoursesTaken.csv> <letterGradeToNumber.csv>" >&2
  exit 1
fi

courses_file="$1"
grades_file="$2"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$courses_file" ] && [ -f "$script_dir/resources/$courses_file" ]; then
  courses_file="$script_dir/resources/$courses_file"
fi

if [ ! -f "$grades_file" ] && [ -f "$script_dir/resources/$grades_file" ]; then
  grades_file="$script_dir/resources/$grades_file"
fi

awk -F',' '
function trim(s) {
  gsub(/^[[:space:]\r]+|[[:space:]\r]+$/, "", s)
  return s
}

NR == FNR {
  if (FNR == 1) next
  grade = trim($1)
  gp[grade] = trim($2) + 0
  next
}

FNR == 1 { next }

{
  credits = trim($5) + 0
  grade = trim($7)
  if (credits > 0 && grade in gp) {
    total_credits += credits
    total_weighted += credits * gp[grade]
  }
}

END {
  if (total_credits > 0)
    printf "%.4f\n", total_weighted / total_credits
  else
    print "0.0000"
}
' "$grades_file" "$courses_file"
