# Bash Assignment - Step-by-Step Approach

> Companion to `BASH-NOTES.md` (the concept reference). This file is the command-level
> playbook for solving all four problems and cross-references the existing solution scripts in
> [q1/pdfWordCounter.sh](q1/pdfWordCounter.sh), [q2/downloadContents.sh](q2/downloadContents.sh),
> [q3/decipher.sh](q3/decipher.sh), and [q4/](q4) (`download.sh`, `organise.sh`,
> `evaluate.sh`).

**Total: 92 marks** - Q1 (10) + Q2 (15) + Q3 (12) + Q4 (55).

> **Theme.** The assignment is a tour of *web mining* with the shell: download something from
> the internet, transform it with the Unix text toolkit, and wrap it in a robust script.
> Every script must validate its arguments and, on misuse, print the exact usage line and
> `exit 1`:
>
> ```bash
> if [ "$#" -ne <N> ]; then
>     echo "Usage: ./script.sh <arg1> <arg2> ..."
>     exit 1
> fi
> ```
>
> **Environment note.** These scripts assume a GNU/Linux toolchain (`wget`, `pdftotext` from
> poppler-utils, `tree`, GNU `timeout`, `md5sum`). On macOS several of these differ or are
> missing (`md5` vs `md5sum`, BSD `wc` pads with leading spaces, no `timeout`). The grader
> runs Linux, so develop/verify on Linux (or a container) and treat macOS quirks as
> portability caveats.

---

## Q1 - `pdfWordCounter.sh` (10 marks)

### Requirement

`Usage: ./pdfWordCounter.sh <URL> <Word>` - the script must:

- **(a)** Download the PDF from `<URL>`.
- **(b)** Convert the PDF to text and print the count of `<Word>`, **case-insensitive** and
  **whole-word only** (`break` matches `Break` and the `break` in `break.`, but **not**
  `breakfast`). Use `pdftotext` and `grep`.
- **(c)** Delete the downloaded PDF.
- **(d)** The script must generate **exactly one** PDF file and delete it on exit; **no text
  file** may be created even temporarily; the **only** terminal output is the number.

### Approach

```bash
URL="$1"; WORD="$2"
FILENAME=$(basename "$URL")             # a name to save the download under
wget -q "$URL" -O "$FILENAME"           # (a) quiet download, single file
COUNT=$(pdftotext "$FILENAME" - | grep -owi "$WORD" | wc -l)   # (b) stdout pipe, no temp file
rm -f "$FILENAME"                       # (c) clean up the only generated file
echo "$COUNT"                           # (d) only output: the number
```

Why each piece:

- `pdftotext "$FILENAME" -` writes text to **stdout** (the `-`), so it is **piped** straight
  into `grep` - no intermediate `.txt` file is ever written (satisfies (d)).
- `grep -o` prints each match on its own line, `-w` enforces whole-word (punctuation like `.`
  is a non-word boundary, so `break.` matches but `breakfast` does not), `-i` is
  case-insensitive. Piping into `wc -l` counts the occurrences.

### Gotchas

- **Counting occurrences, not lines:** `grep -c` would count matching *lines* (two hits on
  one line = 1). The `-o | wc -l` idiom counts every occurrence - this is the crux of the
  marks.
- **Regex metacharacters in `<Word>`:** if the word could contain `.` `*` `[`, add `-F`
  (fixed-string) to avoid treating it as a regex.
- **Filename from URL:** `basename "$URL"` can produce odd names if the URL has a query
  string (`?...`); using a fixed name like `downloaded.pdf` is safer and still satisfies "one
  pdf file".

### Expected output shape

A single integer on one line, e.g. for the sample link with word `code`:

```
42
```

(the exact number depends on the live PDF).

---

## Q2 - `downloadContents.sh` (15 marks)

### Requirement

`Usage: ./downloadContents.sh <url> <directory_path>`:

- **(a)** Recursively download pages/files reachable from `<url>`, restricted to **(i)** the
  same domain and **(ii)** the starting directory or below (no parent dirs). Page requisites
  (CSS/images) needed to render the pages must be fetched even if outside the start dir, as
  long as same-domain. Convert links to point at the downloaded files. Save under
  `<directory_path>`. **[5]**
