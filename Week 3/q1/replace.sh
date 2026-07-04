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

# Detect a genuine *call* to init_adapter(), not a bare prototype/declaration.
# A line such as "int init_adapter(struct adapter_config *cfg);" only declares the
# function; the brief (and src/README.txt) require a real call site, so the function
# name must appear at the start of a statement, after `return`/`case`, or after an
# operator/open-paren -- never preceded by a return-type token in a declaration.
has_init_adapter_call() {
  grep -Eq \
    '(^[[:space:]]*init_adapter[[:space:]]*\()|((return|case)[[:space:]]+[^;]*init_adapter[[:space:]]*\()|([-=(,!?:&|+*/<>%][[:space:]]*init_adapter[[:space:]]*\()' \
    "$1"
}

find "$src_root" -type f \( -name "*.c" -o -name "*.h" \) -print0 |
while IFS= read -r -d '' file; do
  if has_init_adapter_call "$file" && grep -q '^#include <oldlib\.h>$' "$file"; then
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
