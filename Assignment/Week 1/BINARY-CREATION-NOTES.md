# Binary Creation - Comprehensive Study Notes

> Distilled from the 55-slide *Week 1: Binary Creation* deck, organized around what the
> assignment actually tests. Use this as the concept reference; use
> `ASSIGNMENT-APPROACH.md` for the step-by-step solving guide.

A program does not become an executable in one step. It is *gradually transformed* from
human-readable source into a runnable binary, passing through several intermediate
representations. This document follows that journey:

1. **Translation** - the compilation / interpretation pipeline.
2. **Build management** - `make` and `cmake` orchestrate the translation for real projects.
3. **Linking** - resolving external references, statically (build time) and dynamically
   (load time / first use).

---

## 0. How the deck maps to the assignment

| Deck topic | Slides | Assignment problem it supports |
|---|---|---|
| Compilation pipeline (gcc stages) | 1-6 | P1 (compilation model background) |
| Interpretation pipeline (Python bytecode/VM) | 4 | P1 (interpretation model + JIT) |
| `make` (Makefile v1-v4, variables, pattern rules) | 7-16 | P2 (`rawmake`, tasks 1-6) |
| Shared libraries (manual build, `-fPIC`, `-shared`) | 21-23 | P2 (static/dynamic libs) |
| CMake (commands, hierarchy, install) | 17-28 | P2 (`CMakeLists.txt`, tasks 7-8) |
| Linking overview, static linking, ELF, `nm` | 29-39 | P3 background |
| Relocation (PC-relative, records, rel32 rule) | 40-44 | P3 (linking internals) |
| Dynamic linking, PLT/GOT, lazy binding | 45-53 | P3 (the `printf` excavation) |
| Tooling (`readelf`/`objdump`/`nm`/`gdb`) | 33, 55 | P1, P3 |

The three problems line up almost exactly with the three halves of the deck:
**P1 = pipelines/JIT**, **P2 = build tools**, **P3 = linking**.

---

## 1. Compilation vs Interpretation pipelines

### 1.1 The compilation pipeline (C++ / gcc, x86-64)

Source flows through a fixed sequence of stages, each answering one question:

```
hello.cpp -> Syntax Analysis  (is the program well-formed?)
          -> Semantic Analysis (does it have type errors?)
          -> Code Optimization (can it be made more efficient?)
          -> Code Generation   (emit x86-64 assembly)   -> hello.s
          -> Assemble          (assembly -> machine code) -> hello.o
          -> Link              (object files + libraries) -> hello
                                                             (runs on the processor)
```

Key idea: the pipeline is *a progression from description to realization*. Each stage
narrows the gap between "what the human wrote" and "what the processor runs".

### 1.2 Breaking gcc into stages with switches

You can run each stage independently:

```bash
g++ -E hello.cpp -o hello.ii   # Preprocess only       (.ii)
g++ -S hello.ii  -o hello.s    # Compile to assembly    (.s)
g++ -c hello.s   -o hello.o    # Assemble to object     (.o)
g++    hello.o   -o hello       # Link to executable
```

Single-shot with all intermediates kept:

```bash
g++ -save-temps -v hello.cpp -o hello
# Keeps hello.ii, hello.s, hello.o
# -v shows the detailed internal steps (calls to cc1plus, as, ld)
```

### 1.3 What `g++` really invokes under the hood

`g++` is a *driver*; it orchestrates specialized tools:

- **Preprocess + compile**: `cc1plus` turns `.cpp`/`.ii` into `.s`.
- **Assemble**: `as` turns `.s` into `.o`.
- **Link**: `collect2` (the frontend to `ld`) links object files with startup code and
  libraries.

To inspect optimizer output:

- `-fdump-tree-all`, `-fdump-tree-original`, etc. dump the GIMPLE IRs after various passes.
- `-fopt-info` prints optimization summaries.

### 1.4 The interpretation pipeline (Python)

