# sed and awk - Comprehensive Study Notes

> Distilled from the 41-slide *Week 3: Sed and Awk* deck (Amitabha Sanyal), organized around
> what the assignment actually tests. Use this as the concept reference; use
> `ASSIGNMENT-APPROACH.md` for the step-by-step solving guide.

`sed` and `awk` are *stream processors*: they read input one line at a time, run a small
program against each line, and emit a transformed stream. Neither loads the whole file into
memory, so both run in (near) constant space and slot naturally into Unix pipelines. The
mental model for both tools is the same **read-a-line / run-the-script / print** loop; the
difference is what the script can express:

1. **`sed`** - a *stream editor*. Its script is a list of `[address] command` pairs that
   edit the line held in the **pattern space**. Best for surgical, one-shot text edits
   (substitute, delete, insert, move lines between files).
2. **`awk`** - a *pattern-action language*. It splits each line into **fields**, matches the
   record against **patterns**, and runs **actions** (a small C-like language with variables,
   arrays, arithmetic, and `printf`). Best for field extraction, aggregation, and formatted
   reports.

This document follows that split: the `sed` model and its command families first, then the
`awk` model, its patterns, and its actions.

---

## 0. How the lecture maps to the assignment

| Deck topic | Slides | Assignment task it supports |
|---|---|---|
| The `sed` model: pattern/hold space, the cycle, invocation | 1-3 | All `sed` tasks (`replace.sh`, `remove_debug.sh`) |
| Script structure, addresses (single / set / range / nested / `!`) | 4-6 | `sed-a` (match only the right files), `sed-b` (match marker lines) |
| Line command `=` | 8 | Counting (background for `sed-b` count) |
| Modify commands `i a c d` | 9-10 | `sed-b` (`d` to delete debug lines) |
| Substitute `s///`, back-refs `&` and `\1`, transform `y///` | 11-13 | `sed-a` (`s` to swap the include line) |
| IO / flow: `n N`, `p P`, `h H g G x`, `r w`, `b q`, revised workflow | 14-22 | `sed` robustness; `viewWithColor.sh` post-processing |
| The `awk` model: cycle, fields, records, `$0..$n` | 23-26 | All `awk` tasks (field extraction) |
| Predefined variables `FS RS NF NR OFS ORS FILENAME` | 27 | `awk-1/2/3` field picking; `FNR`/`NR` in `viewWithColor.sh` |
| Program structure `BEGIN { } pattern { } END { }` | 28-30 | `viewWithoutColor.awk`, `calculateCPI.sh` |
| Pattern types: match `~ !~`, expressions, range | 31-34 | `awk-1/2/3` (`/Failed password/`, `/ERROR/`) |
| Actions: variables, `-v`, associative arrays, `print/printf/sprintf` | 35-39 | `summary.sh` frequency table, formatted printing |
| Decisions and loops (`if`, `for`, `while`, `break/continue`) | 40-41 | Field-walking loops, the formatted-report example |

The assignment's two halves line up with the two tools: **Q1** drills `awk` field
extraction + `sed` one-shot edits over a log/source tree; **Q2** drills `awk` formatted
reports + `sed`/`awk` colorization over CSV course data.

---

## 1. The sed model

### 1.1 Two buffers and one cycle

`sed` is a **stream editor**. It maintains two buffers:

- **pattern space** - holds the current line being processed.
- **hold space** - a scratch buffer that survives *between* cycles, used to accumulate or
  shuffle text (`h H g G x`).

The cycle, repeated until input is exhausted:

```
Until all lines are read:
  1. read the next input line into the PATTERN SPACE
  2. run the script (every [address] command) against the pattern space
  3. transfer the pattern space to the output stream  (unless -n suppresses it)
```

### 1.2 Invocation

```
sed [options] 'script' input_files
sed [options] -f script_file input_files
```

- **inlined**: `sed 'script' file` - the script is the argument.
- **from a file**: `sed -f script_file file` - read the program from `script_file`.

### 1.3 Common options

| Option | Meaning |
|---|---|
| `-n` | Do **not** auto-print the pattern space; output only on an explicit `p`/`P`. |
| `-f scriptfile` | Read the script from a file. |
| `-s` | Treat each input file separately (else commands run on the *concatenation*). |
| `-r` (`-E`) | Use **extended** regular expressions (no backslash before `( ) { } +`). |
| `-i[.bak]` | Edit **in place**; with a suffix, keep a backup (`file.bak`). |

