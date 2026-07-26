BEGIN {
  FS = ","
  OFS = ""
  width = 20
  line = ""
  semester_filter_norm = toupper(trim(semester_filter))
}

function trim(s) {
  gsub(/^[[:space:]]+|[[:space:]]+$/, "", s)
  return s
}

NR == 1 {
  # Separator width must be 20 * number of displayed fields.
  cols = NF - 1  # Drop the Name column from display.
  line = ""
  for (i = 1; i <= width * cols; i++) {
    line = line "-"
  }

  print line
  printf "%20s%20s%20s%20s%20s%20s\n", "Year", "Semester", "Code", "Credits", "Tag", "letterGrade"
  print line
  next
}

{
  year = trim($1)
  semester = trim($2)
  code = trim($3)
  credits = trim($5)
  tag = trim($6)
  grade = trim($7)

  if (semester_filter_norm != "" && toupper(semester) != semester_filter_norm) {
    next
  }

  printf "%20s%20s%20s%20s%20s%20s\n", year, semester, code, credits, tag, grade
}
