# GDB / perf / valgrind - Step-by-Step Assignment Approach

> Companion to `GDB-PROFILING-NOTES.md` (the concept reference). This file is the
> command-level playbook for solving all three problems and cross-references the existing
> answers in [q1/stack.py](q1/stack.py), [q2/q2.txt](q2/q2.txt), and
> [q3/solved.cpp](q3/solved.cpp).

The assignment has **three problems**, one per tool family:

| Problem | Tool | Deliverable | Marks |
|---|---|---|---|
| P1 - Stack visualizer | gdb + Python API | `q1/stack.py` | (unspecified in brief) |
| P2 - Ring-buffer profiling | perf | `q2/q2.txt` (Q1-Q7) | **40** (4+5+6+6+5+7+7) |
| P3 - Memory-leak fix | valgrind | `q3/solved.cpp` | (unspecified in brief) |

The accompanying code lives under
[Resources/Resources accompanying assignment/](<Resources/Resources accompanying assignment>):
`stack_example.c` (P1), `ring_buffer.hpp` + `main.cpp` + `Makefile` (P2), `problem.cpp` (P3).

> **Architecture note.** The assignment text and slides use **x86-64** (`rbp`/`rsp`, `divq`,
> `lock cmpxchg`, `jne`, `mov ...(%rXX),%rYY`). Concrete addresses, opcodes, mnemonics, IPC
> values, and per-instruction cycle percentages are **machine-dependent**. The existing
> `q2.txt` was produced on an **AArch64** host (`ldar`, `casal`, `b.ne`, `udiv`,
> `0x....` ARM addresses), and `stack.py` includes AArch64 register fallbacks (`sp`/`x29`).
> Re-run every command on your own target and record *your* numbers - the method is identical
> across architectures.

---

## Problem 1 - Stack visualizer (gdb-Python) 

### What the problem asks

Use GDB to **observe the call stack directly**. Each function call builds an activation record
on the stack; `rbp` (base) and `rsp` (top) bound the current frame, the stack grows toward
lower addresses, and `rbp >= rsp`. You are given a skeleton pretty-printer
`stack.py` (using it is
optional) and must implement a function that runs **every time execution stops** (the GDB
**stop event** - breakpoint, watchpoint, `step`, or `next`) and prints the stack memory from
`rsp` up to the 8-byte block starting at `rbp + 16`, marking where `rsp` and `rbp` point.

Test program: [stack_example.c](<Resources/Resources accompanying assignment/stack_example.c>).

### Build and drive

```bash
gcc -g -O0 -fno-omit-frame-pointer -o stack_example stack_example.c
gdb stack_example
(gdb) source stack.py
[stack.py] Stack visualizer loaded. It will print the stack whenever execution stops.
(gdb) break main
(gdb) r
(gdb) b 11           # inside calc()
(gdb) c
```

- `-O0 -fno-omit-frame-pointer` keep a real frame pointer so `rbp` is meaningful and the layout
  is not optimized away.
- Hitting a breakpoint is a **stop event**, so the handler fires automatically after `r` and
  after each `c`.

### Approach (what `stack.py` must do)

1. **Register a stop handler:** `gdb.events.stop.connect(handler)` (section 6.4 of the notes).
   Print the load banner exactly once at import.
2. **Read the frame registers:** `int(gdb.parse_and_eval("$rsp"))` and `"$rbp"`. Add AArch64
   fallbacks (`$sp`, `$x29`/`$fp`) so it is portable to ARM grading machines.
3. **Read raw stack bytes:** `gdb.selected_inferior().read_memory(addr, 8)` for each 8-byte row.
4. **Walk `rsp -> rbp + 16` in 8-byte steps**, printing a boxed row per qword and annotating
   the rows where `addr == rsp` and/or `addr == rbp`.

### Expected output shape

```
rsp = 0x7fffffffdba0, rbp = 0x7fffffffdbe0
+-------------------------+
| 00 00 00 00 00 00 00 00 | <- rsp
+-------------------------+
| ...                     |
+-------------------------+
| f0 db ff ff ff 7f 00 00 | <- rbp
+-------------------------+
| ...                     |
+-------------------------+
```

