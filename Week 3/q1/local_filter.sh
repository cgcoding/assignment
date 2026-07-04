#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <input> <output>" >&2
  exit 1
fi

input_file="$1"
output_dir="$2"
output_file="$output_dir/error_lines.txt"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$input_file" ]; then
  if [ -f "$script_dir/$input_file" ]; then
    input_file="$script_dir/$input_file"
  elif [ -f "$script_dir/q1_inputs/$input_file" ]; then
    input_file="$script_dir/q1_inputs/$input_file"
  fi
fi

mkdir -p "$output_dir"

awk '
/ERROR/ {
  date = $1
  time = $2
  code = ""

  for (i = 1; i <= NF; i++) {
    if ($i ~ /^code=/) {
      code = $i
      sub(/^code=/, "", code)
      gsub(/[^[:alnum:]_:-]/, "", code)
      break
    }
  }

  if (date != "" && time != "" && code != "") {
    print date, time, code
  }
}
' "$input_file" | awk 'NF > 0' > "$output_file"
