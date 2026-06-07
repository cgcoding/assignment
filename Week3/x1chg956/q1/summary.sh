#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <input> <output>" >&2
  exit 1
fi

input_file="$1"
output_dir="$2"
output_file="$output_dir/top_failed_users.txt"
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
/Failed password/ {
  user = ""
  for (i = 1; i <= NF; i++) {
    if ($i == "for") {
      if ($(i + 1) == "invalid" && $(i + 2) == "user") {
        user = $(i + 3)
      } else {
        user = $(i + 1)
      }
      break
    }
  }

  if (user != "") {
    count[user]++
  }
}

END {
  for (u in count) {
    print u, count[u]
  }
}
' "$input_file" | LC_ALL=C sort -k2,2nr -k1,1 | awk 'NF > 0' | head -n 10 > "$output_file"
