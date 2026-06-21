# Debugging & Profiling - Comprehensive Study Notes

> Distilled from the two Week 4 lecture decks - *GDB (The GNU Debugger)* (29 slides) and
> *Debugging and profiling tools* (57 slides) - organized around what the assignment actually
> tests. Use this as the concept reference; use `ASSIGNMENT-APPROACH.md` for the
> step-by-step solving guide.

A program that compiles and runs is not the end of the story. Real software has **logic
errors**, **memory errors**, and **performance bottlenecks** that only surface at runtime,
and none of them are visible from the source alone. This week is about the four tools that
let you observe a *running* binary from the outside:

- **`gdb`** - an interactive debugger that stops, steps, and inspects a live process.
- **`gprof`** - a function-level profiler that answers "where does the time go?".
- **`perf`** - a hardware-counter profiler that answers "why is the CPU slow?".
- **`valgrind`** - a binary-instrumentation framework that answers "where is the memory bug?".

The unifying idea is **observation of a process you did not write hooks into**: `gdb` borrows
the kernel's `ptrace` facility, `gprof` injects instrumentation at compile time, `perf` reads
the CPU's performance-monitoring unit, and `valgrind` JIT-rewrites the machine code with a
shadow memory model. This document follows that progression.

---

## 0. How the lectures map to the assignment

| Lecture topic | Deck / slides | Assignment problem it supports |
|---|---|---|
| GDB model: debugger vs debugged process, `ptrace`, `0xCC` | gdb 5-6; tools 7-8 | P1 background (why a stop event exists) |
| Compiling for debugging (`-g`, `readelf --debug-dump`) | gdb 3; tools 5 | P1 (need `-g` to read frames) |
| Breakpoints, stepping, `continue` | gdb 7-9; tools 9-11 | P1 (drive the program to each frame) |
| Printing, `display`, watchpoints | gdb 11-12; tools 13-14 | P1 (stop event fires on break/watch/step) |
| Examining the call stack, registers, memory | gdb 10, 13; tools 12, 15 | **P1** (read `rsp`/`rbp` + stack bytes) |
| Core dumps (`ulimit -c`, `gdb prog core`) | gdb 13; tools 15 | P1/P3 background (segfault triage) |
| GDB-Python API: `gdb.Value`, pretty-printers, **stop events** | gdb 14-27; tools 16-29 | **P1** (the `stack.py` stop handler) |
| `gprof`: `-pg` instrumentation, flat profile, call graph | tools 33-37 | Profiling background for P2 |
| `perf`: counters, `stat`/`record`/`report`/`annotate`, hyperfine | tools 38-47 | **P2** (the `ipc_bench` investigation) |
| `valgrind`: Memcheck, A/V bits, leak categories | tools 48-56 | **P3** (fix `problem.cpp`) |

The three problems line up almost exactly with the three tool families:
**P1 = gdb (+ Python API)**, **P2 = perf**, **P3 = valgrind**. `gprof` is taught as the
conceptual stepping-stone to `perf`.

---

## 1. The GDB execution model

### 1.1 Two processes, one conversation

Debugging is a dialogue between **two** processes:

- The **debugger process** (`gdb` itself) - reads your commands, holds debugger state
  (breakpoints, watchpoints, convenience variables, macros), and shows information about the
  debugged process (program variables, the PC).
- The **debugged process**, also called the **inferior** - your program. It runs until a
  breakpoint or the end, then is *forced to give up control* back to the debugger.

`gdb` can drive the inferior because the kernel exposes a tracing facility (`ptrace`). Running
`run` (or `start`) without any breakpoints just lets the program run to completion (or crash)
"with bugs and everything" - not very useful. The power comes from stopping it.

### 1.2 What happens internally (the `0xCC` trick)

A software breakpoint is implemented by **overwriting one instruction byte with `0xCC`** (the
x86 `int3` trap). The full handshake:

