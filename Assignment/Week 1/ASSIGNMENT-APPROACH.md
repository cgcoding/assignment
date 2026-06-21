# Binary Creation - Step-by-Step Assignment Approach

> Companion to `BINARY-CREATION-NOTES.md` (the concept reference). This file is the
> command-level playbook for solving all three problems and cross-references the existing
> partial answers in [q1.txt](q1.txt), [q2/](q2), and [q3.txt](q3.txt).

**Total: 60 points** - Problem 1 (16) + Problem 2 (18) + Problem 3 (26).

> **Architecture note.** The assignment text shows x86-64 examples (`objdump -m
> i386:x86-64`, `incq (%r11)`). The existing `q1.txt` / `q3.txt` answers were produced on an
> **ARM64/aarch64** machine (`adds x5,x3,x4`, `bl ...@plt`, `0xfffff7...` addresses). All
> concrete addresses, opcodes, and instruction mnemonics are **machine-dependent** - your
> numbers will differ from the assignment's sample. Re-run every command on your own target
> and record *your* output. The method is identical across architectures.

---

## Problem 1 - JIT compilation with PyPy (16 pts)

### Program under test

```python
import time
import __pypy__

def two_loops_series(n):
    total1 = 0
    for i in range(n):           # Loop 2 - a hotspot
        total1 += i
    mid = total1 * 2
    offset = mid + 7
    temp = offset - total1
    total2 = 0
    for j in range(n):           # Loop 3 - a hotspot
        total2 += j * temp
    return total1, total2, temp

if __name__ == "__main__":
    for _ in range(5):           # Loop 1 - NOT a hotspot
        result = two_loops_series(300)
    end = time.time()
    print(f"Result: {result}")
```

Save as `q1.py`. You need PyPy installed: `pypy3 --version`. (On Debian/Ubuntu:
`sudo apt install pypy3`.) CPython will work for the `dis` part of Q1 but **not** for the
JIT parts (Q2-Q4) - those require `pypy3`.

### Q1 - Bytecode for `total1 += i` (2 pts)

```python
import dis
def add(a, b):
    return a + b
dis.dis(add)
```

Then disassemble the real program/function to find the four bytecodes that implement
`total1 += i`. Expected shape (matches [q1.txt](q1.txt)):

```
LOAD_FAST   1 (total1)
LOAD_FAST   2 (i)
INPLACE_ADD            # may appear as BINARY_OP/BINARY_ADD depending on Python version
STORE_FAST  1 (total1)
```

Observe how the interpreter uses the operand **stack**: push `total1`, push `i`, add, store
back into `total1`.

### Q2 - At which iteration do Loops 2 and 3 become hot? (2 pts)

Instrument the code with per-loop counters and register a compile hook:

```python
import pypyjit

loop2_counter = 0
loop3_counter = 0

def on_compile(info):
    # fires whenever PyPy JIT-compiles a loop
    print("JIT compiled loop: type=", info.type, "no=", getattr(info, "loop_no", "unknown"))
    print("loop2_counter =", loop2_counter, "loop3_counter =", loop3_counter)

pypyjit.set_compile_hook(on_compile, False)
```

Increment `loop2_counter` inside Loop 2 and `loop3_counter` inside Loop 3 (use `global`),
run with `pypy3 q1.py`, and read the counter values printed at each compile event. The
callback receives a `pypyjit.JitLoopInfo` object.

Per [q1.txt](q1.txt), the observed answer was **Loop 2 = 81** and **Loop 3 = 81** (the
second loop is detected one full call later, after Loop 2 has run its 300 iterations):

```
JIT compiled loop: ...
loop2_counter = 81 loop3_counter = 0
JIT compiled loop: ...
loop2_counter = 300 loop3_counter = 81
```

> The threshold is the point at which the trace becomes "hot"; the exact number depends on
> PyPy's threshold and is what you must report from *your* run.

### Q3 - Optimized interpreter trace for `total1 += i` (2 + 2 pts)

