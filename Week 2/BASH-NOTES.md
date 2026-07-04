# Bash CLI + Shell Programming - Comprehensive Study Notes

> Distilled from the two Week 2 decks - *Unix Command Line Interface (CLI)* (23 slides) and
> *Shell Programming* (28 slides) - organized around what the Bash assignment actually
> tests. Use this as the concept reference; use `ASSIGNMENT-APPROACH.md` for the
> step-by-step solving guide.

A shell is two things at once: an **interactive command interpreter** you type at, and a
**programming language** you write scripts in. The two decks split exactly along that line.
The first deck is the *vocabulary* - the individual Unix commands (`ls`, `grep`, `wget`,
`tr`, `ps`, ...) and the regular-expression engine that powers searching. The second deck
is the *grammar* - how to glue those commands together with variables, conditionals, loops,
and functions inside a `.sh` script. This document follows that journey:

1. **The CLI** - command syntax, the filesystem, permissions, searching, and the text /
   process toolkit.
2. **Shell programming** - shebang, variables, conditionals, patterns, loops, functions, and
   the environment / visibility model (child shells vs subshells).

Almost every line of the assignment is a small composition of these two halves: download a
file with `wget`, transform it with `tr` / `grep` / `pdftotext`, and wrap the whole thing in
a script that validates its arguments and loops over inputs.

---

## 0. How the lectures map to the assignment

| Deck topic | Source slides | Assignment problem it supports |
|---|---|---|
| Command syntax (`cmd option arg`), `man` | CLI 3-4 | All (usage strings, switches) |
| `wc` (count lines / words / chars) | CLI 5 | Q1 (counting word occurrences) |
| Permissions, `chmod`, inodes, `ln -s` | CLI 6-12 | Q4b (symbolic links), making scripts executable |
| `diff` (compare line by line) | CLI 14-16 | Q4c (compare student vs expected output) |
| `grep` / `egrep`, BRE vs ERE | CLI 17-19 | Q1 (`grep -wi`), Q2e, Q3b (case-insensitive match) |
| `ps`, `kill`, system status | CLI 20 | Q2e (process name for a given PID) |
| `cut`, `tr`, `sort`, `wget`, `basename` | CLI 22 | Q1-Q4 (`tr` ciphers, `sort` marksheet, `wget` downloads) |
| Shebang, `read`, executable scripts | Shell 4-5 | All scripts (`#!/bin/bash`) |
| Positional parameters `$0 $1 $# $? $$` | Shell 7-8 | All (argument parsing, usage check via `$#`) |
| `if` / `test` / `[ ]` / `[[ ]]`, operators | Shell 9-13 | All (usage guards, file tests) |
| `case` + glob / extglob | Shell 14-15 | Q3 (shift search), pattern matching |
| `while`, `$(( ))`, `IFS` read | Shell 17-19 | Q3 (loop over 26 shifts), Q4 (read `roll_list`) |
| `for`, `continue` / `break`, `select` | Shell 20-21 | Q4b/c (iterate submissions & inputs) |
| Functions, `local`, `return` / `$?` | Shell 22-23 | Reusable logic, exit-status checks |
| `source` vs child shell vs subshell, `export` | Shell 24-27 | Q4 (`(cd ...; g++ ...)` subshells) |

The four problems line up with the toolkit cleanly: **Q1 = download + count**, **Q2 =
crawl + report + process lookup**, **Q3 = cipher with `tr`**, **Q4 = a full autograder**
exercising loops, links, subshells, `g++`, `diff`, `timeout`, and `sort`.

---

## 1. The command line model

### 1.1 Anatomy of a command

```
ls -ltr Dropbox
^^ ^^^^ ^^^^^^^
command options argument
```

`ls -ltr Dropbox` means *list the contents of `Dropbox`, in long format (`-l`), sorted by
time (`-t`), in reverse order (`-r`)*. Key rules:

- Options (a.k.a. switches/flags) modify behaviour; they may be **bundled** (`-ltr`) or
  separate (`-l -t -r`).