```
1. GDB: user types `break main`, then `run` (or `start`).
2. GDB: fork() -> waitpid()
3. Child: ptrace(PTRACE_TRACEME) -> execve("./buggyprog")
4. Kernel: stops the child at execve, wakes GDB via waitpid().
5. GDB (wakes): set_breakpoint(main); hands control back to the child.
6. Child (runs): hits 0xCC; hardware triggers an exception. Call this point p.
7. Kernel: halts the child with SIGTRAP, wakes GDB.
8. GDB (wakes): user inspects state and may set more breakpoints p':
     a. for each new point p': set_breakpoint(p');
     b. execute_instr_at(p);          # single-step past the restored byte
     c. ptrace(PTRACE_CONT); waitpid()
```

The two helper routines:

- `set_breakpoint(p)` - **read and save** the original instruction byte at `p`, then **write
  `0xCC`**.
- `execute_instr_at(p)` - **restore** the original byte at `p`, **execute** that one
  instruction, then **write `0xCC` back** so the breakpoint survives for next time.

Key takeaway: a breakpoint is not magic - it is a saved byte plus a trap, and the debugger
constantly swaps the real instruction in and out around it.

---

## 2. Compiling for debugging

Compile with `-g` so the debugger can connect the executable back to the source:

```bash
g++ -g buggyprog.cpp -o buggyprog
```

`-g` embeds **DWARF debug info** that answers questions the raw binary cannot:

- *What are the 10 source statements around the current point?* (line tables)
- *Which machine instructions implement `seriesValue += xpow/ComputeFactorial(k);`?*
- *What is the type of `seriesValue`?* (type info)
- *At what memory address / register is `seriesValue` stored?* (location lists)

You can read the same info without `gdb`:

```bash
readelf --debug-dump=line buggyprog   # line number -> machine code map
readelf --debug-dump=info buggyprog   # types and storage locations (grep for the variable)
```

> For the assignment's stack problem, also add `-O0 -fno-omit-frame-pointer` so the frame
> pointer (`rbp`) actually points at the frame base and the layout is not optimized away.

---

## 3. GDB basic usage

### 3.1 Starting and running

```bash
gdb buggyprog                 # load the program
gdb --args buggyprog a b c    # load it with command-line arguments
gdb buggyprog coredump        # post-mortem on a core dump (see section 5)
```

```
(gdb) run            # start; stops at the first breakpoint
(gdb) run arg1 arg2  # start with arguments
```

### 3.2 Setting breakpoints

```
(gdb) break lineno                 # line in the current file
(gdb) break function               # entry of a function
(gdb) break filename:linenum       # line in a specific file
(gdb) break filename:function
(gdb) tbreak ...                   # temporary breakpoint (auto-deletes after one hit)
(gdb) info breakpoints             # list all breakpoints
```

### 3.3 Reaching and resuming

```
(gdb) run        # reach the first breakpoint
(gdb) continue   # resume until the next breakpoint
```

### 3.4 Stepwise execution

| Command | Effect |
|---|---|
| `next` | execute the current line, **stepping over** any calls |
| `step` | execute the current line, **stepping into** a function call |
| `finish` | run to the **end of the current function** and return |

### 3.5 Locating yourself and listing source

```
(gdb) where      # current call stack (function calls leading here)
(gdb) bt         # backtrace - equivalent to where
(gdb) list       # ~10 source lines around the current line
```

### 3.6 Printing and auto-display

```
(gdb) print exp                  # evaluate any valid C/C++ expression
(gdb) print function::variable   # a variable scoped within a function
(gdb) print file::variable       # a variable defined in a specific file
(gdb) display exp                # auto-print exp every time execution stops
```

### 3.7 Watchpoints - break when *data* changes

```
(gdb) watch exp           # stop when the value of exp changes
(gdb) watch exp if cond   # stop only when exp changes AND cond is true
```

A watchpoint is the data-centric counterpart to a breakpoint: instead of "stop at this
*place*", it says "stop when this *value* changes". Like `step`/`next`/`break`, a watchpoint
hit is a **stop event** - which is exactly the hook the assignment's `stack.py` listens for.

---

## 4. Examining memory and the stack frame

This section is the conceptual core of assignment Problem 1.

### 4.1 The call stack and activation records

Every function call creates an **activation record** (stack frame) holding local variables,
saved registers, arguments, and return information. Variables and scope are *language-level*
concepts, but their runtime realization is the **call stack** maintained by the compiled
program.