```bash
sed -n '/Deceased/p' covid_data.csv          # -n + p: print only matching lines
sed -n -s '1,10 p' Students.csv covid.csv     # first 10 lines of EACH file
sed -n -r '/19D[0-9]{6}/ p' Students.csv       # extended regex address
```

---

## 2. sed addresses

A script is a sequence of:

```
[address] [!] command
```

A **missing address** means *all lines*. `!` **negates** the address (all lines *except*
those matched).

### 2.1 Single-line address

```bash
sed -n '3 p' Students.csv                      # only line 3
sed -n '$ p' Students.csv                       # only the last line ($)
sed -n -e '10 s/HW/ML/' -e '10 p' Students.csv  # -e chains commands
```

### 2.2 Set-of-lines address (regular expression)

```bash
sed -n -r '/19D[0-9]{6}/ p' Students.csv        # every line matching the regex
ls -al | sed -n '/^d/ p'                          # directories (lines starting with d)
```

### 2.3 Range address

```bash
sed -n '1,10 p' spy.py                # lines 1..10
sed -n '/^if/,10 p' spy.py            # from first /^if/ through line 10
sed -n '/^if/,/^else/ p' spy.py       # from an if to its closest else
```

### 2.4 Nested and complemented addresses

```bash
sed -n '20,30{/print/ p}'  spy.py     # print statements within lines 20..30
sed -n '20,30{/print/! p}' spy.py     # NON-print statements within 20..30  (! = negate)
```

> The `{ ... }` block applies the inner command(s) only to lines already selected by the
> outer address - this is how you combine a *line range* with a *content match*, which is
> exactly the kind of precision `sed-a`/`sed-b` need.

---

## 3. sed commands

### 3.1 Line-number command `=`

Prints the **line numbers** of matching lines (not their text):

```bash
sed -n '20,30{/print/! =}' spy.py     # line numbers of non-print lines in 20..30
```

### 3.2 Modify commands `i a c d`

| Cmd | Name | Behaviour |
|---|---|---|
| `i` | insert | Send text to output **immediately**, before the addressed line. |
| `a` | append | Queue text to be output **after** the current cycle ends. |
| `c` | change | Delete the pattern space, output the replacement text, start the next cycle. |
| `d` | delete | Delete the pattern space and **immediately start the next cycle**. |

```bash
sed '1 i 2019 Batch' Students.csv                      # insert a line before line 1
sed -n -r -e '/19D[0-9]{6}/ c Dual Degree Student' Students.csv   # change matched lines
```

`d` is the workhorse for *removing* lines (used by `sed-b` to drop `// TEMPDEBUG:` markers).

### 3.3 Substitute command `s`

```
s/search/replace/[flags]
```

- `search` is a regular expression; `replace` is the replacement text.
- **flags**: `g` (global - all occurrences on the line), an integer (replace the *n*-th
  occurrence), `p` (print), `w file` (write), `i` (case-insensitive).

```bash
sed -r 's/\"//g' Students.csv          # delete every double-quote on each line
```

**Back-references in the replacement:**

- `&` - the entire text matched by `search`.
- `\1`, `\2`, ... - the text matched by the *n*-th `\(...\)` group (parentheses in `-r`).

```bash
# & : append a domain to every roll number
sed -r 's/19[0-9A-Z]{7}/&@iitb.ac.in/' Students.csv

# \1 \2 : swap the roll-number and name columns
sed -r 's/("19[0-9A-Z]{7}"),("[ a-zA-Z]*")/\2,\1/' Students.csv
```

> The single-anchored substitution `s/^#include <oldlib.h>$/#include <newlib.h>/` is the
> core of `sed-a`: anchor with `^...$` so you replace the whole line and nothing partial.

### 3.4 Transform command `y`

```
y/listOfChars1/listOfChars2/
```

Character-by-character transliteration (like `tr`); the two lists **must be the same
length**.

```bash
sed '1,4 y/BD/bd/' Students.csv        # on lines 1..4: B->b, D->d
```

---

## 4. sed IO and flow control

### 4.1 Multi-line input: `n` and `N`

- **`n`** - finish the current line (auto-print it unless `-n`), read the **next** line into
  the pattern space, continue with the next command.
- **`N`** - **append** the next input line to the pattern space (with an embedded `\n`), so
  two lines can be processed together.