- Some options have a **verbose** long form: `ls -lt --reverse Dropbox`.
- `man <command>` is itself a command - it documents every other command (`man ls`).

### 1.2 File-management commands worth memorizing

| Command | Purpose |
|---|---|
| `cat` | Concatenate files and print them |
| `cp`, `mv` | Copy / move (or rename) files and directories |
| `ls`, `tree` | List files; `tree` shows the hierarchy |
| `chmod`, `chgrp`, `chown` | Change mode / group / owner |
| `mkdir`, `rm`, `rmdir` | Make / remove directories and files |
| `ln`, `ln -s` | Create a hard / symbolic link |
| `pwd` | Print working directory |
| `less` | Page through a file forward and backward |
| `wc` | Count **l**ines (`-l`), **w**ords (`-w`), **c**haracters (`-c`) |
| `head`, `tail` | First / last few lines of a file |

`wc` is the workhorse for Q1: pipe matches into `wc -l` to count them.

---

## 2. Permissions, inodes, and links

### 2.1 Reading an `ls -l` line

```
-rwx--x--- 1 sanyal testgroup 136 Aug 3 21:04 test.sh
^          ^ ^      ^         ^   ^            ^
type       | owner  group     size date         name
           links
```

The first character is the **type** (`-` regular file, `d` directory, `l` symlink). The
next nine characters are three triads - **owner**, **group**, **others** - each `rwx`:

- `-rwx--x---` : not a directory; owner has read/write/execute; group has execute only;
  others have nothing.
- `drwxrw-r-x` : a directory; for a directory `r` = list files, `w`+`x` = add/delete files,
  `x` = `cd` into it. The `w` bit is meaningless without `x`.

### 2.2 Changing permissions with `chmod`

Octal form `chmod NNNN filename`, where each digit is the sum of `r=4`, `w=2`, `x=1`:

```bash
chmod 750 test.sh    # owner rwx(7), group r-x(5), others ---(0)
chmod +x script.sh   # symbolic form: add execute for everyone
```

Making a script executable (`chmod +x script.sh`) is the precondition for running it as
`./script.sh`.

### 2.3 Inodes, hard links, and soft links

A file is split into an **inode** (properties: permissions, owner, timestamps, size,
pointers to data) and its **data blocks**. A directory entry just maps a *name* to an inode.

- `ln a.txt hlink` - a **hard link**: a second name pointing at the *same inode*. Both
  names are equal; the data survives until the last name is removed.
- `ln -s a.txt slink` - a **symbolic (soft) link**: a tiny file whose contents are the
  *path* to the target. If the target moves or is deleted, the link dangles.

> **Why this matters for Q4b:** the autograder must create *symbolic* links with **relative**
> targets (`ln -s ../../mock_grading/submissions/file.cpp link`) so the `organised/` tree
> references submissions without copying large files.

---

## 3. Comparing and searching files

### 3.1 The comparison family

| Command | Use |
|---|---|
| `cmp` | Compare two files byte by byte |
| `comm` | Compare items in two **sorted** files |
| `diff`, `diff3`, `meld` | Compare two (or three) files line by line |
| `find` | Search the tree by name/attributes and act on matches |
| `grep` | Search file contents for text patterns |
| `which`, `whereis`, `locate` | Locate commands / files on the system |

### 3.2 Reading `diff` output

`diff file1.txt file2.txt` reports the edits needed to turn **file1 into file2**:

```
0a1
> This is the zeroeth line.
2,3c3,4
< This is a second line
< This is a third line.
---
> This is a second line.
> This is a third line
5d5
< And that is all
```

- `0a1` - **a**dd, after line 0 of file1, content matching line 1 of file2.
- `2,3c3,4` - **c**hange lines 2-3 of file1 into lines 3-4 of file2.
- `5d5` - **d**elete line 5 of file1.
- `<` lines come from file1, `>` lines from file2.

