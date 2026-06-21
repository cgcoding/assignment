# sed and awk - Step-by-Step Assignment Approach

> Companion to `SED-AWK-NOTES.md` (the concept reference). This file is the command-level
> playbook for solving both questions and cross-references the existing answers under
> [q1/](q1) and [q2/](q2). Source brief:
> [Resources/Assignment Sed and Awk - 2026.pdf](Resources/Assignment%20Sed%20and%20Awk%20-%202026.pdf).

**Total: 65 marks** - Q1 (25) + Q2 (40).

| Question | Subtask | File | Tool required | Marks |
|---|---|---|---|---|
| Q1 | awk-1 | `failed_login.sh` | awk | 5 |
| Q1 | awk-2 | `summary.sh` | awk | 5 |
| Q1 | awk-3 | `local_filter.sh` | awk | 5 |
| Q1 | sed-a | `replace.sh` | sed | 5 |
| Q1 | sed-b | `remove_debug.sh` | sed | 5 |
| Q2 | A | `viewWithoutColor.awk` | awk | 10 |
| Q2 | B | `viewWithColor.sh` | sed + awk | 20 |
| Q2 | C | `viewSemester.sh` | sed/awk | 5 |
| Q2 | D | `calculateCPI.sh` | sed/awk | 5 |

> **Ground rules (from the brief).** You may use `bash`, `sed`, `awk`, and standard Unix
> utilities. **Do not** use Python, R, Perl, spreadsheets, or GUI tools. The `awk-*` tasks
> **must use awk**; the `sed-*` tasks **must use sed**. Solutions must work on the given
> directory tree and **must not assume a fixed depth** for `*.c`/`*.h` files. For Q2 tasks A
> and B you may use loops *inside* a `sed`/`awk` program but **not** outside it, and you must
> submit **one file per task** with no helper files (except the provided `defineColors.sh`,
> assumed to live in `./resources`).

---

## Q1 - Logs and a source tree (25 marks)

The provided tarball extracts to `q1_inputs/`:

```
./q1_inputs/
|-- logs/
|   |-- auth.log
|   `-- app.log
`-- src/
    |-- README.txt
    |-- include/{core/{adapter.h, legacy_wrap.h}, moduleA/http_client.h, moduleB/metrics.h}
    |-- legacy/net/{adapter_boot.c, adapter_reset.h, connection.c}
    |-- module1/io/{file_reader.c, init_helpers.h, init_sequence.c, parser.c}
    `-- module2/
        |-- drivers/serial/{serial_boot.c, serial_diag.c, serial_diag.h, subsys/{recovery.c, recovery.h}}
        |-- drivers/usb/{adapter_probe.c, adapter_probe.h, tempdebug_notes.c}
        `-- tools/report.awk
```

The five scripts share a usage `./script.sh <input> <output>` and write a single named file
into `<output>/`.

### awk-1 - `failed_login.sh` (5 marks)

**Requirement.** `./failed_login.sh <input> <output>` reads `auth.log` and writes
`<output>/failed_logins.txt`, one record per **failed** login with fields in order:
**month, day, time, username, source IP**. Must handle both log shapes:

```
Jul 10 08:11:09 labnode42 sshd[1800]: Failed password for root from 10.5.12.77 port 51322 ssh2
Jul 10 08:11:09 labnode42 sshd[1900]: Failed password for invalid user guest from 185.199.108.7 port 59201 ssh2
```

i.e. extract `root` in the first and `guest` in the second.

**Approach.** Filter to `/Failed password/`, then walk the fields:

```awk
/Failed password/ {
  month=$1; day=$2; time=$3; user=""; ip=""
  for (i = 1; i <= NF; i++) {
    if ($i == "for") user = ($(i+1)=="invalid" && $(i+2)=="user") ? $(i+3) : $(i+1)
    if ($i == "from") ip = $(i+1)
  }
  if (user != "" && ip != "") print month, day, time, user, ip
}
```

**Gotchas.** The token after `for` is either the username *or* the literal `invalid user`
prefix; key off `invalid`/`user`. Skip non-`Failed` lines (`Accepted`, `session opened`,
`Connection closed`) - they must not appear.