```bash
sed 'n; n; a ------------'         # print a dashed line after every 3rd line
sed -r 'N; s/\n//g' Students.csv   # join adjacent line pairs (strip the newline)
```

### 4.2 Printing: `p` and `P`

- **`p`** - print the **entire** pattern space (prints twice unless `-n`).
- **`P`** - print only **up to and including the first newline** (the first of a multi-line
  pattern space).

```bash
sed -n 'N; p' Students.csv | wc -l   # 146  (p prints both joined lines)
sed -n 'N; P' Students.csv | wc -l   #  73  (P prints only the first)
```

### 4.3 Hold space: `h H g G x`

| Cmd | Effect |
|---|---|
| `h` | `hold := pattern`  (copy pattern -> hold) |
| `H` | `hold := hold + "\n" + pattern`  (append) |
| `g` | `pattern := hold`  (copy hold -> pattern) |
| `G` | `pattern := pattern + "\n" + hold`  (append) |
| `x` | exchange (swap) pattern and hold spaces |

```bash
# move all dual-degree students to the end of the file
sed -r -e '/19D[0-9]{6}/ H' -e '/19D[0-9]{6}/ d' -e '$ G' Students.csv
```

In a script file (run as `sed -r -f scriptfile Students.csv`); the braces and the commands
must be on **separate lines**:

```sed
/19D[0-9]{6}/ {
  H
  d
}
$ {
  G
}
```

### 4.4 The revised sed workflow (the real execution model)

```
hold_space := empty
while read_next_line(input, pattern_space) do
    append_queue := empty
    while there are more commands cmd do
        if address_matches(cmd, pattern_space)
            case opcode(cmd) of
              's' : apply substitution to pattern space
              'p' : output(pattern_space)
              'i' : output(cmd.text)                      # immediate
              'a' : append_queue.enqueue(cmd.text)        # deferred
              'd' : goto END_CYCLE
              'c' : output(cmd.text); goto END_CYCLE
              'n' : if auto_print then output(pattern_space)
                    flush(append_queue)
                    if not read_next_line(...) goto STOP
              'N' : if not read_next_line(input, next_line) goto STOP
                    else pattern_space := pattern_space + "\n" + next_line
    if auto_print then output(pattern_space)
    END_CYCLE: flush(append_queue)
STOP:
```

Key consequences: `i` text appears immediately, `a` text is flushed at end-of-cycle, and
`d`/`c` short-circuit the rest of the script.

### 4.5 File IO: `r` and `w`

- **`r filename`** - read `filename` and copy it to the **output stream** (not the pattern
  space).
- **`w filename`** - write the pattern space to `filename`.

```bash
sed '$ r extras.csv' Students.csv                      # append a file at the end
sed -r -n '/19D[0-9]{6}/ w dd-students.csv' Students.csv # write matches to a file
```

### 4.6 Branching and quitting: `b` and `q`

- **`b label`** - branch (unconditionally) to `:label`, or to end-of-script if no label.
- **`q`** - quit `sed`.

```sed
/19D[0-9]{6}/ b save
w others.csv
b
:save
w dd-students.csv
```

```bash
sed '50q' datafile     # print the first 50 lines, then quit
```

---

## 5. The awk model

### 5.1 What awk is

Named after **A**ho, **W**einberger and **K**ernighan. A scripting language for manipulating
data and generating reports. The **awk cycle**:

```
- scan the file line by line
- split each input line into FIELDS
- compare the line / fields against PATTERNS
- run ACTION(s) on matched lines
```

Best for *transforming* data files and producing *formatted reports*.

### 5.2 Fields and records

- A **field** is a unit of data; fields are separated by the **field separator** (default:
  whitespace).
- A **record** is the whole line (`$0`); fields are `$1 $2 ... $NF`.
- A **data file** is a sequence of records.

```
record  $0 : "190050339","Kandibanda Sai","ML","Advisor : Prof. Dilip Jain"
fields  $1   $2                  $3      $4   (with FS=",")
```

### 5.3 Invocation

```
awk [options] 'script' file(s)
awk [options] -f scriptfile file(s)
```

| Option | Meaning |
|---|---|
| `-F sep` | set the input field separator (e.g. `-F,` for CSV) |
| `-f file` | read the program from a file |
| `-v name=val` | set an awk variable **before** processing (see scope, below) |

### 5.4 Predefined variables