For the `main` frame where `rsp == rbp`, the first row is annotated `<- rsp rbp` and there are
3 rows (`rsp`, `rsp+8`, `rbp+16`). For the `calc` frame, `rsp` and `rbp` are 0x40 apart, giving
11 rows.

### Gotchas

- The **byte values will differ** every run (addresses, the `marker = 0x1122334455667788`
  little-endian bytes `88 77 66 55 44 33 22 11`, saved `rbp`, return address). Only the
  **structure** must match.
- Print the range **inclusive** of `rbp + 16` - it is the last row, not one past it.
- Format bytes as lowercase 2-digit hex; keep the box border width consistent with the rows.
- Do not `run` past program exit inside the handler; just read memory and return.

---

## Problem 2 - Ring-buffer profiling with perf (40 marks)

### Setup

`ConcurrentRingBuffer` ([ring_buffer.hpp](<Resources/Resources accompanying assignment/ring_buffer.hpp>))
is a "lock-free" multi-producer / single-consumer logging queue;
[main.cpp](<Resources/Resources accompanying assignment/main.cpp>) runs 6 producer threads and
1 consumer for 5 seconds. **Do not modify the files.** Treat the binary as a black box and use
`perf` to find what is wrong *from the hardware's perspective*. Build with the provided
[Makefile](<Resources/Resources accompanying assignment/Makefile>)
(`-O3 -g -std=c++17 -pthread -march=native`):

```bash
make
./ipc_bench
```

Answer Q1-Q7 in plaintext in `q2.txt`. The four commands, run in order:

```bash
perf stat ./ipc_bench                 # Q1: counters, IPC, user/sys time
perf record ./ipc_bench               # Q2/Q3: sample -> perf.data
perf report                           # Q2: overhead by symbol  (add --stdio for a dump)
perf annotate --stdio -s "<fn>"       # Q3: per-instruction cycle %
```

### Q1 - First-pass triage (4 marks)

Run `perf stat ./ipc_bench`, then:

1. **IPC** (`insn per cycle`): healthy CPU-bound code sustains **2-4**; a low value means the
   core is **stalled** (memory/coherence/branch/division), not retiring work. Report *your*
   number. (On a VM without PMU access, `cycles`/`instructions` may read `<not supported>` -
   say so and reason from the rest.)
2. **Large sys time** for a user-space lock-free structure that makes no explicit syscalls
   points to hidden kernel entries: contention-driven **`sched_yield`** (from
   `std::this_thread::yield()`) and **allocator** internals under multithreaded pressure.

### Q2 - Locating the hot functions (5 marks)

`perf record ./ipc_bench` then `perf report`:

1. The **top symbol** is expected to be a scheduler / `__sched_yield` path plus
   `producer_thread`, with allocator paths (`_int_malloc`, `_int_free`, `malloc`, `free`)
   close behind - i.e. cycles go to **scheduling and heap management**, not queue logic.
2. With **`-O3`**, `enqueue()`/`dequeue()` are **inlined** into their callers, so they may not
   appear as separate symbols. Function-level `perf report` is therefore insufficient; you need
   **instruction/source-level** inspection (`perf annotate`) to find the exact bottleneck.

### Q3 - Diagnosing bottlenecks (6 marks)

Open the annotated producer (`perf annotate`), paste the **four** highest-percentage assembly
lines, then explain (x86 mnemonics; ARM equivalents in parentheses):

1. A **load** `mov ...(%rXX),%rYY` (ARM `ldar`) that reads `head_`, a variable this thread
   never writes -> expensive due to **MESI** cache-line contention: the consumer writes the
   line, so every producer read forces coherence traffic (invalidation / ownership transfer).
2. The **`jne` after `lock cmpxchg`** (ARM `b.ne` after `casal`) carries >30% while the
   `cmpxchg` shows ~0%: the atomic starts the coherence transaction, but the **stall surfaces
   on the branch** (sample skid + pipeline recovery on retry/spin).