**Expected output shape.**

```
Jul 10 08:11:09 root 10.5.12.77
Jul 10 08:11:09 guest 185.199.108.7
```

### awk-2 - `summary.sh` (5 marks)

**Requirement.** `./summary.sh <input> <output>` writes `<output>/top_failed_users.txt`: the
**top 10** usernames by number of failed logins, **descending by count**; ties broken by
**ascending lexicographic username**. awk must do both the field extraction *and* the
frequency summary.

**Approach.** Count into an associative array in awk; emit `user count`; sort then take 10:

```bash
awk '/Failed password/ { ...extract user as in awk-1...; if (user!="") c[user]++ }
     END { for (u in c) print u, c[u] }' "$in" \
  | LC_ALL=C sort -k2,2nr -k1,1 | head -n 10 > "$out"
```

**Gotchas.** `sort -k2,2nr` = numeric, reverse on the count; `-k1,1` = ascending username
for ties. `LC_ALL=C` keeps lexicographic order stable. `for (u in c)` is unordered, so the
external `sort` is what guarantees the spec order.

**Expected output shape** (count column shown for clarity):

```
root 5
deploy 4
admin 3
backup 2
git 2
guest 2
```

### awk-3 - `local_filter.sh` (5 marks)

**Requirement.** `local_filter.sh <input> <output>` reads `app.log`, keeps lines containing
`ERROR`, and writes `<output>/error_lines.txt` with only **date, time, error code**.

**Approach.** A log line looks like
`2026-07-10 08:11:21 ERROR cache module=adapter worker=2 code=E203 message="..."`. Match
`/ERROR/`, take `$1` (date) and `$2` (time), and find the `code=` field:

```awk
/ERROR/ {
  for (i = 1; i <= NF; i++) if ($i ~ /^code=/) { code = substr($i, 6); break }
  if (code != "") print $1, $2, code
}
```

**Gotchas.** Only the `code=` field carries the error code; don't print `WARN`/`INFO`
lines. Strip the `code=` prefix.

**Expected output shape.**

```
2026-07-10 08:11:21 E203
2026-07-10 08:11:45 E517
```

### sed-a - `replace.sh` (5 marks)

**Requirement.** Across `src/` (recursively, any depth), in `*.c`/`*.h` files that contain
`#include <oldlib.h>` **and also a call to `init_adapter()`**, replace the include with
`#include <newlib.h>`. Modify no other file. Any backup must use the `.bak` extension. Write
`<output>/patched_files.txt` listing the files actually modified.

**Approach.** Walk with `find ... -print0`; for each file, test **both** conditions with
`grep -q`; only then run an anchored `sed` substitution; record the file:

```bash
find "$src" -type f \( -name '*.c' -o -name '*.h' \) -print0 |
while IFS= read -r -d '' f; do
  if grep -q 'init_adapter[[:space:]]*(' "$f" && grep -q '^#include <oldlib\.h>$' "$f"; then
    sed -i.bak 's|^#include <oldlib.h>$|#include <newlib.h>|' "$f"
    cmp -s "$f.bak" "$f" || printf '%s\n' "$f" >> "$out/patched_files.txt"
    rm -f "$f.bak"
  fi
done
```

**Gotchas.**
- **Both** conditions are mandatory - the tree is seeded with distractors: files with the
  old include but no `init_adapter` (`connection.c`, `serial_diag.c`, `serial_diag.h`,
  `http_client.h`, `legacy_wrap.h`, `init_helpers.h`), and files that call `init_adapter`
  but never include `oldlib.h`.
- A **prototype** `int init_adapter(struct adapter_config *cfg);` (in `adapter.h`) is a
  *declaration*, not a *call* - a regex like `init_adapter[[:space:]]*(` cannot tell them
  apart. Decide deliberately whether a header that only declares the function should be
  patched.
- Anchor the substitution (`^...$`) so only the whole include line changes; clean up `.bak`.

**Expected output shape** (`patched_files.txt`, one path per modified file):