> **Why this matters for Q4c:** comparing a student's output to the expected output is an
> exact-match test. Use `diff -q a b` (quiet: it only sets an exit status, prints nothing) and
> branch on `$?` - matching means score += 1.

---

## 4. Regular expressions with `grep` / `egrep`

`egrep` (= `grep -E`) prints every line containing a match for an **Extended Regular
Expression (ERE)**.

```bash
egrep line grep.txt              # lines containing "line"
egrep 'first|second' grep.txt    # alternation: "first" OR "second"
egrep '(Th)?is' grep.txt         # optional group: "This" or "is"
egrep '[a-z]{2,5}' grep.txt      # a run of 2-5 lowercase letters
ls -al | egrep '^d'              # lines (from ls) that start with d -> directories
```

### 4.1 Useful character classes and anchors

- `.` any single character; `*` zero-or-more of the preceding; `?` optional; `+` one-or-more.
- `[a-z]`, `[[:alpha:]]`, `[0-9]` - character classes.
- `^` start of line, `$` end of line.
- `{m,n}` - between m and n repetitions.

A full email matcher from the deck:

```bash
egrep '^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$' emails
```

### 4.2 BRE vs ERE - the gotcha that trips everyone

Plain `grep` uses **Basic Regular Expressions (BRE)**, in which `{ } ( ) | +` are *literal*
characters and must be **escaped** with `\` to act as operators. `egrep` / `grep -E` treats
them as operators directly.

```bash
egrep 'a|b' grep.txt   # alternation -> matches lines with a or b
grep  'a|b' grep.txt   # literal -> matches only lines containing the text "a|b"
```

### 4.3 The flags the assignment leans on

| Flag | Meaning | Where used |
|---|---|---|
| `-i` | Case-insensitive | Q1, Q2e, Q3b (`Break` == `break`) |
| `-w` | Whole-word match only | Q1 (`break.` matches, `breakfast` does not) |
| `-o` | Print only the matched part, one per line | Q1 (so `wc -l` counts occurrences) |
| `-q` | Quiet - no output, just an exit status | Q3b (test "did this shift contain Queen?") |
| `-v` | Invert - lines that do **not** match | General filtering |
| `-c` | Count matching **lines** (not occurrences) | Contrast with `-o | wc -l` |

> **Counting trap:** `grep -c` counts matching *lines*, so two occurrences on one line count
> as one. To count *occurrences*, use `grep -o ... | wc -l`. This is exactly why Q1 uses
> `grep -owi`.

---

## 5. System status and processes

| Command | Use |
|---|---|
| `date` | Show / set the date |
| `df` | Free disk space per mounted partition |
| `du` | Disk usage of files / directories |
| `env` | List environment variables |
| `ps` | Show processes (`ps aux` = all processes, detailed) |
| `stat` | File / filesystem status |
| `uname` | System information (`uname -a`) |
| `kill`, `pkill` | Terminate a process by PID / name |

### 5.1 Reading `ps aux`

`ps aux` prints a header then one line per process. The columns are
`USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND` - so **field 2 is the PID** and
**field 11 onward is the COMMAND**.

```bash
ps aux | awk 'NR>1 && $2==59 {print $11}'   # name of the process whose PID is 59
```

> **Why this matters for Q2e:** you compute a number `n` (the count of `{` in a JSON file)
> and must print the COMMAND of the process whose PID equals `n`, or `No such process` if
> none exists. `awk` with `$2==n` over `ps aux` (skipping the header with `NR>1`) does this.
> Note kernel threads appear bracketed (e.g. `[migration/7]`).

### 5.2 Disk partitions (context)

A disk is split into **partitions** (`/dev/nvme0n1p7`, ...), each **mounted** on a directory
of the single Unix tree (`/`, `/home`, `/boot/efi`). `df` shows partitions and mount points.
Separating user data from system data stops a full `/home` from freezing the OS.

---

## 6. Text-processing toolkit

| Command | Use |
|---|---|
| `cut` | Extract delimiter-separated fields of a line |
| `fmt` | Reflow text to a width |
| `paste` | Merge lines of files into tab-separated columns |
| `sort` | Sort lines by key (`-n` numeric, `-r` reverse, `-k` field) |
| `tr` | **Translate / delete characters** (set-to-set mapping) |
| `expand` | Convert tabs to spaces |
| `wget` | Download files / mirror sites over HTTP(S) |
| `basename` | Strip leading directory components from a path |

### 6.1 `tr` - the cipher engine

`tr SET1 SET2` replaces each character in SET1 with the character at the same position in
SET2; `tr -d SET` deletes; `tr -c SET` complements the set; combine as `tr -cd SET` (keep
only SET, delete the rest).

```bash
echo "Hello" | tr 'a-z' 'A-Z'      # -> HELLO   (translate)
tr -cd '{' < file.json | wc -c     # count just the '{' characters  (Q2d)
echo "abc" | tr 'abcdef' 'defabc'  # Caesar-style rotation by 3      (Q3)
```

> **Why this matters for Q3:** a Caesar shift is exactly a `tr` from the plain alphabet to a
> rotated alphabet. Build the rotated alphabet with Bash substring slicing and feed both to
> `tr`. Reading the file via `< encrypted.txt` preserves newlines; `echo "$x" | tr ...` works
> on a single line.

### 6.2 `wget` - fetching and mirroring

| Option | Effect |
|---|---|
| `-q` | Quiet (no progress output to the terminal) |
| `-O file` | Write the single download to `file` |
| `-r` / `--recursive` | Recursively follow links |
| `--no-parent` | Never ascend to a parent directory |
| `-p` / `--page-requisites` | Also fetch CSS / images needed to render a page |
| `--convert-links` | Rewrite links in downloaded HTML to point locally |
| `--domains d` | Restrict the crawl to domain(s) `d` |
| `-R pat` / `--reject pat` | Reject files matching the glob (e.g. `index.html*`, `*.tmp`) |
| `-P dir` / `--directory-prefix` | Save everything under `dir` |
| `-nH` / `--no-host-directories` | Don't create the `host/` top directory |
| `--cut-dirs=N` | Drop `N` leading path components from the saved layout |
| `-nd` / `--no-directories` | Don't recreate the directory structure |

> **Why this matters for Q2/Q4:** `--no-parent` + `--domains` enforce the crawl boundary;
> `-p` + `--convert-links` make the local copy self-contained; `-nH --cut-dirs=N` flatten the
> awkward `host/~user/.../target` nesting so the saved directory matches the remote name.

### 6.3 `basename` - deriving names from paths

```bash
basename /a/b/c/page.html        # -> page.html
basename "${URL%/}"              # strip a trailing slash first, then take the last component
```

`${URL%/}` is parameter expansion that removes a trailing `/`; useful before `basename` when
the URL ends in `/`.

---

## 7. Shell programming: structure and input

### 7.1 The shebang and the workflow

```bash
#!/bin/bash      # must be the FIRST line; selects the interpreter (portability)
```

Workflow: write commands into a `.sh` file -> `chmod +x file.sh` -> run as `./file.sh`.
Running `./file.sh` (or `bash file.sh`) starts a **child shell**.

### 7.2 Reading input with `read`

```bash
read -p "May I ask your name: " name   # -p prints a prompt; stores into $name
echo "Hello $name"                      # $name evaluates the variable
read -p "Number: " n                    # with no var, the value lands in $REPLY
read -n1 -p "Hit a key: " key           # -n1 reads exactly one character
exit 0                                   # explicit successful exit status
```

`$` means **evaluate**: `name` is the variable, `$name` is its value.

### 7.3 Variables and the special `$` parameters

User variables: assign with **no spaces** (`i=5`), read with `$` (`$i`). Environment
variables (inspect with `env`) include `PATH`, `HOME`, `PWD`.

| Parameter | Meaning |
|---|---|
| `$0` | Name of the current script |
| `$1` - `$9` | Positional parameters 1-9 |
| `$#` | Number of positional parameters |
| `$*` | All parameters as **one** string (`"$*"`) |
| `$@` | All parameters as **separate** strings (`"$@"`) |
| `$?` | Exit status of the most recent command |
| `$$` | PID of the current shell |

> **Why this matters for every problem:** the assignment requires a usage guard. The idiom is
> `if [ "$#" -ne 2 ]; then echo "Usage: ..."; exit 1; fi` - check the *number* of arguments
> with `$#` and exit non-zero on misuse.

---

## 8. Conditionals

### 8.1 The `if` skeleton and what a "condition" is

```bash
if conditional; then
    statements
elif conditional; then
    statements
else
    statements
fi
```

A "conditional" is **any command**; it is true when the command's exit status is `0`. So
`if ls -al; then ...` runs the then-branch when `ls` succeeds. Two equivalent ways to write
explicit tests:

```bash
test expression
[ expression ]     # note the REQUIRED spaces inside the brackets
```

### 8.2 The test operators

```bash
# strings
[ "$USER" = root ]      [ "$USER" != root ]
[ -n "$VAR" ]           # non-empty (length > 0)
[ -z "$VAR" ]           # empty (length == 0)

# integers
[ "$#" -gt 0 ]          # also -ge -lt -le -eq -ne

# files
[ -f "$1" ]             # is a regular file
[ -d "$1" ]             # is a directory
[ -r "$1" ] [ -w "$1" ] [ -x "$1" ]   # readable / writable / executable
[ -h "$1" ]             # is a symbolic link
[ file1 -nt file2 ]     # file1 is newer than file2
```

### 8.3 `&&`, `||`, `!`, and `[[ ]]`

Combine tests with `&&` (and), `||` (or), `!` (not) - and keep `&&` / `||` **outside** the
single brackets:

```bash
if [ "$Passed" = Y ] && [ "$CPI" -ge 8 ]; then ...
```

The doubled form `[[ ... ]]` is a Bash builtin that *does* allow `&&` / `||` / `<` inside it
and is safer with unquoted variables and globbing:

```bash
if [[ ! -f "$1" || ! -r "$1" || ! -w "$1" ]]; then
    echo "File $1 is not accessible"; exit 1
fi
```

> Rule of thumb: prefer `[[ ... ]]` for file/string tests; always quote variables (`"$1"`)
> to survive spaces and emptiness.

---

## 9. `case` statements and glob patterns

```bash
read -n1 -p "Hit a key: " key; echo
case $key in
    [a-z]) echo "$key is lower case" ;;
    [A-Z]) echo "$key is upper case" ;;
    [0-9]) echo "$key is a digit" ;;
    *)     echo "$key is something else" ;;
esac
```

Each branch ends with `;;`. The patterns are **globs**, not regexes:

| Pattern | Matches |
|---|---|
| `*` | Zero or more of any character |
| `?` | Exactly one character (`a.c??` matches `a.cvs`, `a.cpp`) |
| `[[:alpha:]]` | A single alphabetic character |
| `[yY][eE][sS]` | `yes`, `YES`, `YeS`, ... |

**extglob** (enable with `shopt -s extglob`, disable with `shopt -u extglob`) adds:

| Pattern | Matches |
|---|---|
| `@(p1\|p2)` | Exactly one of the patterns |
| `?(pat)` | 0 or 1 occurrence |
| `*(pat)` | 0 or more occurrences |
| `+(pat)` | 1 or more occurrences |
| `!(pat)` | Anything that does **not** match `pat` |

---

## 10. Loops

### 10.1 `while` and arithmetic

```bash
read -p "Give me a number: " n
i=1; fac=1
while (( i <= n )); do      # (( )) : arithmetic test, no $ needed on names
    fac=$(( fac * i ))      # $(( )) : evaluate arithmetic, substitute result
    (( i++ ))
done
echo $fac
```

- `$(( ... ))` evaluates an arithmetic expression to a **value** (substituted in place).
- `(( ... ))` evaluates for **side-effects / exit status** (status is `0` if the value is
  non-zero, i.e. arithmetic-true).

### 10.2 `while read` with a custom field separator

```bash
while IFS=: read userName passWord userID groupID genInfo homeDir userShell; do
    echo "$userName -> $homeDir"
done < /etc/passwd
```

Setting `IFS` (Internal Field Separator) splits each line into the named variables.

> **Why this matters for Q4:** iterate the `roll_list` file line by line with
> `while IFS= read -r roll; do ...; done < roll_list`. Use `IFS=` (empty) and `-r` to read
> raw lines without trimming whitespace or mangling backslashes.

### 10.3 `for`, `continue`, `break`

```bash
for args in *; do ls -al "$args"; done    # iterate over files (glob expands)

for index in 1 2 3 4 5 6; do
    if [ "$index" -le 3 ]; then
        echo "continue"; continue          # skip to next iteration
    else
        echo "break"; break                # leave the loop
    fi
done
```

To iterate over command output line-by-line (not word-by-word) set `IFS=$'\n'` first and
restore it afterward. For numeric ranges, `for s in $(seq 0 25)` or `for ((i=0;i<n;i++))`.

> **Why this matters for Q3:** loop `for s in $(seq 0 25)` over all 26 Caesar shifts; `break`
> as soon as a shift reveals a signature word.

### 10.4 `select` (menus)

```bash
select FILENAME in *; do
    echo "You picked $FILENAME ($REPLY)"
    chmod go-rwx "$FILENAME"
done
```

`select` prints a numbered menu and loops; `$REPLY` holds the chosen number.

---

## 11. Functions, scope, and the environment model

### 11.1 Defining functions and capturing status

```bash
check_file() {
    if [ -f "$1" ]; then return 0; else return 1; fi   # 0 = success, non-zero = failure
}
check_file "/etc/passwd"
status=$?                       # capture the return value
echo "The exit: $status"
```

`return` yields an **exit status** (0-255), not a value; capture it with `$?`. To return
*data*, `echo` it and capture with command substitution: `result=$(my_function)`.

### 11.2 `local` variables

```bash
var1='A'; var2='B'
my_function () {
    local var1='C'    # visible only inside the function
    var2='D'          # NO local -> modifies the global var2
}
my_function
# afterwards: var1 is still 'A', var2 is now 'D'
```

### 11.3 `source` vs child shell vs subshell

This is the trickiest concept and decides what state survives where.

| Mechanism | How it's created | What it sees / what propagates back |
|---|---|---|
| `source file.sh` (`. file.sh`) | Runs in the **current** shell | Imports all variables & functions into your shell; changes persist |
| **Child shell** (`./file.sh`, `bash file.sh`, running a non-builtin) | `fork()` then `exec()` | `exec` wipes inherited memory; sees only **exported** vars (`export`, `export -f`) and `PATH`/`HOME`; cannot write back to the parent |
| **Subshell** (`( ... )`, `$( ... )`, `` `...` ``, builtin in a pipe) | `fork()` only (no `exec`) | Inherits a **full copy** including locals and functions; still **cannot** write changes back to the parent |

```bash
export VAR=value          # make a variable visible to child shells
export -f my_function     # make a function visible to child shells

x=5
( x=$((x+1)); echo "Inside subshell: x=$x" )   # prints 6
echo "Back in parent: x=$x"                     # prints 5 - subshell change is lost
```

**What a subshell inherits from the parent:** exported env vars (`PATH`, `HOME`), shell vars
(`$1`, `$PPID`, `$PS1`), user variables and functions, the current working directory, and
file descriptors (stdin/stdout). **What the parent inherits from the subshell:** nothing -
the only way back is through a pipe / captured output.

> **Why this matters for Q4:** the autograder compiles and runs each student's code from
> *inside* that student's directory using a subshell: `(cd "$STUDENT_DIR" && g++ -o
> executable file.cpp)`. The `cd` is confined to the subshell, so the parent script's working
> directory is untouched after the parentheses close.

---

## 12. Tooling cheat-sheet

### 12.1 Commands

| Tool | One-liner |
|---|---|
| `wget -q -O f URL` | Download URL quietly into file `f` |
| `wget -r -np -p --convert-links --domains D -P dir URL` | Mirror within a boundary |
| `pdftotext file.pdf -` | Convert a PDF to text on **stdout** (`-` = stdout, no temp file) |
| `grep -owi W` | Count-friendly: only matches, whole-word, case-insensitive |
| `grep -qi P` | Test for a pattern silently (sets `$?`) |
| `tr A B` / `tr -d S` / `tr -cd S` | Translate / delete / keep-only characters |
| `tr -cd '{' < f \| wc -c` | Count occurrences of a single character |
| `md5sum f \| awk '{print $1}'` | Print only the checksum hash |
| `sort f -o f` | Sort a file in place |
| `diff -q a b` | Quiet exact comparison (exit status only) |
| `basename "${P%/}"` | Last path component, trailing slash stripped |
| `ps aux \| awk 'NR>1 && $2==n {print $11}'` | COMMAND of the process with PID `n` |
| `ln -s ../../target link` | Relative symbolic link |
| `tree -J dir > out.json` | Directory tree as JSON |
| `timeout 5 ./prog < in` | Kill `prog` if it runs longer than 5s |

### 12.2 Script constructs

| Construct | Meaning |
|---|---|
| `#!/bin/bash` | Shebang (first line) |
| `[ "$#" -ne 2 ] && { echo Usage; exit 1; }` | Argument-count guard |
| `"$1"`, `"$@"` | Positional args - always quote |
| `$(( a + b ))` | Arithmetic evaluation |
| `(( i++ ))` | Arithmetic side-effect |
| `${VAR:offset:length}` | Substring slicing (e.g. rotate an alphabet) |
| `${VAR%/}` | Strip trailing `/` |
| `while IFS= read -r line; do ...; done < f` | Read a file line by line |
| `for ((i=0;i<n;i++))` | C-style numeric loop |
| `result=$(cmd)` | Capture a command's stdout |
| `( cd d && cmd )` | Run `cmd` in a subshell so `cd` is local |
| `cmd 2>/dev/null` | Discard stderr |
| `cmd >out 2>&1` | Redirect stdout to file, stderr to stdout |