On x86-64 two registers delimit the *current* frame:

- **`rbp` (base pointer)** - address of the **base (bottom)** of the current frame.
- **`rsp` (stack pointer)** - address of the **top** of the current frame.

The stack **grows toward lower addresses**, so a callee's frame sits at *lower* addresses
than its caller's, and always **`rbp >= rsp`**. Think of memory as a byte array where an
address is just an index into it:

```
[ ... 0x23 0x9f 0xa0 0x55 0x6b 0xff ... ]
        ^                        ^
       rsp                      rbp
     (0x4000)                 (0x4003)
```

### 4.2 Reading registers and memory in GDB

```
(gdb) info registers rsp rbp     # raw register values
(gdb) p $rsp                     # registers are convenience variables ($rsp, $rbp, $pc)
(gdb) x/16xb $rsp                # examine 16 bytes in hex, starting at rsp
(gdb) x/gx 0x7fffffffdbf0        # examine one 8-byte (giant) word in hex
```

The `x` (examine) command takes a count, a format (`x` hex, `d` decimal, `i` instruction),
and a size (`b` byte, `h` half, `w` word, `g` giant/8-byte). On AArch64 the equivalents are
`sp` (stack pointer) and `x29`/`fp` (frame pointer) - worth knowing because grading machines
differ.

### 4.3 The same data, programmatically (bridge to section 6)

Registers and arbitrary memory can be read from the **GDB-Python API** instead of by hand,
which is what lets a script print the whole frame automatically on every stop. That is the
assignment task: walk from `rsp` up to `rbp + 16`, eight bytes at a time, and annotate which
rows `rsp` and `rbp` point at.

---

## 5. Debugging crashes with core dumps

A **core dump** is a snapshot of a crashed process's memory, written to disk, that you can
autopsy later.

```bash
ulimit -c unlimited                          # lift the core-size limit (default is 0)
sudo sysctl -w kernel.core_pattern=core      # save the dump as ./core
g++ -g crasher.cpp -o crasher && ./crasher   # compile with -g, run, crash
gdb ./crasher core.3669781                   # post-mortem
```

Inside `gdb` on a core file you can **examine but not run**:

| Command | Use |
|---|---|
| `bt` | backtrace - the call stack at the moment of the crash |
| `up` / `down` / `frame n` | navigate to the nth frame |
| `info locals` | examine local variables in the selected frame |
| `disassemble`, `info registers` | machine-level state |
| `info proc mappings` | the virtual memory map - did the crash touch an **unmapped** region? |

The `info proc mappings` step is the classic segfault triage: compare the faulting address
against the mapped segments to see whether the program dereferenced something outside its
address space (a null/wild pointer).

---

## 6. Advanced GDB: the Python API

Native GDB output is cumbersome for complex data (`std::unique_ptr`, user-defined trees). For
example, `disable pretty-printer` then `p node_ptr` on a `std::make_unique<Node>` dumps a wall
of nested `_M_t` / `_Head_base` internals. The **GDB-Python API** lets you extend GDB to
traverse in-memory objects and synthesize readable views.

### 6.1 `gdb.Value` - the bridge between C++ and Python

```python
bt_node = gdb.parse_and_eval('bt')   # parse+evaluate a C/C++ expression -> gdb.Value
```

- `gdb.parse_and_eval(expr)` evaluates an expression *from the debugged program* and returns
  a `gdb.Value`.
- For a pointer value, `val.dereference()` returns the `gdb.Value` of its pointee.
- Structs/classes/unions behave like dictionaries: `node['key_value']`, `node['left']`.

### 6.2 Walking a structure into a Graphviz `.dot` file

The lecture's running example walks a binary tree and emits a `.dot` description:

```python
import io

def print_tree(nodeptr):
    if nodeptr == 0x0:
        return ""
    node = nodeptr.dereference()
    node_name = "node" + str(node['key_value'])
    outfile.write(node_name + "[ label = " + "\"" + str(node['key_value']) + "\"" + "];\n")
    left_name  = print_tree(node['left'])    # recurse left
    right_name = print_tree(node['right'])   # recurse right
    if left_name != "":
        outfile.write(node_name + "-" + left_name  + "[ label = \"L\"];\n")
    if right_name != "":
        outfile.write(node_name + "-" + right_name + "[ label = \"R\"];\n")
    return node_name

outfile = open("out.dot", "w+")
outfile.write("digraph G { \n")
outfile.write("splines=line; \n")
bt_node = gdb.parse_and_eval('bt')
print_tree(bt_node['root'])
outfile.write("}")
outfile.close()
```