- **(b)** Use `tree` to store the directory contents in **JSON** in `urlReport.json`. **[2]**
- **(c)** Print the `md5sum` of that JSON file. **[2]**
- **(d)** Count the `{` characters in the file with `tr` and print on a new line. **[1]**
- **(e)** Call that count `n`; if a process with PID `n` exists, print its COMMAND name (from
  `ps aux`), else print `No such process`. **[5]**

Output: each item on its own line, no spaces.

### Approach

```bash
URL="$1"; DIR="$2"
DOMAIN=$(echo "$URL" | awk -F/ '{print $3}')      # host between the 2nd and 3rd slash
wget -q --recursive --no-parent --page-requisites --convert-links \
     --domains "$DOMAIN" --directory-prefix="$DIR" "$URL"     # (a)
tree -J "$DIR" > "$DIR/urlReport.json"            # (b) -J = JSON
md5sum "$DIR/urlReport.json" | awk '{print $1}'   # (c) hash only
COUNT=$(tr -cd '{' < "$DIR/urlReport.json" | wc -c)   # (d) keep only '{', count
echo "$COUNT"
PROC=$(ps aux | awk -v pid="$COUNT" 'NR>1 && $2==pid {print $11}')   # (e)
[ -z "$PROC" ] && echo "No such process" || echo "$PROC"
```

### Gotchas

- **`--no-parent` vs `--page-requisites`:** `-np` blocks ascent to parent directories, but the
  spec wants requisites *even outside* the start dir (same domain). `wget -p` does try to
  fetch requisites regardless, but the `-np` interaction can occasionally skip parent-dir
  assets - verify the rendered pages actually have their CSS/images.
- **JSON file includes itself:** `tree -J "$DIR" > "$DIR/urlReport.json"` creates the (empty)
  `urlReport.json` *before* `tree` runs, so `tree` lists `urlReport.json` as a node. This is
  deterministic but means the md5sum / brace count include the report's own entry. Generating
  the JSON outside `$DIR` then moving it in avoids this.
- **`{` count must use `tr`:** `tr -cd '{'` deletes everything except `{`; `wc -c` counts the
  survivors. On **BSD/macOS** `wc` pads its output with leading spaces, which would violate
  "no spaces" - GNU `wc` (the grader) does not.
- **`ps` field 11:** kernel threads display bracketed (`[migration/7]`), so `$11` may include
  brackets; the expected sample (`migration/7`) is unbracketed - environment dependent.

### Expected output shape

```
fa069666859c6576953fb9d0cf3e50eb
59
migration/7
```

(md5 hash, then the `{` count, then the process name or `No such process`).

---

## Q3 - `decipher.sh` (12 marks)

### Requirement

`Usage: ./decipher.sh <url>` - the Mary, Queen of Scots cipher story:

- **(a)** Download `<url>` quietly and save as `encrypted.txt`. **[2]**
- **(b)** The text is a Caesar shift cipher. Try **all** shifts on the **last line** and find
  the one whose deciphering contains `Queen`, `Majesty`, `Marie`, or `Mary`
  (case-insensitive). Use `tail`, `tr`, `grep`. **[6]**
- **(c)** Decipher the whole letter with the found key, preserving newlines, into
  `deciphered.txt`. Use `tr`. **[2]**
- **(d)** Encrypt the line *"I would be glad to know the names and qualities of the six
  gentlemen which are to accomplish the designment."* with the **same** key and append it
  after the last line of `encrypted.txt`. **[2]**

You submit only `decipher.sh`; the grader regenerates `encrypted.txt` and `deciphered.txt`.

### Approach

```bash
URL="$1"
LOWER="abcdefghijklmnopqrstuvwxyz"; UPPER="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
wget -q "$URL" -O encrypted.txt                          # (a)

LAST_LINE=$(tail -1 encrypted.txt); FOUND_SHIFT=-1       # (b)
for s in $(seq 0 25); do
    back=$((26 - s))
    sl="${LOWER:$back}${LOWER:0:$back}"; su="${UPPER:$back}${UPPER:0:$back}"
    if echo "$LAST_LINE" | tr "$LOWER$UPPER" "$sl$su" | grep -qi "Marie\|Majesty\|Queen\|Mary"; then
        FOUND_SHIFT=$s; break
    fi
done

back=$((26 - FOUND_SHIFT))                               # (c) decrypt whole file
sl="${LOWER:$back}${LOWER:0:$back}"; su="${UPPER:$back}${UPPER:0:$back}"
tr "$LOWER$UPPER" "$sl$su" < encrypted.txt > deciphered.txt

PT="I would be glad to know the names and qualities of the six gentlemen which are to accomplish the designment."
el="${LOWER:$FOUND_SHIFT}${LOWER:0:$FOUND_SHIFT}"; eu="${UPPER:$FOUND_SHIFT}${UPPER:0:$FOUND_SHIFT}"
echo "$PT" | tr "$LOWER$UPPER" "$el$eu" >> encrypted.txt # (d) encrypt + append
```