---

## 13. One-paragraph summary

Bash is simultaneously an interactive command interpreter and a small programming language.
The **CLI half** gives you a vocabulary of composable commands - file management (`ls`,
`cp`, `ln -s`, `chmod`), comparison and search (`diff`, `grep`/`egrep` with its BRE-vs-ERE
distinction), process and system inspection (`ps`, `kill`, `df`), and a text toolkit (`tr`,
`cut`, `sort`, `wget`, `basename`, `wc`, `pdftotext`). The **scripting half** gives you the
grammar to glue them: a shebang, `read` and positional parameters for input, `if`/`test`/
`[[ ]]` for decisions, `case` with glob patterns, `while`/`for`/`select` loops with
arithmetic and `IFS`-driven reads, and functions with `local` scope and exit-status returns.
Tying it together is the **environment model** - `source` runs in your shell, child shells
(`fork`+`exec`) see only exported state, and subshells (`fork` only) copy everything but
propagate nothing back - which is exactly the discipline an autograder needs when it compiles
and runs untrusted student code in isolation.

### Further reading

- [GNU Bash Manual](https://www.gnu.org/software/bash/manual/) - the authoritative reference.
- [BashGuide (Greg's Wiki)](https://mywiki.wooledge.org/BashGuide) - community best practices.
- [ShellCheck](https://www.shellcheck.net/) - paste a script; it flags quoting and logic bugs.
- [Advanced Bash-Scripting Guide (TLDP)](https://tldp.org/LDP/abs/html/) - the "heavy" stuff:
  process substitution, restricted shells, complex I/O redirection.
- The regular-expressions reference and the `wget`, `tr`, `find`, `ps`, `basename` man pages
  (`man wget`, `man tr`, ...).