```
.../src/legacy/net/adapter_boot.c
.../src/module1/io/init_sequence.c
.../src/module2/drivers/usb/adapter_probe.c
```

### sed-b - `remove_debug.sh` (5 marks)

**Requirement.** Remove every line beginning with `// TEMPDEBUG:` from all `*.c`/`*.h` files
under `src/` (recursively). Write `<output>/debug_removed_count.txt` with the **total number
of removed lines**. Be robust to **paths containing spaces**.

**Approach.** Count first (sum per-file matches), then delete:

```bash
count=$(find "$src" -type f \( -name '*.c' -o -name '*.h' \) -print0 |
  while IFS= read -r -d '' f; do
    awk '/^[[:space:]]*\/\/ TEMPDEBUG:/{c++} END{print c+0}' "$f"
  done | awk '{s+=$1} END{print s+0}')

find "$src" -type f \( -name '*.c' -o -name '*.h' \) -print0 |
while IFS= read -r -d '' f; do sed -i.bak '/^[[:space:]]*\/\/ TEMPDEBUG:/d' "$f"; rm -f "$f.bak"; done

printf '%s\n' "$count" > "$out/debug_removed_count.txt"
```

**Gotchas.** Count **before** you delete (or sum what `sed` reports). `-print0` +
`IFS= read -r -d ''` + quoting `"$f"` is the space-safe iteration idiom. Escape the `//`
in the address (`\/\/`).

**Expected output shape.** A single integer, e.g. `5`.

---

## Q2 - Course visualizer (40 marks)

Inputs (CSV, exported from the provided spreadsheets), record separator `\r\n`:

- `allCoursesTaken.csv` - header `Year,Semester,Code,Name,Credits,Tag,letterGrade`.
- `creditsRequirements.csv` - per-`Tag` credit requirement **and** a colour mapping.
- `letterGradeToNumber.csv` - letter grade -> numeric grade point.

Reference outputs are checked with a **plain `diff`**, so byte-exactness (escape order, CRLF,
spacing) matters.

### Task A - `viewWithoutColor.awk` (10 marks)

**Requirement.** Display `allCoursesTaken.csv` formatted: **drop the `Name` column**, print
the remaining **6** fields each in a `%20s` field. The header separator is
`20 x number_of_fields` hyphens (= 120). Usage: `awk -f viewWithoutColor.awk
./resources/allCoursesTaken.csv`. Its output is **`outputA`**.

**Approach.**

```awk
BEGIN { FS=","; OFS=""; for (i=1;i<=120;i++) line=line"-" }
NR==1 { print line
        printf "%20s%20s%20s%20s%20s%20s\n","Year","Semester","Code","Credits","Tag","letterGrade"
        print line; next }
{ printf "%20s%20s%20s%20s%20s%20s\n", $1,$2,$3,$5,$6,$7 }
```

**Gotchas.** Six columns after dropping `Name` (`$4`). 120 hyphens, not 100. Strip `\r`
(`sed 's/\r$//'` upstream, or trim in awk) so trailing `letterGrade` is clean. Column
offsets become **fixed**: Year 1-20, Semester 21-40, Code 41-60, Credits 61-80, Tag 81-100,
letterGrade 101-120 - tasks B and C rely on these offsets.

### Task B - `viewWithColor.sh` (20 marks)

**Requirement.** Take `outputA` + `creditsRequirements.csv`; using **sed and awk**, colour
each course row by the colour scheme in `creditsRequirements.csv`. `source
./resources/defineColors.sh` for the colour variables. Output is **`outputB`**; `cat
outputB` shows colour. Usage: `./viewWithColor.sh outputA ./resources/creditsRequirements.csv`.

**Approach.** Two-file awk with the `NR==FNR` idiom: build `tag -> (font, background)` from
the credits file, then for each `outputA` course row read the tag from the fixed slice
`substr($0,81,20)` and wrap the line in the colour codes.

```awk
NR==FNR { ...record tag_fg[tag], tag_bg[tag] from creditsRequirements...; next }
{ tag = trim(substr($0,81,20))
  # EMIT BACKGROUND THEN FONT (see gotcha), then the line, then RESET_ALL
  print bg[tag] fg[tag] $0 RESET_ALL }
```