Run it from inside a stopped session with `(gdb) source test_gdb.py`, then render the
resulting `out.dot` with `xdot out.dot` (or a VS Code dot-preview extension).

### 6.3 Registering a type-based pretty-printer

Instead of `source`-ing a script at every stop, embed the logic as a pretty-printer so plain
`p bt` triggers it:

```python
class TreePrinter:
    def __init__(self, val):
        self.val = val
    def to_string(self):
        global outfile
        nodeptr = self.val['root']
        outfile = open("out.dot", "w+")
        outfile.write("digraph G { \n")
        outfile.write("splines=line; \n")
        print_tree(nodeptr)
        outfile.write("}")
        outfile.close()
        return ""                       # we wrote a file; nothing to inline-print

def lookup_type(val):
    if str(val.type) == 'btree':
        return TreePrinter(val)
    return None

gdb.pretty_printers.append(lookup_type)  # register; source this from ~/.gdbinit
```

The recipe in one line: write `XPrinter(val)` with a `to_string`, write `lookup_type(val)`
that maps a value of type `X` to `XPrinter(val)`, register `lookup_type`, and `p val` will run
`XPrinter(val).to_string()`.

### 6.4 Triggering actions on events (the key to Problem 1)

Rather than re-typing a command, **connect a handler to an event**. The event of interest is
the **`stop` event**, fired whenever the inferior stops on a breakpoint, watchpoint, `step`,
or `next`:

```python
import gdb

def stop_handler(event):
    # 'event' carries details; not needed here.
    bt_val = gdb.parse_and_eval('bt')
    printer_output = str(bt_val)   # forces GDB's pretty-print lookup -> TreePrinter.to_string()

gdb.events.stop.connect(stop_handler)
```

This is precisely the mechanism the assignment's `stack.py` must use: connect a handler to
`gdb.events.stop`, and inside it read `$rsp`/`$rbp` and dump the stack memory. That is the
"trigger an activity during an event" pattern the slides describe (and the videos omit).

---

## 7. The GNU profiler: `gprof`

`gprof` is a function-level profiler for C, C++, and Fortran. It reports **how much time** is
spent in each function and **how often** functions are called. Granularity is the **function
level** - it does *not* attribute cost to individual statements.

### 7.1 How it works

- **Instrumentation** (via `-pg`): the compiler inserts a profiling hook at every function
  entry, building a weighted call graph where edges are calls and weights are **exact call
  counts**.
- **Sampling**: a timer interrupts the program at regular intervals (e.g. every 10 ms) and
  records the current program counter (PC).
- **Symbolication**: sampled addresses are mapped to function names via symbol/debug info
  (`-g` improves accuracy), identifying which function was executing at each sample.
- **Combination**: call counts + sampled time produce a call graph annotated with costs.

### 7.2 Workflow

```bash
g++ -std=c++11 -pg -O2 -o search search.cpp   # compile with profiling support
./search                                       # run -> produces gmon.out
gprof -q ./search gmon.out                     # call graph only
gprof -p -q ./search gmon.out                  # flat profile + call graph
```

### 7.3 Reading the call graph

A call-graph entry centers on one function (the line for index `[2]`, shaded in the slide):

```
Index  % time  Self  Children  Called             Function
                0.45  0.62      1/1                  main         <- caller of quicksort
                      13,335,988                     quicksort    <- quicksort calls itself
[2]    83.3    0.45  0.62       1 + 13,335,988       quicksort    <- the subject line
                      13,335,988                     quicksort    <- callee (itself)
```

- The lines *above* the subject are its **callers**; the lines *below* are its **callees**.
- `Self` = time in the function's own body; `Children` = time in functions it called.
- `Called` `1 + 13,335,988` = one call from `main` plus 13,335,988 recursive self-calls.
- `% time 83.3` = cumulative share over all calls to `quicksort`.