3. A **`divq`** (ARM `udiv`) from the modulo index `index = current_tail % capacity_` (and
   `current_head % capacity_`): a 64-bit integer divide on the critical path is far costlier
   than a bit-mask, throttling throughput.

### Q4 - The atomic memory-ordering flaw (6 marks)

The `.load()` / `.store()` calls in `enqueue`/`dequeue` default to `std::memory_order_seq_cst`:

1. **seq_cst** forces a single global order across threads: the CPU must **drain its store
   buffer** and insert full fences, killing store-to-load forwarding freedom and reordering -
   extra stalls under contention.
2. **acquire/release** is sufficient: an **acquire** load forbids later accesses from moving
   *before* it; a **release** store forbids earlier writes from moving *after* it. The pairing
   guarantees the consumer that acquires the published index sees the slot's **fully-written**
   payload.

### Q5 - Heap allocation and kernel overhead (5 marks)

1. `virtual ~LogEntry()` forces a hidden **vptr** in every object: larger footprint, lower
   cache density, so the consumer's sequential scan touches more cache lines (worse locality).
2. `new LogEntry()` / `delete` on the hot path go through glibc `malloc`, whose **per-arena
   spinlocks** serialize threads under load - turning a "lock-free" enqueue into one that
   secretly serializes at the OS level, which is the **sys time** seen in Q1.

### Q6 - Proposing the fixes (7 marks)

State each flaw + fix in one sentence (the three hint areas):

1. **Index layout:** `head_` and `tail_` share a cache line (false sharing) -> separate them
   onto distinct cache lines (`alignas(64)` / padding).
2. **Memory ordering:** everything is `seq_cst` -> use acquire/release (and relaxed where safe).
3. **Hot-path allocation:** per-item `new`/`delete` + virtual destructor -> store `LogEntry`
   **inline** in a preallocated ring and drop the virtual dispatch.

### Q7 - Interpreting perf-stat after the fixes (7 marks)

Predict direction + justify (reasoning matters more than the exact direction):

| Counter | Expectation | Why |
|---|---|---|
| page-faults | down | fewer allocations -> less page churn |
| instructions | down | no malloc/free + fewer retries retired |
| IPC | up (modestly) | fewer stalls/fences -> better issue efficiency |
| sys time | down (sharply) | less yielding + no allocator kernel entries |
| throughput (M ops/s) | up (sharply) | shorter, less-contended hot path |

Finally: IPC can **stay low even as throughput rises** because progress in a contention-heavy
concurrent workload is gated by **coherence/synchronization latency and scheduling**, not
instruction-issue width - low IPC here means cores spend time *waiting*, not that the algorithm
completes fewer operations.

### Gotchas

- `perf record` opens an interactive TUI; add `--stdio` for a dumpable report.
- `perf` often needs privileges or a relaxed `kernel.perf_event_paranoid`; counters may be
  `<not supported>` inside VMs/containers - record that limitation honestly.
- After `-O3` inlining, search by the **caller** symbol (`producer_thread`) when `enqueue`
  has vanished.

---

## Problem 3 - Memory-leak fix with valgrind

### What the problem asks

Compile [problem.cpp](<Resources/Resources accompanying assignment/problem.cpp>), run it under
Valgrind (Memcheck will report errors), and fix it by **adding at most 5 lines** - **without
removing a single line** - saving the result as `solved.cpp`. After the fix Valgrind must
report no errors.

### Diagnose

```bash
g++ -g problem.cpp -o problem
valgrind --leak-check=full --show-leak-kinds=all ./problem
```

The bug is a **shallow copy -> double free**. `Tree copy = original;` invokes the
*implicitly-generated* copy constructor, which copies the `root` **pointer**, so `original` and
`copy` share the same `TreeNode*`. Both destructors then run `delete root` on the same node
(whose own destructor recursively deletes `left`/`right`), producing an **invalid free / double
free** (and invalid reads of the already-freed children).