**Gotchas.**
- **Colour order is graded.** The reference `outputB` emits **background first, then
  font** (e.g. `ESC[40m` then `ESC[33m`), closing with `RESET_ALL`. Emitting font-then-
  background reverses the escapes and a plain `diff` will fail even though the terminal
  *looks* the same. The brief warns about this explicitly.
- Pass the colour variables into awk with `-v` (shell vars are invisible inside awk).
- Leave the 3 header lines uncoloured (their tag slice matches no tag, so they pass through).
- Use `source ./resources/defineColors.sh`; do not redefine or submit it.

**Expected output shape.** `outputA` lines, each course row bracketed by
`<background><font> ... <reset>`; 63 lines in, 63 lines out.

### Task C - `viewSemester.sh` (5 marks)

**Requirement.** `./viewSemester.sh outputB <semester> <year>` filters `outputB` rows by
semester **and** year, sorts by **course code**, and prints - **keeping the colours** of
`outputB`. e.g. `./viewSemester.sh outputB Autumn 2018`.

**Approach.** Pass the 3 header lines through unchanged; for data rows strip ANSI **only to
build the comparison/sort key**, compare `substr(plain,1,20)`==year and
`substr(plain,21,20)`==semester, sort on the code slice `substr(plain,41,20)`, but print the
**original coloured** line.

```bash
head -n 3 "$outputB"
tail -n +4 "$outputB" | awk '...strip_ansi for key; print code "\t" $0 if match...' \
  | LC_ALL=C sort -t$'\t' -k1,1 | cut -f2-
```

**Gotchas.** Compare on the colour-stripped text but emit the coloured original. Watch the
argument order (`semester` then `year`).

### Task D - `calculateCPI.sh` (5 marks)

**Requirement.** `./calculateCPI.sh ./resources/allCoursesTaken.csv
./resources/letterGradeToNumber.csv` - CPI over **all** courses, to **4 decimal places**.

**Approach.** Load grade->point from file 1, then over file 2 accumulate
`sum(credits x point) / sum(credits)`:

```awk
NR==FNR { if (FNR>1) gp[trim($1)] = trim($2)+0; next }
FNR==1  { next }
{ c = trim($5)+0; g = trim($7)
  if (c>0 && g in gp) { tot+=c; wt+=c*gp[g] } }
END { printf (tot>0 ? "%.4f\n" : "0.0000\n"), (tot>0 ? wt/tot : 0) }
```

**Gotchas.** `Credits`=`$5`, `letterGrade`=`$7`. Strip `\r` (CRLF) before the grade lookup,
or the key `"AB\r"` won't match `"AB"`. `printf "%.4f"` for exactly four decimals.

---

## Solution Validation

> **Report-only**, by static inspection against the brief and the reference outputs. No
> solution file was modified or executed. Note that the scripts have evidently already been
> run once against `q1/q1_inputs/` (the source tree now shows `newlib.h` in the patched files
> and the `// TEMPDEBUG:` lines are gone), so `q1/q1_outputs/` reflects a real prior run.

### Q1

| Subtask | File | Status |
|---|---|---|
| awk-1 | [q1/failed_login.sh](q1/failed_login.sh) | **Appropriate** |
| awk-2 | [q1/summary.sh](q1/summary.sh) | **Appropriate** (minor format note) |
| awk-3 | [q1/local_filter.sh](q1/local_filter.sh) | **Appropriate** |
| sed-a | [q1/replace.sh](q1/replace.sh) | **Appropriate** (one edge-case risk) |
| sed-b | [q1/remove_debug.sh](q1/remove_debug.sh) | **Appropriate** |

**awk-1 - [q1/failed_login.sh](q1/failed_login.sh) - Appropriate.** Matches `/Failed
password/`, walks fields to resolve both `for <user>` and `for invalid user <user>`, and the
`from` IP. Prints `month day time user ip`. Checked against
[q1/q1_inputs/logs/auth.log](q1/q1_inputs/logs/auth.log): non-failed lines (`Accepted`,
`session opened`, `Connection closed`) are correctly skipped. The recorded
[q1/q1_outputs/failed_logins.txt](q1/q1_outputs/failed_logins.txt) shows
`Jul 10 08:11:09 root 10.5.12.77` and `... guest 185.199.108.7` - both forms handled. No gaps.