**Drawback:** the information stops at the function boundary - it cannot tell you *which
statement* inside `quicksort` is hot. That limitation is exactly what `perf` overcomes.

---

## 8. Linux `perf`: hardware-counter profiling

`perf` monitors CPU usage at multiple granularities to find bottlenecks, using **hardware
performance counters** plus sampling.

### 8.1 How it works

- Modern CPUs keep special-purpose counters for low-level events: **cycles**, **instructions**,
  **cache-misses**, **branch-misses**.
- `perf` asks the kernel to interrupt the program either (1) at **fixed time intervals**
  (e.g. every 10 ms) or (2) on a **specific event** (e.g. overflow of the branch-miss counter).
- At each interrupt it records the instruction pointer (PC); with `-g` it also records the
  **call stack**.
- Over many samples this yields a statistical picture of *where time is spent*, *which
  branches miss*, and *where cache misses occur*.
- **Flat** reports summarize which functions were active; **call-graph** reports summarize
  which call chains were active.

### 8.2 The command set

```bash
g++ -g -o search search.cpp                  # 1. compile with -g

perf record -F 10000 -g ./search             # 2a. sample at 10 kHz, capture call stacks
perf record -e branch-misses -g ./search     # 2b. sample on branch-miss overflow
                                             #     -> both write perf.data

perf report -n --no-children                 # 3. interactive report, sorted by % overhead
perf report -n --no-children --stdio > out   #    non-interactive dump to a file

perf annotate --stdio -s "quicksort(...)"    # 4. per-instruction cost for one function

perf stat -e cycles,instructions ./search    # 5. quick aggregate counters (IPC, etc.)
```

> `perf report` opens an interactive TUI unless you pass `--stdio`. Use arrow keys to
> navigate, Enter to drill in, `q` to quit.

### 8.3 IPC and the flat report

`perf stat` reports **insn per cycle (IPC)**. A healthy CPU-bound program sustains **2-4 IPC**
on modern hardware; a much lower number means the core is **stalled** (waiting on memory,
coherence traffic, mispredicted branches, or division) rather than retiring instructions. The
final `user time` / `sys time` lines matter too: a user-space program that makes *no explicit
system calls* but shows large **sys time** is secretly entering the kernel - typically via
`sched_yield` under contention or allocator internals (`mmap`/`brk`, arena locks).

### 8.4 `perf annotate` - statement-level cost

Where `gprof` stops at the function, `perf annotate` maps cycle percentages onto **individual
assembly instructions** (and, with `-g`, source lines). Example: a single `vec[low]` access
expands into a costly sequence (load index, sign-extend, load `&vec`, marshal args, `call
operator[]`, dereference, store) that collectively eats samples - invisible to `gprof`.

### 8.5 Measuring improvements: `hyperfine`

To compare versions, time them with warm-up runs:

```bash
g++ -O0 -o search_1 search_1.cpp
hyperfine --warmup 3 ./search_1   # 3 warm-up runs, then 10 measured runs
# Time (mean +/- std):  2.759 s +/- 0.081 s   [User: 2.745 s, System: 0.013 s]
```

### 8.6 Optimization lessons from the case study

The lecture optimizes a quicksort+search benchmark and records the takeaways:

| Step | Change | Idea |
|---|---|---|
| Opt 1 | `std::vector` access -> raw array pointer | remove `operator[]` call + double-deref |
| Opt 2 | recurse on smaller half, loop on larger | ~50% fewer recursive-call overheads |
| Opt 3 | inline `std::swap` as 3 `mov`s | avoid call+prologue+epilogue in the hot loop |
| Opt 4 | iterative pointer-based binary search | remove per-recursion `operator[]` |
| Opt 5 | `-O3` | let the compiler change memory layout / use the ISA |

General conclusions: **abstractions have a cost** (a `std::vector` adds call overhead,
double-dereferencing, and pipeline-stalling data dependencies); recursion is *not* always slow
(for O(log N) depth the call cost is negligible); **reducing work in the inner loop** pays
most; manual gains shrink as you approach a "local maximum" for a given `-O` level; and
**aggressive compiler optimization (`-O3`) can outweigh several manual refinements combined**.