| Var | Meaning |
|---|---|
| `FS` | input field separator (default: whitespace) |
| `RS` | record separator (default: `\n`) |
| `NF` | number of fields in the current record |
| `NR` | number of the current record (across all files) |
| `FNR` | number of the current record **in the current file** |
| `OFS` | output field separator (default: space) |
| `ORS` | output record separator (default: `\n`) |
| `FILENAME` | name of the current input file |

```bash
ls -al | awk '{print NR, $9}'                       # number the files
awk -F, '/Aniket/{print NR, $1, $2}' Students.csv   # line no, roll, name
```

> **`NR == FNR`** is true only while reading the **first** of several files - the standard
> idiom for "build a lookup table from file 1, then use it on file 2" (used by
> `calculateCPI.sh` and `viewWithColor.sh`).

---

## 6. awk program structure

```awk
BEGIN { pre-processing statements }   # once, before any record
pattern { action }                    # once per matching record
pattern { action }
END   { post-processing statements }  # once, after the last record
```

- **`BEGIN`** - initialization: set `FS`, init variables, print report headings.
- **body** - one or more `pattern { action }` rules applied per record.
- **`END`** - aggregates and conclusions (totals, averages).
- Comments start with `#`. `BEGIN` and `END` are themselves *patterns*.

Rules:

- If the **pattern is missing**, the action runs on **all** lines.
- If the **action is missing**, the matched line is **printed**.
- A rule must have *either* a pattern *or* an action.

```bash
awk '/for/' testfile        # print every line containing "for"
```

The body can be one statement, a `;`-separated list, or a multi-line block:

```awk
pattern { statement }
pattern { statement; statement; statement }
pattern {
    statement
    statement
}
```

---

## 7. awk patterns

### 7.1 Match expressions (regular expressions)

- `/re/` - matches an occurrence **anywhere in the whole record** (`$0`).
- `field ~ /re/` - matches within a **field**; `!~` is "does not match".

```bash
awk -F, '/Pooja/ {print $1}' file                         # "Pooja" anywhere in the record
awk -F, '($1 ~ /19D[A-Z0-9]+/){print NR, $0}' Students.csv # only field 1 matches
# /Pooja/{print}  is the same as  ($0 ~ /Pooja/){print}
```

### 7.2 Non-match (expression) patterns

Built from constants, variables (`$n`, built-ins, user vars), and operators:

- Arithmetic: `+ - * / % ^`
- String: concatenation, search, substitution, extraction
- Relational: `< <= == != > >=`
- Boolean: `&& || !`

```bash
awk '$3 * $4 > 500 {print $0}' file
awk '($2 > 5) && ($2 <= 15){print $0}' file
awk '$3 == 100 || $4 > 50' file          # action omitted -> print
```

### 7.3 Range patterns

```
pattern1, pattern2 { action }     # pattern1 turns the action ON, pattern2 turns it OFF
```

```bash
awk '/190050002/,/190020010/{print}' Students.csv
```

---

## 8. awk actions, variables, and output

### 8.1 Actions and variable scope

Actions are made of variables (user, field, built-in), constants (numeric, string,
associative arrays), and operators.

```awk
# fed from:  wc -c *
BEGIN { lines = 0; total = 0 }
{ lines++; total += $1 }
END {
    print lines " lines read"
    print "total is ", total
    if (lines > 0) print "average is ", total / lines
    else           print "average is 0"
}
```

**Passing a shell variable into awk** - a shell variable is **not** visible inside the awk
program; use `-v`:

```bash
w=$1
awk -F, -v w="$w" '
BEGIN { print "Printing w"; print w }
/190050226/ { print $1 }' "$1"
```