**awk-2 - [q1/summary.sh](q1/summary.sh) - Appropriate.** Counts users in an awk array
(extraction + frequency both in awk, as required), then `sort -k2,2nr -k1,1 | head -n 10`
gives descending count with ascending-username tie-breaks.
[q1/q1_outputs/top_failed_users.txt](q1/q1_outputs/top_failed_users.txt) confirms the tie
ordering (`backup, git, guest, monitor` all at 2; `demo, ftp, nagios` at 1).
*Minor note:* the brief says "top 10 **usernames**"; the output is `username count` pairs. If
the grader expects bare usernames this two-column form may differ from the reference - worth
confirming, though it is arguably more informative and still correctly ordered.

**awk-3 - [q1/local_filter.sh](q1/local_filter.sh) - Appropriate.** Filters `/ERROR/`,
extracts `$1`/`$2` and the `code=` field (prefix stripped, sanitised). Verified against
[q1/q1_inputs/logs/app.log](q1/q1_inputs/logs/app.log): only the two `ERROR` lines carry a
`code=`, and [q1/q1_outputs/error_lines.txt](q1/q1_outputs/error_lines.txt) is exactly
`2026-07-10 08:11:21 E203` / `2026-07-10 08:11:45 E517`. `WARN`/`INFO` lines excluded. No gaps.

**sed-a - [q1/replace.sh](q1/replace.sh) - Appropriate, with one edge-case risk.** Logic is
right: recursive `find -print0`, requires **both** `init_adapter(` **and** the anchored
`#include <oldlib.h>` before substituting, uses a `.bak` backup that is then removed, and
records modified files (sorted, de-duplicated) in
[q1/q1_outputs/patched_files.txt](q1/q1_outputs/patched_files.txt). The distractor files that
have the include but no call are correctly left untouched.
*Risk:* the call-detection regex `init_adapter[[:space:]]*(` also matches the **prototype**
`int init_adapter(struct adapter_config *cfg);` in
[q1/q1_inputs/src/include/core/adapter.h](q1/q1_inputs/src/include/core/adapter.h), so
`adapter.h` was patched and appears in `patched_files.txt`. A strict reading of "contains a
**call** to `init_adapter()`" would exclude a header that only *declares* the function. If
the grader's reference excludes `adapter.h`, this is a one-file over-match; tighten the test
to require a call site (e.g. exclude lines ending in `;` that are pure prototypes).

**sed-b - [q1/remove_debug.sh](q1/remove_debug.sh) - Appropriate.** Counts
`^[[:space:]]*// TEMPDEBUG:` lines (summed across files) **before** deleting them with
`sed -i.bak /.../d`, and is space-robust (`-print0`, `IFS= read -r -d ''`, quoted `"$f"`,
`.bak` cleaned up). [q1/q1_outputs/debug_removed_count.txt](q1/q1_outputs/debug_removed_count.txt)
is `5`; the current tree confirms no `// TEMPDEBUG:` lines remain. Allowing leading
whitespace before the marker is a sensible robustness extension over a strict "line begins
with" reading. No gaps.

### Q2

| Task | File | Status |
|---|---|---|
| A | [q2/viewWithoutColor.awk](q2/viewWithoutColor.awk) | **Appropriate** |
| B | [q2/viewWithColor.sh](q2/viewWithColor.sh) | **Incorrect** (colour order reversed) |
| C | [q2/viewSemester.sh](q2/viewSemester.sh) | **Appropriate** |
| D | [q2/calculateCPI.sh](q2/calculateCPI.sh) | **Appropriate** |
| (driver) | [q2/viewCourses.sh](q2/viewCourses.sh) | **Appropriate** (naming note) |

