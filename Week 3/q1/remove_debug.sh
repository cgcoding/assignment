#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <input> <output>" >&2
  exit 1
fi

src_root="$1"
output_dir="$2"
count_file="$output_dir/debug_removed_count.txt"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$src_root" ]; then
  if [ -d "$script_dir/$src_root" ]; then
    src_root="$script_dir/$src_root"
  elif [ -d "$script_dir/q1_inputs/$src_root" ]; then
    src_root="$script_dir/q1_inputs/$src_root"
  fi
fi

mkdir -p "$output_dir"

removed_count="$({
  find "$src_root" -type f \( -name "*.c" -o -name "*.h" \) -print0 |
  while IFS= read -r -d '' file; do
    awk '/^[[:space:]]*\/\/ TEMPDEBUG:/{c++} END{print c+0}' "$file"
  done
} | awk '{s += $1} END{print s+0}')"

find "$src_root" -type f \( -name "*.c" -o -name "*.h" \) -print0 |
while IFS= read -r -d '' file; do
  sed -i.bak '/^[[:space:]]*\/\/ TEMPDEBUG:/d' "$file"
  rm -f "$file.bak"
done

printf '%s\n' "$removed_count" | awk 'NF > 0' > "$count_file"