The key insight: a Caesar shift is a `tr` from the alphabet to a **rotated** alphabet built
with substring slicing. To **decrypt** a forward shift of `s`, rotate **back** by `s`
(= forward by `26 - s`). To **encrypt**, rotate forward by `s`.

### Gotchas

- **Direction:** the deck says "if A->G then ... shift forward by 6". Decryption is the
  inverse; building `${LOWER:back}${LOWER:0:back}` with `back=26-s` maps cipher letter `a`
  back to plaintext correctly.
- **Negative-offset pitfall:** `${LOWER:$FOUND_SHIFT}` when `FOUND_SHIFT` is `-1` is parsed by
  Bash as `${LOWER:-1}` (the *default-value* operator), **not** a negative substring - which
  silently yields the whole alphabet. Negative substrings need a space: `${LOWER: -1}`. Only
  matters if no shift is found; guard step (d) with `[ "$FOUND_SHIFT" -ge 0 ]`.
- **Preserve newlines:** decrypt the whole file via `tr ... < encrypted.txt > deciphered.txt`
  (`tr` only touches letters, leaving newlines and punctuation intact). Don't loop line by
  line with `echo`, which can mangle blank lines.
- **`grep` alternation:** in basic `grep`, `\|` is the alternation operator; `grep -qi` makes
  it quiet and case-insensitive.

### Expected output shape

No terminal output is required; success is the **files**: `encrypted.txt` (original + one
appended ciphertext line) and `deciphered.txt` (readable English with formatting preserved).

---

## Q4 - The Autograder: `download.sh`, `organise.sh`, `evaluate.sh` (55 marks)

Three scripts in the same directory. Each part is graded independently (e.g. `organise.sh`
may assume `download.sh` produced the correct state).

### Q4a - `download.sh` (10 marks)

**Requirement:** `Usage: ./download.sh <link to directory> <cut-dirs argument>`. Mirror the
online directory locally as `mock_grading` (same structure), **rejecting** `index.html` files
and `*.tmp` files. Use `wget` in quiet + recursive mode, no parent dirs, and `--cut-dirs` to
strip the `host/~user/.../` nesting so the saved directory matches the remote name. Finally,
ensure the local directory is named `mock_grading` (rename via `basename` if the remote name
differs).

**Approach (spec-faithful):**

```bash
URL="$1"; CUT="$2"
wget -q -r -np -nH --cut-dirs="$CUT" -R "index.html*,*.tmp" "$URL/"
NAME=$(basename "${URL%/}")
[ "$NAME" != mock_grading ] && mv "$NAME" mock_grading
```

**Gotchas:** the trailing slash on `<link>` matters; `-R "index.html*"` also rejects
`index.html?C=...` sort links; `-nH` drops the `host/` directory and `--cut-dirs=N` drops the
remaining `~user/bash-assignment/` levels (the assignment notes `N` is chosen so the saved
name equals the remote one).

**Expected structure:** `mock_grading/{inputs/, outputs/, roll_list, submissions/}` with no
`index.html` and no `.tmp` files.

### Q4b - `organise.sh` (20 marks)