**Task A - [q2/viewWithoutColor.awk](q2/viewWithoutColor.awk) - Appropriate.** Drops `Name`
(`$4`), prints the 6 remaining fields with `%20s`, and lays a 120-hyphen separator
(`20 x 6`). Compared field-by-field against the reference
[q2/resources/outputA](q2/resources/outputA): header (`Year ... letterGrade`), separators,
and the `%20s` right-justified columns (e.g. `CS 753` kept intact) all match. The extra
`semester_filter` hook is inert when the variable is unset, so Task A output is unaffected.

**Task B - [q2/viewWithColor.sh](q2/viewWithColor.sh) - Incorrect.** The colorizer uses the
correct `NR==FNR` two-file idiom and reads the tag from the right slice
(`substr($0,81,20)`), but it prints **`fg bg $0 RESET_ALL`** - font escape *then* background
escape (line `print fg bg $0 RESET_ALL`). The reference
[q2/resources/outputB](q2/resources/outputB) emits **background then font** - the first
coloured row begins `ESC[40m` (`setab 0`) followed by `ESC[33m` (`setaf 3`). Since Task B is
graded by a plain `diff`, the reversed escape sequence (`ESC[33m ESC[40m ...`) will mismatch
on **every** coloured line even though the terminal rendering looks identical - exactly the
ordering pitfall the brief warns about. **Concrete fix:** swap to `print bg fg $0 RESET_ALL`.
*Secondary (benign) issue:* the header pass-through guard `NR - FNR <= 3` is not the current
record number in the second file (it equals the credits-file line count, a constant); it
happens to be harmless here because header/separator lines have no matching tag and fall
through uncoloured, but the intended guard is `FNR <= 3` while reading `outputA`.

**Task C - [q2/viewSemester.sh](q2/viewSemester.sh) - Appropriate.** Passes the 3 header
lines through unchanged, strips ANSI **only** to build the comparison and sort keys (year
`substr(plain,1,20)`, semester `substr(plain,21,20)`, code `substr(plain,41,20)`), sorts on
the code with `LC_ALL=C sort -k1,1`, and prints the **original coloured** line via
`cut -f2-`. Colours are preserved and the fixed offsets match Task A's layout. No gaps.

**Task D - [q2/calculateCPI.sh](q2/calculateCPI.sh) - Appropriate.** Builds `gp[grade]` from
`letterGradeToNumber.csv`, then accumulates `sum(credits x point)/sum(credits)` over
`allCoursesTaken.csv` using `Credits=$5`, `letterGrade=$7`, and prints `%.4f`. The `trim()`
strips `\r`, so the CRLF inputs are handled and the grade key matches the lookup table. All
courses are included as the brief requires. No gaps.

**Driver - [q2/viewCourses.sh](q2/viewCourses.sh) - Appropriate (naming note).** A thin
wrapper that runs `sed 's/\r$//' | awk -f viewWithoutColor.awk` to produce `outputA`, and
defensively rejects `.xlsx` input. *Naming:* the brief's submission tree lists `viewCourse.sh`
(singular); this file is `viewCourses.sh` (plural). Also note the brief's submission tree
omits `calculateCPI.sh` even though Task D requires it - an inconsistency in the brief itself,
not in the solution. Rename to match whatever the grader's harness expects.

### Coverage summary

| Area | Appropriate | Caveat / risk | Incorrect | Missing |
|---|---|---|---|---|
| Q1 (5 subtasks) | 5 | replace.sh prototype over-match; summary.sh two-column format | 0 | 0 |
| Q2 (4 tasks + driver) | 4 | viewCourses.sh naming | 1 (`viewWithColor.sh` colour order) | 0 |

**Headline gaps to fix before submission:**

1. **`viewWithColor.sh`** - swap escape order to **background-then-font** (`print bg fg $0
   RESET_ALL`); this is the single change that makes the Task-B `diff` pass.
2. **`replace.sh`** - confirm whether the prototype-only header
   [adapter.h](q1/q1_inputs/src/include/core/adapter.h) should be patched; tighten the
   call-detection if the grader treats a declaration as "not a call".
3. **File naming** - reconcile `viewCourses.sh` vs the brief's `viewCourse.sh`, and confirm
   `calculateCPI.sh` is accepted despite its omission from the brief's submission tree.
