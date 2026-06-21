#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <outputA> <creditsRequirements.csv>" >&2
  exit 1
fi

output_a="$1"
credits_file="$2"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
credits_dir="$(cd "$(dirname "$credits_file")" && pwd)"

if [ ! -f "$output_a" ] && [ -f "$script_dir/resources/$output_a" ]; then
  output_a="$script_dir/resources/$output_a"
fi

if [ ! -f "$credits_file" ] && [ -f "$script_dir/resources/$credits_file" ]; then
  credits_file="$script_dir/resources/$credits_file"
  credits_dir="$script_dir/resources"
fi

if [ -f "$credits_dir/defineColors.sh" ]; then
  # shellcheck source=/dev/null
  . "$credits_dir/defineColors.sh"
elif [ -f "$script_dir/resources/defineColors.sh" ]; then
  # shellcheck source=/dev/null
  . "$script_dir/resources/defineColors.sh"
elif [ -f "$script_dir/../resources/defineColors.sh" ]; then
  # shellcheck source=/dev/null
  . "$script_dir/../resources/defineColors.sh"
else
  echo "defineColors.sh not found next to credits file or in q2/resources" >&2
  exit 1
fi

sed 's/\r$//' "$output_a" | awk -F',' \
  -v RED_FONT="${RED_FONT:-}" \
  -v GREEN_FONT="${GREEN_FONT:-}" \
  -v YELLOW_FONT="${YELLOW_FONT:-}" \
  -v BLUE_FONT="${BLUE_FONT:-}" \
  -v MAGENTA_FONT="${MAGENTA_FONT:-}" \
  -v CYAN_FONT="${CYAN_FONT:-}" \
  -v WHITE_FONT="${WHITE_FONT:-}" \
  -v BLACK_FONT="${BLACK_FONT:-}" \
  -v RED_BACKGROUND="${RED_BACKGROUND:-}" \
  -v GREEN_BACKGROUND="${GREEN_BACKGROUND:-}" \
  -v YELLOW_BACKGROUND="${YELLOW_BACKGROUND:-}" \
  -v BLUE_BACKGROUND="${BLUE_BACKGROUND:-}" \
  -v MAGENTA_BACKGROUND="${MAGENTA_BACKGROUND:-}" \
  -v CYAN_BACKGROUND="${CYAN_BACKGROUND:-}" \
  -v WHITE_BACKGROUND="${WHITE_BACKGROUND:-}" \
  -v BLACK_BACKGROUND="${BLACK_BACKGROUND:-}" \
  -v RESET_ALL="${RESET_ALL:-}" '

function trim(s) {
  gsub(/^[[:space:]]+|[[:space:]]+$/, "", s)
  return s
}

function canon(s) {
  s = toupper(trim(s))
  gsub(/[[:space:]-]+/, "_", s)
  return s
}

function font_code(name, n) {
  n = canon(name)
  if (n == "RED" || n == "RED_FONT") return RED_FONT
  if (n == "GREEN" || n == "GREEN_FONT") return GREEN_FONT
  if (n == "YELLOW" || n == "YELLOW_FONT") return YELLOW_FONT
  if (n == "BLUE" || n == "BLUE_FONT") return BLUE_FONT
  if (n == "MAGENTA" || n == "MAGENTA_FONT") return MAGENTA_FONT
  if (n == "CYAN" || n == "CYAN_FONT") return CYAN_FONT
  if (n == "WHITE" || n == "WHITE_FONT") return WHITE_FONT
  if (n == "BLACK" || n == "BLACK_FONT") return BLACK_FONT
  return ""
}

function bg_code(name, n) {
  n = canon(name)
  if (n == "RED" || n == "RED_BACKGROUND") return RED_BACKGROUND
  if (n == "GREEN" || n == "GREEN_BACKGROUND") return GREEN_BACKGROUND
  if (n == "YELLOW" || n == "YELLOW_BACKGROUND") return YELLOW_BACKGROUND
  if (n == "BLUE" || n == "BLUE_BACKGROUND") return BLUE_BACKGROUND
  if (n == "MAGENTA" || n == "MAGENTA_BACKGROUND") return MAGENTA_BACKGROUND
  if (n == "CYAN" || n == "CYAN_BACKGROUND") return CYAN_BACKGROUND
  if (n == "WHITE" || n == "WHITE_BACKGROUND") return WHITE_BACKGROUND
  if (n == "BLACK" || n == "BLACK_BACKGROUND") return BLACK_BACKGROUND
  return ""
}

BEGIN {
  tag_col = 0
  fg_col = 0
  bg_col = 0
}

NR == FNR {
  if (FNR == 1) {
    for (i = 1; i <= NF; i++) {
      h = canon($i)
      if (h == "TAG") tag_col = i
      if (h == "FONT" || h == "TEXT_COLOR" || h == "FG" || h == "FONT_COLOR" || h == "COLOR_FONT" || h == "COLOR") fg_col = i
      if (h == "BACKGROUND" || h == "BG" || h == "BACKGROUND_COLOR" || h == "COLOR_BACKGROUND") bg_col = i
    }
    next
  }

  if (tag_col == 0) next

  tag = trim($tag_col)
  fg = (fg_col > 0) ? trim($(fg_col)) : ""
  bg = (bg_col > 0) ? trim($(bg_col)) : ""

  if (tag != "") {
    tag_fg[tag] = fg
    tag_bg[tag] = bg
  }
  next
}

{
  # Preserve separators/header and colorize only course rows.
  if (FNR <= 3) {
    print $0
    next
  }

  tag = trim(substr($0, 81, 20))
  fg = font_code(tag_fg[tag])
  bg = bg_code(tag_bg[tag])

  if (fg != "" || bg != "") {
    print bg fg $0 RESET_ALL
  } else {
    print $0
  }
}
' "$credits_file" -