```bash
PYPYLOG=jit-log-opt:my_trace.log pypy3 q1.py
```

1. In `my_trace.log`, **locate Loop 2**: find the loop whose `debug_merge_point` names
   `two_loops_series` and whose first `FOR_ITER` matches the bytecode offset of Loop 2.
2. Inside it, search for the `debug_merge_point(...)` entries for the `total1 += i`
   bytecodes (`LOAD_FAST`/`INPLACE_ADD`/`STORE_FAST`).
3. Around those markers, identify the optimized trace ops. The integer add shows up as an
   **overflow-checked add** with a guard, e.g. (from [q1.txt](q1.txt)):

```
debug_merge_point(0, 0, 'two_loops_series;.../q1.py:14-19~#28 INPLACE_ADD')
+616: setfield_gc(ConstPtr(ptr59), i58, descr=<... IntMutableCell.inst_intvalue 8>)
+620: i60 = int_add_ovf(i47, i52)
guard_no_overflow(descr=<...>) [ ... i47, i52, ... ]
```

4. **How `i` and `total1` carry to the next iteration:** the updated `total1` and the
   incremented `i` are live values passed on the **loop backedge**; they become the input
   state of the next iteration through the trace's final `jump(...)`. State that explicitly
   (max 2 lines, as the question asks).

### Q4 - Disassembled machine code for `total1 += i` (2 + 2 + 2 + 2 pts)

```bash
PYPYLOG=jit-backend:dump.asm pypy3 q1.py
```

1. In `dump.asm`, search for the string **`Loop 2`**. Beneath it are the start addresses of
   the sections; the region of interest is `[resops, failures)` ("resops" = residual
   operations - what survives after the JIT removed Python overhead).
2. Find the `CODE_DUMP` blob starting at the `gc_table` address; extract the bytes for the
   range `[resops, failures)` into `file.bin`. **Be byte-exact** - one byte off produces
   garbage.
3. Convert hex to raw bytes and disassemble:

```bash
xxd -r -p file.bin file_binary.bin
objdump -D -b binary -m i386:x86-64 --adjust-vma=<resops> file_binary.bin
```

(Use `--adjust-vma=<resops>` so addresses line up with the trace; the assignment's x86-64
sample begins `incq (%r11)` / `mov 0x128(%rbp),%rcx`. On ARM64 use
`-m aarch64` instead of `-m i386:x86-64`.)

4. In the resulting assembly, identify the four instruction groups. ARM64 sample from
   [q1.txt](q1.txt) (yours will differ):

| Item | Sample instruction |
|---|---|
| end-of-loop test | `cmp x4, x6` (followed by a conditional branch) |
| code for `total1 += i` | `adds x5, x3, x4` |
| overflow check | `adds` sets flags; a following `b.vs`/`brk` traps overflow |
| backedge jump | `b 0x150 <...>` (unconditional branch back to loop top) |

On x86-64 the equivalents are typically: a `cmp` + `jge/jl` for the loop test, an `add`
(or `incq` for the counter) for the body, a `jo`/`seto` overflow check, and a `jmp` backedge.

---

## Problem 2 - make and CMake (18 pts)

Working directory: [q2/](q2). Source files already present:

```
q2/
|-- helloworld.cpp
|-- myengine/{myengine.cpp, myengine.hpp}
|-- mygame/mygame.cpp
|-- usespthread.cpp
```

> Note: `mygame.cpp` does `#include <myengine.hpp>` (angle brackets), so the compiler must
> be told where the header is via `-I` (or it must be installed under a system include dir).

### Tasks 1-6 - `rawmake` (run as `make -f rawmake <target>`)

A working `rawmake` already exists at [q2/rawmake](q2/rawmake). Verify each rule against the
task spec:

| Task | Target | Key requirement | Points |
|---|---|---|---|
| 1 | `helloworld` | plain compile of `helloworld.cpp` | 1 |
| 2 | `usespthread` | **`-pthread`** flag (pthread library) | 2 |
| 3 | `libMyEngineDynamic.so` | `-fPIC` object + `-shared` | 2 |
| 3 | `libMyEngineStatic.a` | `ar rcs` on the object | 2 |
| 4 | `mygamestatic` | link `mygame.cpp` against the **static** lib | 2 |
| 5 | `mygamedynamic` | link `mygame.cpp` against the **dynamic** lib | 2 |
| 6 | `clean` | `.PHONY`; remove `.o`/`.a`/`.so` + binaries | 1 |

Reference recipes (consistent with the current `rawmake`):

```makefile
CXX = g++
CXXFLAGS = -Wall -O2

helloworld: helloworld.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

usespthread: usespthread.cpp
	$(CXX) $(CXXFLAGS) -pthread -o $@ $<

myengine.o: myengine/myengine.cpp myengine/myengine.hpp
	$(CXX) $(CXXFLAGS) -fPIC -c -o $@ myengine/myengine.cpp

libMyEngineStatic.a: myengine.o
	ar rcs $@ $^

libMyEngineDynamic.so: myengine.o
	$(CXX) -shared -o $@ $^

mygamestatic: mygame/mygame.cpp libMyEngineStatic.a
	$(CXX) $(CXXFLAGS) -o $@ mygame/mygame.cpp -I myengine -L. -lMyEngineStatic

mygamedynamic: mygame/mygame.cpp libMyEngineDynamic.so
	$(CXX) $(CXXFLAGS) -o $@ mygame/mygame.cpp -I myengine -L. -lMyEngineDynamic

.PHONY: clean
clean:
	rm -f helloworld usespthread mygamestatic mygamedynamic *.o *.a *.so
```

Verify:

```bash
cd q2
make -f rawmake helloworld   && ./helloworld
make -f rawmake usespthread  && ./usespthread
make -f rawmake libMyEngineStatic.a
make -f rawmake libMyEngineDynamic.so
make -f rawmake mygamestatic && ./mygamestatic
# dynamic binary needs to find the .so at runtime:
make -f rawmake mygamedynamic && LD_LIBRARY_PATH=. ./mygamedynamic
make -f rawmake clean
```

> Watch-outs: (a) `mygamedynamic` needs `LD_LIBRARY_PATH=.` (or an `-Wl,-rpath,.`) to run,
> since the `.so` is in the current dir. (b) The current `rawmake` omits `-I myengine` on
> the `mygame*` rules - add it if `myengine.hpp` isn't found.

### Task 7 - top-level `CMakeLists.txt` (build + install)

A working file exists at [q2/CMakeLists.txt](q2/CMakeLists.txt). It must produce
`helloworld`, `usespthread`, both libraries, and `mygamestatic`/`mygamedynamic`, and
**install** both libraries **and the header** `myengine.hpp` to `/usr/local/lib` and
`/usr/local/include` respectively.

```cmake
cmake_minimum_required(VERSION 3.10)
project(Week1Project CXX)
set(CMAKE_CXX_STANDARD 17)
add_compile_options(-Wall -O2)

add_executable(helloworld helloworld.cpp)

add_executable(usespthread usespthread.cpp)
target_link_libraries(usespthread pthread)

add_library(MyEngineStatic STATIC myengine/myengine.cpp)
target_include_directories(MyEngineStatic PUBLIC myengine)

add_library(MyEngineDynamic SHARED myengine/myengine.cpp)
target_include_directories(MyEngineDynamic PUBLIC myengine)

add_executable(mygamestatic mygame/mygame.cpp)
target_link_libraries(mygamestatic MyEngineStatic)

add_executable(mygamedynamic mygame/mygame.cpp)
target_link_libraries(mygamedynamic MyEngineDynamic)

install(TARGETS MyEngineStatic MyEngineDynamic
        ARCHIVE DESTINATION lib      # libMyEngineStatic.a  -> /usr/local/lib
        LIBRARY DESTINATION lib)     # libMyEngineDynamic.so -> /usr/local/lib
install(FILES myengine/myengine.hpp DESTINATION include)  # -> /usr/local/include
```