---

## 9. `valgrind`: dynamic memory analysis

Valgrind is a toolchain for **dynamic instrumentation** of binaries. Its tools include
**Memcheck** (leaks, use-after-free, uninitialized reads/writes), **Helgrind** (data races),
**Cachegrind** (cache simulation), and **Callgrind** (call-graph + instruction counts). This
course focuses on **Memcheck**.

### 9.1 How Memcheck works - shadow memory

- Valgrind translates machine code into an architecture-neutral **IR**, inserts checking
  logic, and JIT-compiles it back for the CPU.
- It maintains a **parallel metadata structure** ("shadow memory") for every byte of
  application memory (stack, heap, data, bss). Each byte carries:
  - **A-bits (Addressability)** - is the program *allowed* to access this byte? Set during
    `malloc`/`free` and stack growth.
  - **V-bits (Validity)** - does the location hold a *defined* value?
- For an instruction like `mov eax, [ebx]`, Valgrind checks the A-bit/V-bit at `ebx`
  **before** the real CPU executes it.
- Shadow memory is a multi-level sparse array (like OS page tables), allowing lazy allocation
  of shadow bits only where the program actually touches memory.
- This software-defined MMU is precise but incurs a **10-50x slowdown**.

### 9.2 How Memcheck detects leaks

- Valgrind keeps a hidden record of every active `malloc` (address, size, allocation stack
  trace), added at `malloc` and removed at `free`.
- Just before the process exits, it performs a **mark-and-sweep audit**: treating registers,
  the stack, and global segments (`.data`/`.bss`) as the **root set** of potential pointers,
  it chases them to see which heap blocks are still reachable.
- Each unfreed block is classified:

| Category | Meaning |
|---|---|
| **Still reachable** | a pointer to the block exists in the root set (sloppy, but not lost) |
| **Definitely lost** | no pointer exists anywhere - a true leak |
| **Indirectly lost** | reachable only via other lost blocks (e.g. the tail of a lost list) |

Doing the audit once at exit lets Valgrind report all leaks in one comprehensive summary.

### 9.3 Running Memcheck

```bash
gcc -g leaky_prog.c -o leaky_prog                 # -g so reports carry file:line

valgrind --leak-check=summary ./leaky_prog        # basic
valgrind --leak-check=full \
         --show-leak-kinds=all ./leaky_prog       # full diagnostics
# helpful: --track-origins=yes (sources of uninitialized values)
#          --log-file=vg.log    (write the report to a file)
```

### 9.4 Reading a leak report

```
==3141801== HEAP SUMMARY:
==3141801==     in use at exit: 37 bytes in 1 blocks
==3141801==   total heap usage: 6 allocs, 5 frees, 1,088 bytes allocated
==3141801==
==3141801== 37 bytes in 1 blocks are definitely lost in loss record 1 of 1
==3141801==    at 0x4848899: malloc (vgpreload_memcheck-amd64-linux.so)
==3141801==    by 0x109238: duplicate_and_trim (leaky_prog.c:13)
==3141801==    by 0x109356: main (leaky_prog.c:38)
==3141801== LEAK SUMMARY:
==3141801==    definitely lost: 37 bytes in 1 blocks
==3141801==    indirectly lost: 0 bytes in 0 blocks
==3141801==      possibly lost: 0 bytes in 0 blocks
==3141801==    still reachable: 0 bytes in 0 blocks
```

How to read it: **6 allocs vs 5 frees** => a true leak; the allocation **stack trace** names
the exact `file:line` of the leaking `malloc` (`main -> duplicate_and_trim -> malloc` at line
13); and `total bytes allocated` is larger than your own allocations because it includes
glibc's own heap (e.g. a 1 KB stdout buffer). The goal of the assignment's valgrind problem is
to make this report come back **clean** (zero lost, zero errors).

---

## 10. Tooling cheat-sheet

### 10.1 GDB commands

