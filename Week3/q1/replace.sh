#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <input> <output>" >&2
  exit 1
fi

src_root="$1"
output_dir="$2"
patched_list="$output_dir/patched_files.txt"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$src_root" ]; then
  if [ -d "$script_dir/$src_root" ]; then
    src_root="$script_dir/$src_root"
  elif [ -d "$script_dir/q1_inputs/$src_root" ]; then
    src_root="$script_dir/q1_inputs/$src_root"
  fi
fi

mkdir -p "$output_dir"
: > "$patched_list"

find "$src_root" -type f \( -name "*.c" -o -name "*.h" \) -print0 |
while IFS= read -r -d '' file; do
  if grep -q 'init_adapter[[:space:]]*(' "$file" && grep -q '^#include <oldlib\.h>$' "$file"; then
    sed -i.bak 's|^#include <oldlib.h>$|#include <newlib.h>|' "$file"

    if ! cmp -s "$file.bak" "$file"; then
      printf '%s\n' "$file" >> "$patched_list"
    fi

    rm -f "$file.bak"
  fi
done

if [ -s "$patched_list" ]; then
  LC_ALL=C sort -u "$patched_list" -o "$patched_list"
  awk 'NF > 0' "$patched_list" > "$patched_list.tmp"
  mv "$patched_list.tmp" "$patched_list"
fi