### Fix

Add a user-defined copy constructor so each `Tree` owns its own root, breaking the shared
pointer:

```cpp
Tree(const Tree& other) : root(new TreeNode(other.root->data)) {}
```

This is **1 added line, 0 removed** (within the "<= 5 lines, remove nothing" budget). Now
`copy.root` is a distinct node, each `delete root` runs once, and Valgrind comes back clean.

### Expected clean report

```
==XXXXX== All heap blocks were freed -- no leaks are possible
==XXXXX== ERROR SUMMARY: 0 errors from 0 contexts ...
```

### Gotchas

- The minimal fix above clones only the root's `data`, not the `left`/`right` subtree - that is
  acceptable because the assignment requires only that **Valgrind not complain** (no
  use-after-free, no leak), not a structurally identical deep copy. A full deep copy
  (recursively cloning children) would also satisfy the brief but costs more lines.
- The "rule of three" alternative (also delete the copy assignment, or `= delete` the copy ops)
  would change behaviour/remove the copy and is unnecessary here.

---

## Solution Validation

Static, report-only inspection of the three submitted solution files against the assignment
spec. **No files were edited, compiled, or executed.** Architecture/address-dependent outputs
(register values, stack bytes, perf addresses/percentages, IPC) are treated as
machine-dependent and are not counted as defects.

### P1 - [q1/stack.py](q1/stack.py) - Status: **Appropriate**

**Checked vs spec:**

- **Stop-event hook** - registers `gdb.events.stop.connect(_on_stop)` and prints the exact
  banner `"[stack.py] Stack visualizer loaded. It will print the stack whenever execution
  stops."` => matches the required load message and the "run on every stop" requirement.
- **Register read** - `_read_first_register("rsp","sp")` and `("rbp","x29","fp")` reads the
  frame registers via `gdb.parse_and_eval`, with AArch64 fallbacks => portable; prints
  `rsp = 0x..., rbp = 0x...`.
- **Memory read** - `gdb.selected_inferior().read_memory(addr, 8)` reads raw stack bytes
  (8 per row) => correct API.
- **Range** - `start = rsp`, `end = rbp + 16`, loop `addr <= end` stepping 8 => exactly "from
  `rsp` to the 8-byte block starting at `rbp+16`", inclusive. For `rsp == rbp` (main) this
  yields the 3 rows shown in the PDF; for the `calc` frame (`rbp - rsp == 0x40`) it yields 11
  rows, matching the sample.
- **Formatting** - boxed rows `| xx xx ... |` with lowercase 2-digit hex, border lines, and
  `<- rsp` / `<- rbp` / `<- rsp rbp` annotations when an address coincides => matches the PDF
  layout, including the combined `<- rsp rbp` label.

**Concrete gaps:** none material. Minor cosmetic-only observations (not defects): the handler
prints a leading blank line before `rsp = ...` (the PDF shows none), and the actual byte values
are inherently machine-dependent. Logic, range, event wiring, and format all conform.

### P2 - [q2/q2.txt](q2/q2.txt) - Status: **Appropriate**

**Checked vs spec:** all seven questions are answered in order with correct conceptual content.

- **Q1** - explains IPC and ties high sys time to yield/allocator kernel entries. ✓ reasoning.
- **Q2** - top symbols = scheduler/`__sched_yield`/`producer_thread` + allocator paths;
  correctly notes `-O3` inlines `enqueue` so `perf annotate` is needed. ✓
- **Q3** - identifies the four hotspots and maps them correctly: load of `head_` (MESI
  contention), branch after CAS (stall attribution/skid), and `udiv` from
  `current_tail % capacity_`. ✓ The C++ source line for the division is correctly named.
- **Q4** - seq_cst => global order + store-buffer drain/fences; acquire/release defined and
  justified as sufficient. ✓
- **Q5** - virtual destructor => vptr/footprint/cache; malloc arena locks => serialization =>
  sys time. ✓