| Command | Use |
|---|---|
| `break` / `tbreak` `loc` | set a (temporary) breakpoint at line/function/file:line |
| `watch exp [if cond]` | break when a value changes |
| `run` / `continue` | start / resume to the next stop |
| `next` / `step` / `finish` | step over / step into / run to return |
| `bt` / `where` / `frame n` / `up` / `down` | inspect & navigate the call stack |
| `list` | show source around the current line |
| `print exp` / `display exp` | evaluate once / auto-evaluate on every stop |
| `info registers [reg]` | register values (`$rsp`, `$rbp`, `$pc`) |
| `x/NFU addr` | examine memory: count `N`, format `F` (`x`/`d`/`i`), unit `U` (`b`/`h`/`w`/`g`) |
| `info locals` / `info args` | locals / arguments of the selected frame |
| `disassemble` | machine code of the current function |
| `info proc mappings` | virtual memory map (segfault triage) |
| `source script.py` | run a GDB-Python script |

### 10.2 GDB-Python API

| API | Use |
|---|---|
| `gdb.parse_and_eval("expr")` | evaluate a program expression -> `gdb.Value` |
| `val.dereference()` | pointee of a pointer `gdb.Value` |
| `val['field']` | struct/class/union member access |
| `gdb.selected_inferior().read_memory(addr, n)` | read `n` raw bytes from the inferior |
| `gdb.events.stop.connect(handler)` | run `handler(event)` on every stop |
| `gdb.pretty_printers.append(lookup)` | register a type-based pretty-printer |

### 10.3 Compiler flags for tooling

| Flag | Tool | Meaning |
|---|---|---|
| `-g` | gdb / gprof / perf / valgrind | emit DWARF debug info (file:line, types, locations) |
| `-O0` | all | no optimization - layout matches the source (needed to read frames) |
| `-fno-omit-frame-pointer` | gdb | keep `rbp` as a real frame pointer |
| `-pg` | gprof | insert per-function profiling hooks (-> `gmon.out`) |
| `-O2` / `-O3` | perf | optimized builds (note: inlining can hide small functions) |
| `-pthread` | perf/valgrind | link POSIX threads |

### 10.4 Profilers / analyzers

| Command | Use |
|---|---|
| `gprof -p -q ./prog gmon.out` | flat profile + call graph (function granularity) |
| `perf stat ./prog` | aggregate counters: cycles, instructions, IPC, faults, user/sys |
| `perf record -g ./prog` | sample into `perf.data` (with call stacks) |
| `perf report --stdio` | overhead by symbol / call chain |
| `perf annotate --stdio -s "fn"` | cycle % per assembly instruction (statement granularity) |
| `hyperfine --warmup 3 ./prog` | statistical wall-clock benchmarking |
| `valgrind --leak-check=full --show-leak-kinds=all ./prog` | Memcheck leak diagnostics |

---

## 11. One-paragraph summary

Debugging and profiling are about **observing a running binary from the outside**. `gdb` stops
the inferior with the kernel's help (the `0xCC`/`ptrace` handshake), then lets you step,
inspect the call stack and registers, examine raw memory, and - through the Python API - react
to **stop events** and synthesize custom views of program state. When the program is correct
but slow, `gprof` gives a function-level picture from `-pg` instrumentation and sampling, while
`perf` drills to the **instruction** using the CPU's hardware counters, exposing stalls,
cache-misses, branch-misses, and a true IPC. When the program corrupts or leaks memory,
`valgrind`'s Memcheck shadows every byte with addressability/validity bits and runs an exit-time
mark-and-sweep to classify leaks as definitely / indirectly lost or still reachable. Together
they cover the three failure modes that compilation cannot catch: **logic errors, performance
bottlenecks, and memory errors.**

### Further reading

- *Debugging with GDB: The GNU Source-Level Debugger* - Stallman, Pesch, et al. (the canonical
  reference, by GDB's original author).
- GDB Python API documentation - for pretty-printers and event handlers.
- *Linux perf Examples* - Brendan Gregg; plus `man perf` and the Linux Perf tutorial.
- *Valgrind User Manual* (Memcheck chapter) - the authoritative guide to leak categories and
  flags.
- *Computer Systems: A Programmer's Perspective* (CSAPP), Bryant & O'Hallaron - Ch. 3 (machine
  code, the stack) and Ch. 5-6 (optimization, the memory hierarchy).