> **Gap to fix in the current file:** the existing `q2/CMakeLists.txt` installs the *target
> binaries* to `bin` but does **not** install `myengine.hpp`. Task 7.4 explicitly requires
> the **header** to land in `/usr/local/include`, so add the
> `install(FILES myengine/myengine.hpp DESTINATION include)` line above. The default install
> prefix is `/usr/local`, so `DESTINATION lib`/`include` resolve to `/usr/local/lib` and
> `/usr/local/include`.

Build/verify:

```bash
cd q2
mkdir build && cd build
cmake ..
make            # -> helloworld, usespthread, libMyEngineStatic.a, libMyEngineDynamic.so, ...
sudo make install  # installs both libs + header into /usr/local/{lib,include}
make clean      # CMake-generated Makefile already has a PHONY clean
```

### Task 8 - `mygame/CMakeLists.txt` (use the installed libraries)

A file exists at [q2/mygame/CMakeLists.txt](q2/mygame/CMakeLists.txt). It compiles
`mygame.cpp` against the **installed** libraries (from Task 7) to produce `mygamestatic`
and `mygamedynamic`:

```cmake
cmake_minimum_required(VERSION 3.22)
project(MyGame CXX)
set(CMAKE_CXX_STANDARD 17)

include_directories(/usr/local/include)   # find installed myengine.hpp
link_directories(/usr/local/lib)          # find installed libs

add_executable(mygamestatic mygame.cpp)
target_link_libraries(mygamestatic MyEngineStatic)

add_executable(mygamedynamic mygame.cpp)
target_link_libraries(mygamedynamic MyEngineDynamic)
```

> Because these libs are installed (not defined as targets in this file), link by file/name.
> If `target_link_libraries(... MyEngineStatic)` cannot resolve, use explicit paths
> `target_link_libraries(mygamestatic /usr/local/lib/libMyEngineStatic.a)` and
> `target_link_libraries(mygamedynamic /usr/local/lib/libMyEngineDynamic.so)`.

Build/verify (from `q2/mygame`):

```bash
mkdir build && cd build
cmake ..
make            # -> mygamestatic, mygamedynamic
```

---

## Problem 3 - Linking: tracing `printf` through PLT/GOT (26 pts)

Program:

```c
#include <stdio.h>
int main() {
    printf("Hi\n");
    return 0;
}
```

Save as `hello.c`.

### Step 1 - Compile, and know why each switch matters

```bash
gcc -g -no-pie -fno-builtin-printf -o hello hello.c
```

- `-g` - debug info, so `gdb` can break and show symbols.
- `-no-pie` - non-position-independent executable -> **fixed load addresses**, so the
  `objdump` addresses match what `gdb` shows at runtime (makes the excavation tractable).
- `-fno-builtin-printf` - stops gcc from optimizing `printf("Hi\n")` into `puts`/inlining,
  forcing a genuine `call printf@plt` so there is a PLT/GOT chain to trace.

### Step 2-5 - Static excavation (objdump)

```bash
objdump -d hello                 # find call PLT[printf], PLT[printf], PLT[0]
objdump -s -j .got.plt hello     # dump GOT contents (GOT[printf], GOT[1], GOT[2])
```

What to read off:

- **Step 2 - `PLT[printf]`**: in `objdump -d`, find `call ...<printf@plt>`; the target is
  `PLT[printf]`.
- **Step 3 - `GOT[printf]` and `*GOT[printf]`**: the first instruction of `PLT[printf]` is
  `jmp *GOT[printf]` - that operand address is `GOT[printf]`; its stored contents
  (`objdump -s -j .got.plt`) is `*GOT[printf]` (initially points back into the PLT).