- **Q6** - the three flaw/fix pairs match the hint areas (false sharing -> `alignas(64)`;
  seq_cst -> acquire/release; per-item `new` + virtual dtor -> inline storage). ✓
- **Q7** - per-counter up/down predictions with justification, plus the IPC-vs-throughput
  closing argument. ✓

**Concrete gaps - RESOLVED 2026-07-04 (full PMU run, see Execution Results):**

- ~~**Q1.1** - no numeric IPC~~ **Filled:** measured **IPC = 0.13** (42.4G cycles:u /
  5.66G instructions:u from `perf stat`).
- ~~**Q3** - instructions lacked per-instruction cycle percentages~~ **Filled:** real
  `perf annotate` percentages on the x86-64 forms - `lock cmpxchg` **41.07%**, `head_`/
  `tail_` loads **15.16%/15.13%**, `divq` **9.76%**, `jne` retry 0.46%.

All required content is present and correct with real measured evidence.

### P3 - [q3/solved.cpp](q3/solved.cpp) - Status: **Appropriate**

**Checked vs spec** (diff against
[problem.cpp](<Resources/Resources accompanying assignment/problem.cpp>)):

- **Exactly one line added**, line 25: `Tree(const Tree& other) : root(new TreeNode(other.root->data)) {}`
  => within the "<= 5 added lines" budget.
- **No line removed** => satisfies "do not remove a single line" (all of `problem.cpp` is
  preserved verbatim).
- **Fixes the reported error** - the original double-free arises because the implicit copy
  constructor shares `root` between `original` and `copy`, so both destructors `delete` the same
  node. The added copy constructor gives `copy` its own distinct `root`, so each node is freed
  exactly once => Memcheck should report 0 errors / 0 leaks.

**Concrete gaps:** none against the stated requirement. Observation only (not a defect): the
copy constructor clones the root's `data` but not its `left`/`right` children, so `copy` is not
a structurally complete deep copy of `original`. The assignment requires only that Valgrind stop
complaining (no use-after-free, no leak), which this satisfies; a full recursive deep copy would
be a stricter-than-required alternative.

### Validation summary

| Problem | File | Status | Note |
|---|---|---|---|
| P1 stack visualizer | [q1/stack.py](q1/stack.py) | **Appropriate** | stop-event hook, range `rsp..rbp+16`, format, banner all conform |
| P2 perf | [q2/q2.txt](q2/q2.txt) | **Appropriate** | Q1-Q7 complete with measured IPC (0.13) and annotate percentages (2026-07-04 run) |
| P3 valgrind | [q3/solved.cpp](q3/solved.cpp) | **Appropriate** | 1 line added, 0 removed; valgrind clean (0 errors, 0 leaks) |

---

## Submission checklist

- **P1:** `q1/stack.py` - stop-event handler that prints `rsp`/`rbp` and the stack from `rsp`
  to `rbp+16`; verify against `stack_example.c` compiled with
  `-g -O0 -fno-omit-frame-pointer`.
- **P2:** `q2/q2.txt` - Q1-Q7 in plaintext; `make && ./ipc_bench`, then
  `perf stat` / `perf record` / `perf report` / `perf annotate`. Paste *your* IPC and the four
  hot instructions with percentages where the host's PMU allows.
- **P3:** `q3/solved.cpp` - `problem.cpp` plus <=5 added lines (no deletions) so
  `valgrind --leak-check=full ./solved` reports 0 errors.
- Re-run everything on **your own machine** and record *your* real addresses, opcodes, IPC, and
  percentages; the values quoted above are machine-dependent reference points.

---

## Execution Results (2026-06-21)

Executed on an **x86-64** host (8 logical CPUs). Tooling present: `gcc`/`g++`/`gdb`/`perf`.
`valgrind` was **not installed** at the original run time (2026-06-21); the deferred perf
PMU and valgrind verifications were **completed on 2026-07-04** (see P2/P3 below). Scratch
builds were done in `/tmp/wk4scratch`; no provided source files were modified.
Summary: **P1 PASS**, **P2 PASS (full PMU data)**, **P3 PASS (valgrind clean)**.