(Without `-v`, `$1` inside awk is the **first field**, not the shell's first argument.)

### 8.2 Associative arrays

Indices are created by use; any string can be a key. The canonical "group-and-sum":

```awk
awk -F, '
($9 ~ /[A-Z][A-Z]/) { state[$9] = state[$9] + $10 }   # sum deaths per state code
END { for (i in state) print state[i], i }            # iterate the keys
'
```

> `for (key in array)` iterates the keys in **unspecified order** - if you need a sorted
> report, pipe through `sort` (as the assignment's `summary.sh` does).

### 8.3 Output: `print`, `printf`, `sprintf`

- `print` - simple output (items joined by `OFS`, line ended by `ORS`).
- `printf` - C-style formatted output (no implicit newline).
- `sprintf` - returns a formatted **string**.

```bash
awk -F, '{print $1,$2 | "sort"}'        Students.csv   # pipe output to a command
awk -F, '{print $1,$2 | "sort -k 2"}'   Students.csv
awk '{printf("z is %5.3f \n", z)}'
awk -F, '{ text = sprintf("1: %d - 2: %d", $1, $2); print text }' Students.csv
```

> `%20s` right-justifies a string in a 20-wide field - this is exactly the format
> `viewWithoutColor.awk` uses (`printf "%20s%20s..."`), and the header rule of
> "hyphens = 20 x number_of_fields".

### 8.4 Decisions and loops

```awk
if (cond) { ... } else { ... }

for (i = 1; i <= NF; i++) { total += $i; count++ }   # C-style for

for (x = 0; x < 20; x++) {
    if (array[x] > 100) continue
    printf "%d ", x
    if (array[x] < 0) break
}
# while / do-while also available
```

### 8.5 A complete formatted-report example

```awk
BEGIN {
    FS = ","; total = 0
    print "  Covid Data   Date: 24th July"
    print "  State   Dist.   Cases"
    print "  =================================="
}
{
    printf("%6s %-25s %d\n", $9, $7, $10) | "sort -k 1"
    state[$9] += $10; total += $10
}
END {
    print "  ======================================"
    print "  State   Total"
    for (i in state) printf("  %-15s   %d\n", i, state[i])
    print "  Total Cases (India):  " total
}
```

This single program shows the whole `awk` toolbox: `BEGIN` headers, per-record field
extraction + aggregation into an associative array, piping to `sort`, and an `END` summary.

---

## 9. Tooling cheat-sheet

### 9.1 sed options and commands

| Item | Meaning |
|---|---|
| `-n` | suppress auto-print |
| `-r` / `-E` | extended regex |
| `-s` | per-file (not concatenated) |
| `-f file` | script from file |
| `-i[.bak]` | edit in place (optional backup suffix) |
| `-e cmd` | add another command on the command line |
| `s/re/rep/[g\|N\|p\|w f]` | substitute |
| `y/abc/xyz/` | transliterate |
| `p` / `P` | print all / first line of pattern space |
| `d` / `=` | delete / print line number |
| `i \| a \| c` | insert / append / change |
| `n` / `N` | next line / append next line |
| `h H g G x` | hold-space moves |
| `r` / `w` | read / write file |
| `b` / `q` | branch / quit |

### 9.2 awk variables and operators

| Item | Meaning |
|---|---|
| `$0`, `$1..$NF` | whole record, individual fields |
| `FS RS OFS ORS` | input/output field & record separators |
| `NF NR FNR FILENAME` | field count, record numbers, filename |
| `-F sep` / `-v n=v` / `-f file` | set FS / set variable / script file |
| `~  !~` | field matches / does not match a regex |
| `&& \|\| !` | boolean and / or / not |
| `+ - * / % ^` | arithmetic |
| `array[key]`, `for (k in array)` | associative arrays |
| `print`, `printf`, `sprintf` | output / formatted output / format-to-string |
| `BEGIN { } END { }` | pre/post-processing blocks |
| `if`, `for`, `while`, `break`, `continue` | control flow |

---

## 10. One-paragraph summary

`sed` and `awk` are streaming, line-at-a-time text processors that live where Unix data
already is - logs, command output, and pipelines. `sed` is a **stream editor**: a list of
`[address] command` pairs edits the **pattern space** (with a **hold space** for cross-line
state), giving precise one-shot edits via `s///`, `d`, `y///`, addresses, and `h/H/g/G`.
`awk` is a **pattern-action language**: it splits each record into **fields**, matches it
against **patterns** (regexes, expressions, ranges, `BEGIN`/`END`), and runs **actions** (a
C-like language with variables, associative arrays, `printf`, and the `NR == FNR`
two-file idiom) - ideal for field extraction, frequency tables, and formatted reports.
Together they cover "investigate, transform, and report" tasks far faster than spinning up a
full programming language.

### Further reading

- *sed & awk*, Dale Dougherty & Arnold Robbins (O'Reilly), 2nd ed. - the canonical reference.
- *The AWK Programming Language*, Aho, Kernighan & Weinberger - by the authors.
- GNU manuals: `info sed`, `info gawk`; and `man sed`, `man awk`.
- Source decks: [Resources/Lecture - sed-and-awk-2026.pdf](Resources/Lecture%20-%20sed-and-awk-2026.pdf).