- **Step 4 - `$index` and `PLT[0]`**: after the jump, `PLT[printf]` does `push $index` then
  `jmp PLT[0]`. Read `$index` and the `PLT[0]` address.
- **Step 5 - `GOT[1]`, `*GOT[1]`, `GOT[2]`, `*GOT[2]`**: `PLT[0]` does `push *GOT[1]`
  (link map) and `jmp *GOT[2]` (resolver). Read those GOT entries and their contents.

### Step 6 - Runtime excavation (gdb)

```bash
gdb ./hello
(gdb) break main
(gdb) run
(gdb) x/gx <GOT[1]>          # *GOT[1] before the call
(gdb) x/gx <GOT[2]>          # *GOT[2] before the call
(gdb) x/gx <GOT[printf]>     # *GOT[printf] BEFORE - still points into the PLT
# step over the printf call (use ni/si to reach and pass the call)
(gdb) ni
(gdb) x/gx <GOT[printf]>     # *GOT[printf] AFTER - now the resolved libc address
```

Useful gdb commands: `break`, `run`, `continue`, `x` (examine), `si` (step into),
`ni` (step over). The key observation: `*GOT[printf]` **changes** from a PLT address to the
real `printf` address in `libc.so` once lazy binding resolves it.

### The table to fill (13 x 2 = 26 pts)

Blue rows (1-9) come from `objdump`; red rows (10-13) come from `gdb`. Sample values from
[q3.txt](q3.txt) (ARM64 - **yours will differ**):

| # | Step | Context | Value required | Sample value |
|---|---|---|---|---|
| 1 | 2 | `call PLT[printf]` | `PLT[printf]` | `0x401040` |
| 2 | 3 | `jump *GOT[printf]` | `GOT[printf]` | `0x420018` |
| 3 | 3 | `jump *GOT[printf]` | `*GOT[printf]` | `0x400510` (into PLT) |
| 4 | 4 | `push $index` | `$index` | `0` |
| 5 | 4 | `jmp PLT[0]` | `PLT[0]` | `0x400510` |
| 6 | 5 | `push *GOT[1]` | `GOT[1]` | `0x420000` |
| 7 | 5 | `push *GOT[1]` | `*GOT[1]` | `0xfffff7df2fc0` (link map) |
| 8 | 5 | `jump *GOT[2]` | `GOT[2]` | `0x420008` |
| 9 | 5 | `jump *GOT[2]` | `*GOT[2]` | `0x400510` |
| 10 | 6 | just before call | `*GOT[1]` | `0xfffff7df2fc0` |
| 11 | 6 | just before call | `*GOT[2]` | `0x400510` |
| 12 | 6 | just before call | `*GOT[printf]` | `0x400510` (unresolved) |
| 13 | 6 | just after the call | `*GOT[printf]` | `0xfffff7e1f8a0` (resolved) |

The crucial before/after contrast is rows **12 vs 13**: `*GOT[printf]` flips from a
PLT-internal address to the resolved `printf` address in `libc.so` - that single change is
the entire point of lazy binding.

---

## Submission checklist

- **Problem 1 (16):** Q1 bytecode (2); Q2 hotspot iterations w/ evidence (2); Q3 optimized
  trace (2) + carry-forward explanation (2); Q4 four instruction groups - end-of-loop test
  (2), `total1 += i` (2), overflow check (2), backedge jump (2). -> fill [q1.txt](q1.txt).
- **Problem 2 (18):** `rawmake` tasks 1-6 (1+2+2+2+2+2+1); CMake task 7 incl. header install
  (1+2+2+2+2); `mygame/CMakeLists.txt` task 8 (2+2). -> files under [q2/](q2).
- **Problem 3 (26):** compile with the three switches; fill all 13 table rows (13x2) -
  objdump for rows 1-9, gdb for rows 10-13. -> fill [q3.txt](q3.txt).
- Re-run everything on **your own machine** and paste *your* real addresses/opcodes; the
  sample values above are reference only and are architecture-dependent.