**Requirement:** `Usage: organise.sh` (no args). Create `organised/` and, for every roll
number in `mock_grading/roll_list`, a subdirectory `organised/<roll>/`. Inside each, create a
**relative symbolic link** to every submission file beginning with that roll number, pointing
at `../../mock_grading/submissions/<file>`. Files are named honestly (each starts with the
owner's roll number, all roll numbers equal length); a student has at least one file and at
most one `.cpp`.

**Approach:**

```bash
while IFS= read -r roll; do
    [ -z "$roll" ] && continue
    mkdir -p "organised/$roll"
    for f in "mock_grading/submissions/${roll}"*; do
        [ -f "$f" ] || continue
        ln -sf "../../mock_grading/submissions/$(basename "$f")" "organised/$roll/$(basename "$f")"
    done
done < mock_grading/roll_list
```

**Gotchas:** the link **target must be relative** (`../../mock_grading/...`) so the tree is
portable; the relative path is computed from the link's location (`organised/<roll>/`), hence
two `..`. Guard the glob with `[ -f "$f" ]` in case a roll has no matching file.

**Expected structure:**

```
organised/180070035/180070035.cpp -> ../../mock_grading/submissions/180070035.cpp
```

### Q4c - `evaluate.sh` (25 marks)

**Requirement:** `Usage: evaluate.sh` (no args). Produce `marksheet.csv` (one line per
student, `roll,score`, sorted lexicographically) and `distribution.txt` (one line per input,
`<input>, <count-correct>`). For each student, from `organised/<roll>`:

- Compile the single `.cpp` into `executable`, suppressing compiler errors (`2>/dev/null`).
  The file may be missing or fail to compile.
- For each input `mock_grading/inputs/foo.in`, run `executable` (timeout **5s**), redirecting
  stderr to `/dev/null`, and write output to `organised/<roll>/student_outputs/foo.out`. The
  output file is created by `>` **regardless** of whether `executable` exists or crashes.
- Compare with `mock_grading/outputs/foo.out`; on an exact match, `score += 1` and
  `distribution[i] += 1`.

Run compilation and execution **from within** `organised/<roll>` (so relative file access in
student code works).

**Approach:**

```bash
mapfile -t INPUTS < <(find mock_grading/inputs -maxdepth 1 -name '*.in' | sort)
declare -a dist; for ((i=0;i<${#INPUTS[@]};i++)); do dist[$i]=0; done
> marksheet.csv; > distribution.txt

while IFS= read -r roll; do
    [ -z "$roll" ] && continue
    d="organised/$roll"; mkdir -p "$d/student_outputs"; score=0
    cpp=$(ls "$d"/*.cpp 2>/dev/null | head -1)
    [ -n "$cpp" ] && ( cd "$d" && g++ -o executable "$(basename "$cpp")" 2>/dev/null )
    for ((i=0;i<${#INPUTS[@]};i++)); do
        name=$(basename "${INPUTS[$i]}" .in)
        ( cd "$d" && timeout 5 ./executable < "../../mock_grading/inputs/$name.in" \
              > "student_outputs/$name.out" 2>/dev/null )
        if diff -q "$d/student_outputs/$name.out" "mock_grading/outputs/$name.out" >/dev/null 2>&1; then
            score=$((score+1)); dist[$i]=$((dist[$i]+1))
        fi
    done
    echo "$roll,$score" >> marksheet.csv
done < mock_grading/roll_list

sort marksheet.csv -o marksheet.csv
for ((i=0;i<${#INPUTS[@]};i++)); do
    echo "$(basename "${INPUTS[$i]}" .in), ${dist[$i]}" >> distribution.txt
done
```

**Gotchas:**

- **The `>` always creates the output file** even if `executable` is absent or crashes -
  that's *why* no explicit existence check is needed, and it guarantees `diff` has a file to
  compare (it simply won't match the non-blank expected output).
- **Timeout:** `timeout 5` caps runaway/infinite student programs; suppress the resulting
  noise with `2>/dev/null`.
- **Subshell `cd`:** wrapping `cd` in `( ... )` confines the directory change so the loop's
  working directory is untouched.
- **Output formats differ on purpose:** `marksheet.csv` uses `roll,score` (no space, per the
  `180070035,2` example) while `distribution.txt` uses `<input>, <count>` (with a space, per
  the `10, 6` example).
- **Distribution ordering:** building the input list with `find | sort` yields lexicographic
  order (`0,1,10,11,...,19,2,3,...`); the spec does not mandate numeric order, but be aware
  the lines are not in `0..19` numeric sequence.

**Expected output shape:**

```
# marksheet.csv               # distribution.txt
180070026,0                   0, 6
180070035,2                   1, 6
```

---

## Solution Validation

> **Report-only.** The following is a static inspection of the submitted scripts against the
> spec above. No script was executed or modified. `q4` evidence files
> ([marksheet.csv](q4/marksheet.csv), [distribution.txt](q4/distribution.txt),
> [organised/](q4/organised)) were read to corroborate behaviour.

### Q1 - [q1/pdfWordCounter.sh](q1/pdfWordCounter.sh) - **Appropriate**

**Checked vs spec:** usage guard `[ "$#" -ne 2 ]` -> usage + `exit 1` (✓); `wget -q -O`
single download (✓ (a)); `pdftotext "$FILENAME" -` pipes to **stdout**, so no temp `.txt`
file (✓ (d)); `grep -owi "$WORD" | wc -l` gives whole-word, case-insensitive **occurrence**
count (✓ (b)); `rm -f "$FILENAME"` deletes the one generated PDF (✓ (c)); the only output is
`echo "$COUNT"` (✓ (d)).

**Concrete gaps / notes:**

- Minor: if `<Word>` contained regex metacharacters, `grep` would treat them as a pattern;
  `grep -Fowi` would harden it. Not required by the sample word `code`.
- Minor: `FILENAME=$(basename "$URL")` could yield a non-`.pdf` or query-laden name; harmless
  since `-O` forces the single output file, which is then removed.

### Q2 - [q2/downloadContents.sh](q2/downloadContents.sh) - **Appropriate (with caveats)**

**Checked vs spec:** usage guard (✓); domain extracted via `awk -F/ '{print $3}'` (✓);
`wget --recursive --no-parent --page-requisites --convert-links --domains "$DOMAIN"
--directory-prefix="$DIR"` (✓ (a)); `tree -J "$DIR" > "$DIR/urlReport.json"` (✓ (b));
`md5sum ... | awk '{print $1}'` prints hash only (✓ (c)); `tr -cd '{' < ... | wc -c`
(✓ (d)); `ps aux | awk -v pid=... 'NR>1 && $2==pid {print $11}'` with the `No such process`
fallback (✓ (e)). Output ordering (md5 / count / process) matches the required shape.

**Concrete gaps / notes:**

- **Self-inclusion:** writing `urlReport.json` *inside* `$DIR` means the redirect creates the
  empty file before `tree` scans `$DIR`, so the JSON lists `urlReport.json` itself. Result is
  deterministic but the md5sum / brace count include the report's own node; generating the
  JSON outside `$DIR` and moving it in would be cleaner.
- **`-np` vs requisites:** `--no-parent` can suppress page requisites that live in parent
  directories, which the spec wants fetched (same-domain). Worth verifying rendered pages.
- **Portability:** BSD/macOS `wc -c` pads leading spaces (would break "no spaces"); fine under
  GNU `wc` on the Linux grader. `$11` may be bracketed for kernel threads.

### Q3 - [q3/decipher.sh](q3/decipher.sh) - **Appropriate**

**Checked vs spec:** usage guard (✓); `wget -q ... -O encrypted.txt` quiet download (✓ (a));
loops `seq 0 25`, decrypts the `tail -1` last line with a `tr` rotation, `grep -qi
"Marie\|Majesty\|Queen\|Mary"`, `break` on first hit (✓ (b)); whole-file decrypt via
`tr ... < encrypted.txt > deciphered.txt` preserving newlines (✓ (c)); encrypts the fixed
plaintext with the **same forward** shift and appends with `>>` (✓ (d)). The decrypt rotation
(`back = 26 - s`) and encrypt rotation (`FOUND_SHIFT`) are mathematically correct inverses.

**Concrete gaps / notes:**

- Step (c) is correctly guarded by `[ "$FOUND_SHIFT" -ge 0 ]`, but step (d) is **not**: if no
  shift were found (`FOUND_SHIFT=-1`), `${LOWER:$FOUND_SHIFT}` is parsed as `${LOWER:-1}`
  (default-value operator) and yields the full alphabet rather than erroring. Benign for valid
  inputs but a latent edge case; guarding (d) too would be safer.

### Q4a - [q4/download.sh](q4/download.sh) - **Appropriate (alternative approach)**

**Checked vs spec:** usage guard for 2 args (✓); `wget -q --recursive --no-parent --reject
"index.html*" --reject "*.tmp"` (✓ - quiet, recursive, no-parent, rejects index + tmp);
renames the located directory to `mock_grading` (✓). Instead of `--cut-dirs`/`-nH`, it
downloads into a temp tree (`.download_tmp_$$`), then `find`s the directory whose name matches
`basename "${URL%/}"` and `mv`s it to `mock_grading` - a robust way to reach the same end
state.

**Concrete gaps / notes:**

- The `<cut-dirs argument>` (`$2`) is **accepted but ignored** (the script ends with a no-op
  `:`). The required outcome (a correctly-named, correctly-structured `mock_grading`) is still
  achieved via `find` + `mv`, so this is a deviation in *method*, not in result. If the grader
  inspects for `--cut-dirs` usage specifically, add it; if it only checks the resulting tree,
  this passes.

### Q4b - [q4/organise.sh](q4/organise.sh) - **Appropriate**

**Checked vs spec:** usage guard for 0 args (✓); creates `organised/` (✓); reads `roll_list`
with `while IFS= read -r roll` (✓); per roll, `mkdir -p organised/$roll` and globs
`submissions/${roll}*` creating `ln -sf ../../mock_grading/submissions/<file>` **relative**
links (✓). Glob guarded with `[ -f "$filepath" ]` (✓).

**Evidence (from [q4/organised/](q4/organised)):**

- `organised/220010001/220010001.cpp -> ../../mock_grading/submissions/220010001.cpp` -
  relative target confirmed.
- `organised/220010010/` correctly holds **two** links (`220010010foo.cpp`,
  `220010010README.txt`) for the multi-file student.
- `organised/220010005/` links the non-`.cpp` `220010005notes.txt` (a student with no `.cpp`),
  matching "link every submitted file".

No gaps found - matches the spec exactly.

### Q4c - [q4/evaluate.sh](q4/evaluate.sh) - **Appropriate**

**Checked vs spec:** usage guard for 0 args (✓); builds a sorted input array via `find ... -name
'*.in' | sort` (✓); zero-initialised `distribution` array sized to inputs (✓); compiles the
single `.cpp` from inside `organised/<roll>` with `( cd ... && g++ -o executable ... 2>/dev/null )`
(✓); runs each input under `timeout 5 ./executable < in > student_outputs/out 2>/dev/null`,
with a Perl-`alarm` fallback when `timeout`/`gtimeout` is absent (✓); `diff -q` exact compare,
`score`/`distribution` incremented on match (✓); `marksheet.csv` written then `sort`ed in
place (✓); `distribution.txt` one line per input as `<name>, <count>` (✓). Output formats
match both examples (`roll,score` no space; `name, count` with a space).

**Evidence (from [q4/marksheet.csv](q4/marksheet.csv) + [q4/distribution.txt](q4/distribution.txt)):**

- Internal consistency check: sum of marksheet scores = `20+15+10+5+0+0+19+15+12+18 = 114`;
  sum of distribution counts = `114`. The two independent tallies agree exactly - strong
  evidence the per-testcase scoring is correct.
- Students with no `.cpp` / broken `.cpp` (`220010005`, `220010006`) score `0`, as expected.

**Concrete gaps / notes:**

- `distribution.txt` lines are in lexicographic input order (`0,1,10,11,...,19,2,...`) rather
  than numeric `0..19`. The spec does not require numeric order, so this is cosmetic; sort
  numerically (`sort -n`) if a strict `0..19` sequence is desired.
- The `| :` appended to the run command is a harmless attempt to absorb shell job-control
  noise; stdout is already captured by `>`, so it has no functional effect.

### Validation summary

| Question | File | Status |
|---|---|---|
| Q1 | [pdfWordCounter.sh](q1/pdfWordCounter.sh) | Appropriate |
| Q2 | [downloadContents.sh](q2/downloadContents.sh) | Appropriate (caveats: self-inclusion, `-np`/requisites) |
| Q3 | [decipher.sh](q3/decipher.sh) | Appropriate (latent: unguarded step d) |
| Q4a | [download.sh](q4/download.sh) | Appropriate (alternative; `cut-dirs` arg ignored) |
| Q4b | [organise.sh](q4/organise.sh) | Appropriate (links verified) |
| Q4c | [evaluate.sh](q4/evaluate.sh) | Appropriate (marksheet/distribution sums reconcile to 114) |

> **Caveat:** validation is by static inspection plus reading the committed `q4` evidence. The
> live-network parts (Q1/Q2/Q3/Q4a `wget` downloads) and `g++`/`timeout` behaviour should be
> re-run on the Linux grading environment to confirm end-to-end, consistent with the
> report-only scope.