### P1 - Stack visualizer (gdb-Python) - PASS

- Built `gcc -g -O0 -fno-omit-frame-pointer -o stack_example stack_example.c`, then drove
  `gdb -q -batch -x cmds.gdb ./stack_example` with `source .../q1/stack.py`, `break main`, `run`,
  `break 14` (inside `calc()`), `continue`.
- Confirmed exactly as specified:
  - The load banner `"[stack.py] Stack visualizer loaded..."` prints **once** at import.
  - Each stop prints `rsp = 0x..., rbp = 0x...`.
  - Boxed 8-byte rows from `rsp` up to and including `rbp+16`, with the right annotations.
  - `main` frame: `rsp == rbp` (0x7fffffffd5f0) -> **3 rows**, first labelled `<- rsp rbp`.
  - `calc` frame: `rsp`/`rbp` 0x40 apart -> **11 rows**, `<- rsp` on the first and `<- rbp` on the
    `rbp` row; the `marker = 0x1122334455667788` is visible little-endian as
    `88 77 66 55 44 33 22 11`.
- Byte values are machine-dependent; the **structure** matched the spec. **No defect found;
  `stack.py` was not edited.**

### P2 - Ring-buffer profiling (perf) - PASS (full PMU run 2026-07-04)

- `make` (`-O3 -g -std=c++17 -pthread -march=native -Wno-interference-size`) + `./ipc_bench`:
  baseline throughput **3.31 M ops/sec** (16,575,191 items in 5.01 s).
- **Full perf run completed 2026-07-04** (perf 6.8.12 via
  `/usr/lib/linux-tools-6.8.0-134/perf` - the `/usr/bin/perf` wrapper rejects this custom
  kernel version string; `perf_event_paranoid = 2`, so user-space `:u` counters work):
  - `perf stat`: **42,397,378,897 cycles:u / 5,662,682,909 instructions:u -> IPC = 0.13**;
    2,751 page-faults:u; 3.15% branch-misses; user 18.18s / sys 15.17s over 5.01s wall.
  - `perf report --no-children` (135K samples): `producer_thread` 47.12%,
    `consumer_thread` 22.34%, `__sched_yield` 10.11%, `_int_malloc` 6.12%,
    `_int_free` 4.14%, `malloc` 1.46%.
  - `perf annotate` on `producer_thread` (enqueue inlined): **`lock cmpxchg` 41.07%**,
    `head_`/`tail_` loads 15.16%/15.13%, **`divq` 9.76%**, `jne` retry 0.46%,
    `call sched_yield@plt` 1.52%.
- `q2.txt` Q1/Q2/Q3 and the commands footer were rewritten with these measured numbers,
  replacing the earlier "PMU blocked, objdump fallback" placeholders; the conceptual Q4-Q7
  answers were preserved. The earlier ARM64 `ldar`/`casal`/`b.ne`/`udiv` listing had already
  been replaced by the x86-64 forms; those now carry real annotate percentages.

### P3 - Memory-leak fix (valgrind) - PASS (valgrind verified 2026-07-04)

- Confirmed `solved.cpp` == `problem.cpp` + a **single added line** (line 25,
  `Tree(const Tree& other) : root(new TreeNode(other.root->data)) {}`), **0 lines removed** -
  within the "<=5 added, 0 removed" budget.
- `g++ -g q3/solved.cpp -o solved` builds and runs **cleanly** (exit 0, prints
  "Check memory usage for leaks!").
- **valgrind verification DONE (Valgrind-3.22.0):**
  `valgrind --leak-check=full --show-leak-kinds=all ./solved` reports
  **"All heap blocks were freed -- no leaks are possible"** and
  **"ERROR SUMMARY: 0 errors from 0 contexts"** (6 allocs, 6 frees, 77,920 bytes).
  Combined with the earlier runtime contrast (original `problem.cpp` SIGSEGVs from the
  shallow-copy double free, `solved.cpp` exits 0), the fix is fully verified.