---

## Solution Validation

> **Report-only.** The following is a static inspection of the existing solution artifacts
> against the assignment specification. No solution code was compiled, run, or modified.
> As noted above, all concrete addresses, opcodes, and instruction mnemonics are
> **machine-dependent** (the answers were produced on ARM64/aarch64), so byte-exact
> encodings are not graded here - only structural correctness and completeness against the
> spec. Re-run on your own target to confirm the concrete values.

| Problem | Artifact | Status |
|---|---|---|
| P1 - JIT compilation | [q1.txt](q1.txt) | **Incomplete** |
| P2 - make + CMake | [q2/](q2) | **Incomplete** |
| P3 - Linking | [q3.txt](q3.txt) | **Incomplete** |

### P1 - JIT compilation -> [q1.txt](q1.txt) (16 pts) - *Incomplete*

**Checked against spec:** the four numbered questions (bytecode of `total1 += i`; hotspot
iteration numbers for Loops 2/3; optimized interpreter trace + carry-forward; disassembled
machine code with the four instruction groups).

- **Q1 - Bytecode (2 pts): Appropriate.** [q1.txt](q1.txt) gives
  `LOAD_FAST total1 / LOAD_FAST i / INPLACE_ADD / STORE_FAST total1`, which matches the
  expected stack-based shape for `total1 += i`.
- **Q2 - Hotspot iterations (2 pts): Appropriate.** Reports **Loop 2 = 81, Loop 3 = 81**
  with supporting instrumented output (<= 4 lines), consistent with the playbook above.
- **Q3 - Optimized trace (2 + 2 pts): Incorrect/Incomplete.** The "trace sequence" pasted
  for `total1 += i` is the **bytecode** again
  (`LOAD_FAST / LOAD_FAST / BINARY_ADD / STORE_FAST`), **not** the optimized interpreter
  trace the question asks for. The actual optimized-trace ops appear only lower down in the
  *evidence* block (`setfield_gc(...)`, `int_add_ovf(i47, i52)`, `guard_no_overflow(...)`).
  **Gap:** promote those `int_add_ovf` / `guard_no_overflow` / `setfield_gc` lines into the
  trace-sequence answer; the bytecode listing is not an acceptable answer for the optimized
  trace. The carry-forward explanation (live `total1`/`i` on the backedge via `jump(...)`)
  is fine.
- **Q4 - Machine code groups (2+2+2+2 pts): Mostly appropriate, one weak mapping.**
  `total1 += i` -> `adds x5, x3, x4` and the backedge `b 0x150` are correct in shape; the
  overflow check (`adds` setting flags + a trap) is plausible. **Gap:** the *end-of-loop
  test* is given as `cmp x4, x6` followed by `brk #0` - `brk #0` is a trap/guard, not the
  loop's conditional branch. The end-of-loop test should pair the `cmp` with a **conditional
  branch** (e.g. `b.ge`/`b.lt`); identify and cite that branch.

### P2 - make + CMake -> [q2/](q2) (18 pts) - *Incomplete*

**Checked against spec:** `rawmake` tasks 1-6, top-level [q2/CMakeLists.txt](q2/CMakeLists.txt)
(tasks 1-4 + install of both libs **and** the header), and
[q2/mygame/CMakeLists.txt](q2/mygame/CMakeLists.txt) (task 8). Source files
([helloworld.cpp](q2/helloworld.cpp), [usespthread.cpp](q2/usespthread.cpp),
[myengine/](q2/myengine), [mygame/mygame.cpp](q2/mygame/mygame.cpp)) are present and match
the required directory structure.