```
hello.py -> Syntax Analysis    (well-formed?)
         -> Bytecode Generator (code for a Virtual Machine) -> hello.pyc
         -> Bytecode Optimizer (optimize the bytecode)
         -> VM Simulator       (interpret the bytecode)      -> results
```

Notable contrast with compilation: **type errors are detected during bytecode
interpretation**, and **linking to libraries also happens at interpretation time** - not
ahead of time.

### 1.5 Bridge to Problem 1: JIT compilation

JIT (Just-In-Time) compilation is a *third* model that fuses the two above, and it is the
subject of assignment Problem 1 (specifically PyPy's JIT for Python):

- Start with the **interpretation** model (flexible, good for dynamically typed code).
- The runtime tracks **frequently executed paths**, especially loops.
- When a path becomes **"hot"** (crosses an iteration threshold), the JIT **traces** the
  low-level operations produced while executing the bytecodes in that path. A trace is a
  **linear sequence of instructions with guards**.
- The trace is **optimized** to strip interpreter overhead. Type assumptions are captured
  as **guards** so the specialized machine code stays valid.
- The optimized trace is turned into **machine code** for the current processor and stored
  in executable memory inside the running process.
- Later visits **jump straight to the compiled code**; guards validate the assumptions.
- If a **guard fails**, control leaves the compiled code and PyPy rebuilds the
  interpreter-visible state, resuming at the right bytecode.

Illustrative simplification for `a + b`:

```
# raw bytecode                 # optimized trace
LOAD_FAST 0   (push a)         load 0
LOAD_FAST 1   (push b)         guard: value is integer
BINARY_ADD                     load 1
                               guard: value is integer
                               integer_add
```

The assignment asks you to recover the *real* bytecode, the *real* optimized trace, and
the *real* disassembled machine code - not these simplified versions.

---

## 2. Build tools: `make`

### 2.1 Why build tools at all?

Building an executable from interdependent sources, headers, configs, and libraries gets
complex:

- Multiple source files with complex dependencies.
- Different compilers and options.
- Linkage to external libraries.
- Multiple build configurations (debug, release, test).
- Environment variables and paths.

And an efficiency concern: full recompilation for a tiny change is wasteful; **incremental
builds** need careful dependency tracking. `make` solves both.

### 2.2 The running example

```c
// main.c
#include <stdio.h>
#include <mathutils.h>
int main() {
    int x;
    printf("Enter a number: ");
    scanf("%d", &x);
    int result = square(x);
    printf("The square of %d is %d\n", x, result);
    return 0;
}
```

```c
// mathutils.c
#include <mathutils.h>
int square(int n) { return n * n; }
```

```c
// mathutils.h
#ifndef MATHUTILS_H
#define MATHUTILS_H
int square(int n);
#endif
```

Manual build: `gcc -o main main.c mathutils.c -I.` - fine until you have 100 files and
change only two.

### 2.3 Makefile evolution (v1 -> v4)

**v1 - one rule:**

```makefile
main: main.c mathutils.c
	gcc -o main main.c mathutils.c -I.
```

- `main` (the *target*) depends on `main.c` and `mathutils.c`; if either changes, rebuild.
- The recipe line **must start with a TAB**, not spaces.

**v2 - variables + implicit rule:**

```makefile
CC = gcc
CPPFLAGS = -I.

main: main.o mathutils.o
	$(CC) -o main main.o mathutils.o
# %.o: %.c
#	$(CC) $(CPPFLAGS) $(CFLAGS) -c -o $@ $<
```

- Switching compilers is now a one-line change (`gcc` -> `clang`).
- `make` figures out `main.o` deps using the (commented) **implicit rule**.
- Caveat: the dependency on `mathutils.h` is **not** declared, so editing the header does
  **not** trigger a rebuild - a real bug.

**v3 - pattern rules + automatic variables:**

```makefile
CC = gcc
CPPFLAGS = -I.
DEPS = mathutils.h

main: main.o mathutils.o
	$(CC) -o $@ $^

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CPPFLAGS)
```

Automatic variables:

- `$@` = the target (left-hand side).
- `$<` = the first prerequisite.
- `$^` = the full list of prerequisites.

Now each `.o` correctly depends on its `.c` **and** on `mathutils.h`.

**v4 - organized directories + `patsubst` + clean:**

```makefile
CC=gcc
IDIR=include
CPPFLAGS=-I$(IDIR)
ODIR=obj
SDIR=src

_DEPS = mathutils.h
DEPS = $(patsubst %,$(IDIR)/%,$(_DEPS))
_OBJ = main.o mathutils.o
OBJ = $(patsubst %,$(ODIR)/%,$(_OBJ))

main: $(OBJ)
	$(CC) -o $@ $^ $(CPPFLAGS)

$(ODIR)/%.o: $(SDIR)/%.c $(DEPS)
	$(CC) -c -o $@ $< $(CPPFLAGS)

.PHONY: clean
clean:
	rm -f $(ODIR)/*.o
```

- `$(patsubst PATTERN,REPLACEMENT,TEXT)` rewrites whitespace-separated words; `%` matches
  any run of characters. Used here to prefix bare names with their directory.
- `.PHONY: clean` tells `make` that `clean` is **not a file** - it always runs.

### 2.4 Recommended project layout

- `include/` - all `.h` files.
- `src/` - all `.c` / `.cpp` sources.
- `lib/` - local libraries (`.a`, `.so`).
- `obj/` - intermediate object files.

Keeps the project clean, maintainable, and scalable.

---

## 3. Shared libraries and CMake

### 3.1 What is a shared library?

Compiled code ready for reuse. Example: `libm` (the C math library) has **two parts**:

- The **header** (`math.h` in `/usr/include`) - function prototypes, for type-checking at
  compile time.
- The **shared object** (`libm.so` in `/usr/lib/x86_64-linux-gnu`) - the actual code, used
  at link/run time.

### 3.2 Building a shared library manually

```bash
gcc -c -fpic -Iinclude mathutils.c        # position-independent object
gcc -shared -o libmathutils.so mathutils.o # link into a shared object
```

- `-fpic` / `-fPIC` generates **position-independent code** (PIC), required for dynamic
  linking (the library can be mapped at any address).
- Library files must be named `lib*.so`.

Using it:

```bash
export LD_LIBRARY_PATH=$(pwd):$LD_LIBRARY_PATH        # runtime: dynamic linker search path
gcc -L$(pwd) -o main main.c -lmathutils -Iinclude     # build time: static linker
# Alternative to LD_LIBRARY_PATH - bake the path into the binary:
# gcc -L$(pwd) -o main main.c -lmathutils -Iinclude -Wl,-rpath,$(pwd)
./main
```

- `-l<name>` links against `lib<name>.so`; `-L<dir>` adds a search dir for the **static
  linker** (build time).
- `LD_LIBRARY_PATH` tells the **dynamic linker** where to find the `.so` at **run time**.
- `-Wl,-rpath,<dir>` embeds the runtime search path into the executable.

A **static** library would instead be an archive `lib*.a`, built with `ar rcs`.

### 3.3 CMake basics

CMake is a **build-system generator**: it describes the build *platform-independently* in a
`CMakeLists.txt`, then generates the actual build files (Makefiles by default on Linux, but
also Xcode, Visual Studio, Eclipse, etc.). Syntax is simpler than raw Makefiles.

It auto-discovers compilers and libraries:

- Standard system libs (`m`, `pthread`): CMake just passes the right linker flag (`-lm`,
  `-lpthread`).
- Non-standard libs (OpenSSL, Boost): `find_package` locates headers and compiled libs and
  generates the `-I` / `-L` flags.

Simplest `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.22.1)
project(main_test)
include_directories(include)
file(GLOB SOURCES "src/*.c")
add_executable(main ${SOURCES})
```

Running `cmake .` detects the C/C++ compilers, verifies they work, detects ABI and
supported features (C++11/C99), then generates the build files.

### 3.4 CMake command reference

**Core (used constantly):**

- `cmake_minimum_required(VERSION x.y)` - minimum version + policies.
- `project(name [LANGUAGES])` - define project + enabled languages.
- `add_executable(target srcs)` - create an executable target.
- `add_library(target [STATIC|SHARED] srcs)` - create a library target.
- `target_link_libraries(target libs)` - link libraries into a target.
- `target_include_directories(target {PRIVATE|PUBLIC|INTERFACE} dirs)` - include paths with
  scope.
- `add_subdirectory(dir)` - build subprojects / hierarchical layouts.

**Common in real projects:**

- `target_compile_options(target opts)` - flags like `-Wall -Wextra -O2`.
- `target_compile_definitions(target defs)` - `-D` macros.
- `find_package(Pkg ...)` - locate external libraries.
- `option(NAME "help" ON|OFF)` - build-time switches.
- `install(TARGETS ...)` - installation rules.

**Use with care:**

- `file(GLOB var "pattern")` - convenient, but may require re-running CMake when files are
  added/removed.

### 3.5 Hierarchy of CMakeLists + building a library

Layout with a sub-build for the library:

```
.
|-- build/                 # out-of-source build dir
|-- CMakeLists.txt         # builds the executable
|-- include/mathutils.h    # library header
|-- shared/
|   |-- mathutils.c        # library source
|   |-- CMakeLists.txt     # builds the shared lib
|-- src/main.c
```

Top-level `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.22.1)
project(makeexecutable)
set(CMAKE_BUILD_TYPE Release)
add_subdirectory(shared)
file(GLOB SOURCES "src/*.c")
add_executable(main ${SOURCES})
target_link_libraries(main mathutils)
```

`shared/CMakeLists.txt`:

```cmake
add_library(mathutils SHARED mathutils.c)
target_include_directories(mathutils PUBLIC ${CMAKE_SOURCE_DIR}/include)
```

Build flow (out-of-source keeps the tree clean):

```bash
cd build
cmake ..
make
```

---

## 4. Linking

### 4.1 What is linking?

Linking produces an executable by **combining object files and resolving all symbol
references** across them. Two flavors:

- **Static linking**: every external reference (from object files and libraries) is
  resolved at compile/link time; the executable is self-contained.
- **Dynamic linking**: references between user object files are resolved at link time, but
  references to **shared libraries** are resolved at **load time** or at **first use**
  (lazy binding).

There are **three actors**:

1. The **static linker** (`ld`) - resolves inter-module references and writes the ELF
   executable.
2. The **loader** - loads the executable and the dynamic linker.
3. The **dynamic linker** (`ld-linux.so`) - loads shared libraries and performs runtime
   relocations.

### 4.2 Static linking - essential steps

1. **Input collection** - read each object file's symbol table (what it defines / refs).
2. **Symbol resolution** - for every undefined symbol, pick a matching definition; error on
   missing or multiply-defined symbols.
3. **Combining layouts** - merge like sections across modules (`.text`, `.rodata`, `.data`,
   `.bss`); assign final addresses respecting alignment and R/W/X permissions.
4. **Relocation** - patch every code/data location that references a symbol.

### 4.3 The ELF file format

ELF (Executable and Linkable Format) is the fixed structure Linux uses for executables,
object files (`.o`), shared libraries (`.so`), and core dumps. Inspect with:

- `readelf` - headers, symbols, relocations, sections.
- `objdump` - disassemble code, inspect sections.
- `nm` - list symbols.
- `file` - identify the ELF type.

### 4.4 ELF and the user-space memory model

The ELF layout matches the in-memory layout, so the kernel can map sections directly into
segments with the right permissions:

```
High memory
   Stack (grows down)
   Heap  (grows up)
   Uninitialized globals (.bss)   rw-
   Initialized globals   (.data)  rw-
   Read-only data        (.rodata) r--
   Code segment          (.text)  r-x
Low memory
```

- `.bss` - uninitialized globals.
- `.data` - initialized globals.
- `.rodata` - strings and other constants.
- `.text` - program instructions.
- plus symbol tables, relocation entries, headers.

### 4.5 Tentative addresses in `.o` files, and module combining

In an object file, each section (`.text`, `.data`, `.bss`) is **relocatable** and starts at
`0x0`; every symbol gets a tentative address relative to its section start. Final absolute
addresses are assigned during linking.

```bash
$ nm Module1.o
                 U b        # undefined here
0000000000000000 B i        # i in .bss
0000000000000000 T main     # main in .text
                 U malloc    # undefined
                 U printf    # undefined
0000000000000000 D x        # x in .data
```

Symbol-type letters: `U` undefined, `T` text (defined code), `D` initialized data, `B` bss
(uninitialized), lowercase = local.

During linking, like sections from all modules are concatenated, so symbols get their final
addresses. Comparing `nm -n -S` before/after shows tentative `0x0...` addresses in the
`.o`s becoming real addresses (e.g. `main` at `0x401745`) in the final executable.

### 4.6 Relocation

**The problem:** in `.o` files, references to functions/variables are emitted with
**placeholder** displacements (zeros). When modules are combined and sections move,
relocation **patches every affected reference** to point at the symbol's final address.

**How references look (`objdump -dr Module1.o`):** (`-d` disassemble, `-r` show relocations)

```
1f: e8 00 00 00 00   call 24 <main+0x24>
    20: R_X86_64_PLT32 fn-0x4
24: 89 05 00 00 00 00 mov  %eax,0x0(%rip)
    26: R_X86_64_PC32  i-0x4
```

- `e8` is a **relative call**; the 4-byte displacement `00 00 00 00` is a placeholder the
  linker will patch with the address of `fn`.
- The `mov ...,0x0(%rip)` likewise has a placeholder to be patched to reach `i`.

**PC-relative addressing (`objdump -d main`):**

```
401764: e8 29 00 00 00   call 401792 <fn>
0000000000401792 <fn>:
```

- Opcode `e8` = near call; operand `29 00 00 00` (little-endian) = displacement `0x29`.
- PC after the call instruction = `0x401769`; target = `0x401769 + 0x29 = 0x401792` = `fn`.
- If caller and callee are in the **same section**, they move together, so **no relocation
  is needed**.

**The four relocation cases:**

| Case | Reference | Relocation needed? |
|---|---|---|
| 1 | Call to a function in the **same** module | No (PC-relative disp stays valid) |
| 2 | Call to a function in a **different** module | Yes |
| 3 | Reference to a variable in the **same** module | Yes (code/data in different sections) |
| 4 | Reference to a variable in **another** module | Yes |

**Relocation records (`readelf -r Module1.o`):**

```
RELOCATION RECORDS FOR [.text]:
OFFSET        TYPE            VALUE
000000000012  R_X86_64_PLT32  malloc-4
000000000020  R_X86_64_PLT32  fn-4
000000000026  R_X86_64_PC32   i-4
00000000002c  R_X86_64_PC32   b-4
000000000035  R_X86_64_PC32   .rodata-4
000000000042  R_X86_64_PLT32  printf-4
```

- `OFFSET` - where the displacement is written.
- `addend` - the constant addend (often `-4` for `call`/`jmp rel32`).
- `target` - final address of the referenced symbol / PLT entry.

**The x86-64 rel32 rule:**

```
OFFSET + 4 + displacement = target
=> displacement = target - (OFFSET + 4)
```

In `readelf` notation the `OFFSET` is implicit and you see `displacement = target - addend`.
Example for `malloc-4` at offset `0x12`: *"take the final address of `malloc`, subtract 4,
then subtract `0x12`."*

### 4.7 Dynamic linking

**Benefits:**

- **Smaller executables** - library code isn't embedded.
- **Reduced memory footprint** - one copy of a shared lib is mapped once and shared across
  processes.
- **Easier updates** - update the `.so` without recompiling its users.

**How the gcc linker is invoked:** `g++` calls `collect2` (frontend to `ld`) with, among
others: `-dynamic-linker /lib64/ld-linux-x86-64.so.2` (sets the dynamic linker), `-pie`,
`-z now -z relro`, the `-L` library paths, your `.o` files, and the libraries
`-lstdc++ -lm -lgcc_s -lgcc -lc`, plus the C runtime startup/teardown objects
(`crt*.o`).

**Two phases:**

1. **Build time (static linking):** inter-module dependencies between *your* objects are
   fully resolved; dependencies on shared libraries remain **unresolved**, but relocation
   records and PLT/GOT stubs are created. The linker also verifies the referenced symbols
   exist in the named shared libs.
2. **Runtime (dynamic linking):**
   - `execve` starts the ELF executable.
   - The kernel reads the ELF program headers and maps sections into the address space
     (**loading**).
   - If a `PT_INTERP` entry is present, the kernel maps the **dynamic linker** and hands it
     control. (`readelf -p .interp` shows the dynamic linker path.)
   - The dynamic linker maps the required shared libraries (usually between heap and stack),
     performs relocations, and prepares execution.
   - **Shared-library variables** are typically resolved at this startup phase;
     **shared-library functions** are resolved **lazily on first call** via PLT/GOT.

**Memory model with shared libraries:** shared libraries are mapped between heap and stack.
A shared library's `.text` may be shared across processes/modules, but the library has **no
separate stack or heap** - it grows on the common stack/heap.

### 4.8 The PLT/GOT mechanism and lazy binding

Two tables cooperate ("jugalbandi"):

- **PLT (Procedure Linkage Table)** - a table of small **code** fragments (in `.text`-like
  executable memory).
- **GOT (Global Offset Table)** - a table of **data** (addresses), in the data segment.

Structure for a `printf` call:

```
# in main
callq PLT[printf]

PLT[0]:
    pushq *GOT[1]      ; push address of the link map
    jmp   *GOT[2]      ; jump to the dynamic linker's resolver

PLT[printf]:
    jmpq  *GOT[printf]
next:
    pushq $index       ; relocation index for printf
    jmp   PLT[0]

GOT[printf] (initially): -> label `next:` in PLT[printf]
GOT[printf] (resolved):  -> address of printf in libc.so
GOT[1]: -> address of the link map
GOT[2]: -> address of the dynamic linker's resolver
```

> **Notation used in the assignment:** `PLT[printf]` = the *address* of the PLT entry;
> `GOT[printf]` = the *address* of the GOT entry; `*GOT[printf]` = the *contents* of the GOT
> entry. So `pushq *GOT[1]` means "push the contents of `GOT[1]`". (This is deliberately not
> the usual asm dereference convention.)

**Lazy binding, step by step (first call to `printf`):**

1. The call transfers control to `PLT[printf]`.
2. `PLT[printf]` jumps to the address stored in `GOT[printf]`. Initially that address points
   **back** into `PLT[printf]` (the `next:` instruction).
3. A relocation index `$index` is pushed; control transfers to `PLT[0]`.
4. `PLT[0]` pushes the **link-map** address (`*GOT[1]`).
5. Control jumps to the **resolver** (`*GOT[2]`).
6. Using the link map and `$index`, the resolver identifies the symbol (`printf`) and finds
   its address in `libc.so`.
7. `GOT[printf]` is **patched** with the resolved runtime address; control transfers there.
8. **Subsequent calls** jump directly to `printf` via `GOT[printf]` through `PLT[printf]` -
   the resolver is not involved again.

This entire chain - call -> PLT -> GOT -> PLT[0] -> resolver -> GOT patch -> printf - is
exactly what Problem 3 asks you to recover with `objdump` and `gdb`.

---

## 5. Tooling cheat-sheet

### 5.1 GCC / G++ switches

| Switch | Meaning |
|---|---|
| `-E` | Preprocess only (-> `.ii`) |
| `-S` | Compile to assembly (-> `.s`) |
| `-c` | Assemble to object (-> `.o`) |
| `-save-temps -v` | Keep all intermediates; show internal tool calls |
| `-I<dir>` | Add header search dir |
| `-L<dir>` | Add library search dir (static linker) |
| `-l<name>` | Link `lib<name>.so`/`.a` |
| `-fPIC` / `-fpic` | Position-independent code (for shared libs) |
| `-shared` | Produce a shared object (`.so`) |
| `-pthread` | Compile/link with POSIX threads |
| `-Wl,-rpath,<dir>` | Embed runtime library search path |
| `-g` | Emit debug info (for `gdb`) |
| `-no-pie` | Non-position-independent executable (fixed addresses) |
| `-fno-builtin-printf` | Don't inline/replace `printf` - force a real PLT call |
| `-fdump-tree-*`, `-fopt-info` | Dump optimizer IRs / summaries |

### 5.2 Binary inspection tools

| Tool | Use |
|---|---|
| `nm [-n] [-S] file` | List symbols (`-n` sort by address, `-S` show sizes) |
| `objdump -d` | Disassemble `.text` |
| `objdump -dr` | Disassemble + show relocation entries |
| `objdump -s -j .got.plt` | Hex-dump a specific section (e.g. `.got.plt`) |
| `objdump -D -b binary -m i386:x86-64 --adjust-vma=<addr>` | Disassemble raw bytes at a base address |
| `readelf -r` | Relocation records |
| `readelf -p .interp` | Show the dynamic linker path |
| `file` | Identify ELF type |
| `ar rcs lib*.a *.o` | Build a static archive |
| `xxd -r -p` | Convert a hex dump back into raw bytes |

### 5.3 Debugger / runtime

- `gdb`, with `break`, `run`, `continue`, `x` (examine memory), `si` (step instruction),
  `ni` (next instruction) - used in Problem 3 to read GOT contents before/after the call.

### 5.4 Python / PyPy (Problem 1)

| Tool / env var | Use |
|---|---|
| `import dis; dis.dis(fn)` | Show the bytecode of a function |
| `import pypyjit` | `pypyjit.set_compile_hook(cb, False)` fires `cb(JitLoopInfo)` on each JIT compile |
| `PYPYLOG=jit-log-opt:<file>` | Dump the **optimized interpreter trace** |
| `PYPYLOG=jit-backend:dump.asm` | Dump the **backend machine code** (`CODE_DUMP` blobs) |
| `debug_merge_point(...)` | Trace markers tying trace ops back to bytecodes |

---

## 6. One-paragraph summary

Binary creation is the gradual transformation of a program from human-readable source into
an executable form, passing through several representations. The **compilation pipeline** is
a progression from description to realization; **build tools** (`make`, `cmake`) capture
dependencies, track updates, and give incremental, portable builds; **linking** resolves
external references - statically, absorbing library requirements into the executable, or
dynamically, postponing some resolution until runtime when shared libraries are mapped,
symbols resolved, and execution finalized via PLT/GOT lazy binding.

### Further reading

- *Computer Systems: A Programmer's Perspective* (CSAPP), Bryant & O'Hallaron, 3rd ed. -
  Ch. 7 (Linking): ELF, PLT, GOT, lazy binding.
- *Linkers and Loaders*, John R. Levine - symbol resolution, relocation.
- The ELF Specification (x86-64 ABI): <https://refspecs.linuxfoundation.org/elf/>
- `man ld`, `man objdump`, `man readelf`, `man nm`.