- **`rawmake` tasks 1-6 (1+2+2+2+2+2+1): Appropriate.** [q2/rawmake](q2/rawmake) has:
  `helloworld` (plain compile); `usespthread` with **`-pthread`**; `myengine.o` built with
  **`-fPIC`**, then `libMyEngineStatic.a` via **`ar rcs`** and `libMyEngineDynamic.so` via
  **`-shared`** (library names match the spec); `mygamestatic`/`mygamedynamic` linking
  `mygame.cpp` against the static/dynamic libs with `-L. -l...`; and a `.PHONY: clean` that
  removes `*.o *.a *.so` and the binaries. The header is found because
  [mygame.cpp](q2/mygame/mygame.cpp) uses a relative `#include "../myengine/myengine.hpp"`,
  so the `-I.` is harmless/redundant rather than wrong. (Runtime note: `mygamedynamic` needs
  `LD_LIBRARY_PATH=.` to run - a runtime detail, not a Makefile defect.)
- **Task 7 top-level [q2/CMakeLists.txt](q2/CMakeLists.txt) (1+2+2+2+2): Incomplete - one
  concrete gap.** It correctly builds `helloworld`, `usespthread` (+`pthread`), both
  libraries (target names yield `libMyEngineStatic.a` / `libMyEngineDynamic.so`), and the
  two `mygame*` binaries, and installs the libraries (`ARCHIVE`/`LIBRARY DESTINATION lib`).
  **Gap:** task 7.4 explicitly requires installing the **header** `myengine.hpp` to
  `/usr/local/include`, but there is **no `install(FILES myengine/myengine.hpp DESTINATION
  include)`** rule - only the libs (and target binaries) are installed. Add that line (see
  the Task 7 playbook above). Worth ~2 pts.
- **Task 8 [q2/mygame/CMakeLists.txt](q2/mygame/CMakeLists.txt) (2+2): Appropriate (with a
  dependency caveat).** It sets `include_directories(/usr/local/include)` +
  `link_directories(/usr/local/lib)` and links `mygamestatic`/`mygamedynamic` against
  `MyEngineStatic`/`MyEngineDynamic`. Since those are not targets in this standalone build,
  CMake passes them as `-lMyEngineStatic` / `-lMyEngineDynamic`, which resolve against the
  **installed** `.a`/`.so` in `/usr/local/lib` - so this only works **after** task 7's
  `sudo make install` has run. (If link resolution fails on a given toolchain, fall back to
  explicit paths as noted in the Task 8 playbook.)

### P3 - Linking -> [q3.txt](q3.txt) (26 pts) - *Incomplete*

**Checked against spec:** the 13-row PLT/GOT excavation table (rows 1-9 from `objdump`,
rows 10-13 from `gdb`), and the key before/after change of `*GOT[printf]`.

- **Completeness: all 13 rows are filled**, each with a supporting `objdump`/`gdb` snippet,
  and the crucial **lazy-binding contrast is correct**: `*GOT[printf]` flips from
  `0x400510` (into the PLT, unresolved - rows 3/12) to `0xfffff7e1f8a0` (resolved libc
  address - row 13). Rows 5-11 (`PLT[0]=0x400510`, `GOT[1]/GOT[2]` and their contents,
  `*GOT[1]` link-map, `*GOT[2]`) are internally consistent between the `objdump` and `gdb`
  sections.
- **Concrete gap - Row 1 (`PLT[printf]`) is internally inconsistent.** The value cell reads
  **`401040`**, but its own evidence line is `4006bc: ... bl 400560 <printf@plt>`, i.e. the
  call target (and therefore `PLT[printf]`) is **`0x400560`**, which also fits the address
  neighbourhood (`.plt` at `0x400510`). `0x401040` does not belong to this binary's address
  range and looks carried over from the x86-64 reference value. **Fix:** set
  `PLT[printf] = 0x400560` to match the `bl` evidence. Worth 2 pts.
- **Verify on your own machine.** Because this is a machine-dependent excavation, re-run
  `objdump -d` / `objdump -s -j .got.plt` and `gdb` on *your* build and reconcile every
  cell with its evidence (the Row 1 mismatch shows why each value must be read off the
  excavation, not transcribed).
