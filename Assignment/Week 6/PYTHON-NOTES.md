# Python - Comprehensive Study Notes

> Distilled from the 44-slide *Week 6: Python* deck (Amitabha Sanyal), organized around what
> the assignment actually tests. Use this as the concept reference; use
> `ASSIGNMENT-APPROACH.md` for the step-by-step solving guide.

Python is a **dynamically typed, interpreted, garbage-collected** language whose values live
on the heap and whose variables are merely *names bound to objects*. The deck moves from how
Python runs (interpreter, bytecode, the `__main__` convention) through its core data model
(references, mutability, the built-in containers), up to the features the assignment leans on
most heavily: **comprehensions, first-class functions, OOP with inheritance, exceptions,
modules, and the standard library** (`json`, `os`, `collections`, `sys`, `re`, `pathlib`).
This document follows that arc:

1. **Running Python** - the interpreter model, bytecode, scripts vs modules.
2. **The data model** - references, mutability, lists/dicts/tuples/sets, comprehensions.
3. **Abstractions** - first-class functions, classes, inheritance, exceptions.
4. **The toolbox** - modules/packages, file & JSON I/O, `os`/`pathlib`, CLI, debugging, venv.

---

## 0. How the deck maps to the assignment

| Deck topic | Slides | Assignment problem it supports |
|---|---|---|
| Interpreter model, bytecode, `dis` | 5-9 | Background for all (mental model of execution) |
| `__main__` convention, modules | 5, 37-39 | Every `qN.py` uses `if __name__ == "__main__": main()` |
| References, mutability, `is` vs `==` | 8, 13 | Q1/Q2 board state, history lists |
| Lists, slicing, comprehensions | 10-15 | Q1 valid-moves, Q3 `dp` table, Q4 layers, all `[... for ...]` |
| Dictionaries + comprehensions + ops | 18-19 | Q1 policy dicts, Q2 policy lookup, Q4 `dist`/`best_eng` |
| Tuples, sets, `array` | 20 | Q1 `WINNING_LINES` tuples, Q4 English-word `set` |
| First-class functions, `lambda`, `key=` | 21 | `max(strategy, key=strategy.get)`, `sorted(..., key=...)` |
| Classes, constructors, methods | 22 | Q1 `ChessState`, Q2 `GameEngine` |
| Inheritance, `super`, custom types | 23-24 | Q2 custom `PolicyNotFoundError(Exception)` |
| Exceptions (`try/except/else/finally`) | 33-36 | Q2 `FileNotFoundError`/`JSONDecodeError`/`KeyError` |
| `collections` (`Counter`, `defaultdict`, `deque`) | 30-32 | Q4 `defaultdict`/`deque` BFS |
| File & JSON I/O (`with open`) | 40 | Q1 writes JSON, Q2 reads JSON, Q5 reads byte size |
| `os` / `pathlib` filesystem access | 3, 40-41 | Q5 `os.walk`/`os.rename`/`os.path.*` |
| `sys.argv` / `sys.stdin`, CLI | 42 | Q2 `input()`, Q3/Q4 `sys.stdin.read()` |

The five questions cluster into three "Parts" exactly as the deck's themes cluster:
**Part 1 (Q1-Q2) = OOP + JSON**, **Part 2 (Q3-Q4) = algorithms over the built-in containers**,
**Part 3 (Q5) = the `os` standard-library module**.

---

## 1. Running Python

### 1.1 Where Python fits

Python is a general-purpose **glue / scripting** language. The deck highlights five niches:

- **Scripting & automation** - manipulate files/dirs (`shutil`, `os`), glob paths (`rglob`),
  parse text/CSV/JSON (`csv.DictReader`, `json`), orchestrate other programs (`subprocess`).
- **Data analysis / scientific** - `numpy`, `scipy`, `pandas`, `matplotlib`.
- **Web & APIs** - `Flask`, `Django`, `FastAPI`, `requests`.
- **Machine learning** - `scikit-learn`, `PyTorch`, `TensorFlow`.
- **Wrapper/control layer** over C/C++/Fortran/Rust (e.g. `numpy`, the gdb-Python API).

### 1.2 Getting it to run

```bash
sudo apt install python3 python3-pip python3-venv   # system Python on Debian/Ubuntu
python3 --version                                    # check the interpreter
python3 -m pip --version
```

Three ways to invoke it:

```bash
python3                  # interactive REPL
python3 program.py       # run a script file
python3 -m module_name   # run a module as a program
```

### 1.3 Script or module? The `__main__` convention

Every file is *both* a runnable script and an importable module. The dunder check decides
which role it plays:

```python
# collatz.py
def collatz(n):
    while n > 1:
        print(n, end=" ")
        n = 3 * n + 1 if n % 2 else n // 2
    print(1)

def main():
    n = int(input("Enter n: "))
    collatz(n)

if __name__ == "__main__":   # only fires when run directly, not when imported
    main()
```

- Run directly (`python3 collatz.py`) -> `__name__ == "__main__"` -> `main()` runs.
- `import collatz` -> `__name__ == "collatz"` -> `main()` does **not** run; you call
  `collatz.collatz(7)` yourself.

This is why **all five solution files** end with `if __name__ == "__main__": main()` - it keeps
the importable logic separate from the run-when-launched behaviour.

### 1.4 The execution model: Python is interpreted

```
hello.py -> Syntax Analysis     (is the program well-formed?)
         -> Bytecode Generator  (emit code for a Virtual Machine) -> hello.pyc
         -> Bytecode Optimizer  (optimize the bytecode)
         -> VM Simulator        (the CPython VM interprets bytecode) -> results
```

- Source is **first compiled to bytecode**, then executed by the Python VM.
- Imported modules cache their bytecode under `__pycache__/`.
- Bytecode is a CPython **implementation detail** (not part of the language spec).

### 1.5 Inspecting bytecode with `dis`

```python
import dis
def collatz(n):
    while n > 1:
        print(n, end=" ")
        n = 3 * n + 1 if n % 2 else n // 2
    print(1)
dis.dis(collatz)
```

The body `n = 3*n + 1` disassembles into a sequence that uses the operand **stack**:
`LOAD_CONST 3`, `LOAD_FAST n`, `BINARY_MULTIPLY`, `LOAD_CONST 1`, `BINARY_ADD`,
`STORE_FAST n`. Reading bytecode is the surest way to see what the interpreter actually does.

---

## 2. The data model: references, mutability, containers

### 2.1 Values and variables are references

- A **C/C++ variable** denotes a typed storage location.
- A **Python variable** is a *name* bound to a heap object; the same name can be rebound to
  values of different types over time.
- The object on the heap carries the runtime **identity**, **type**, and **value**.

```python
>>> a = [10, 20]
>>> b = a          # b names the SAME object
>>> a is b         # reference (identity) equality
True
>>> a == b         # value equality
True
>>> c = [10, 20]   # a fresh, equal object
>>> a is c
False
>>> a == c
True
```

`is` compares **identity** (same object?); `==` compares **value**. Confusing the two is a
classic bug source.

### 2.2 Dynamic typing and its consequences

Types are checked **at the point of operation**, inside instructions like `BINARY_ADD`:

```python
def fact(n):
    if n < 0:
        return "The argument cannot be negative"   # returns a STRING
    elif n == 0:
        return 1
    return n * fact(n - 1)

print(4 + fact(arg))   # 4 + "..." fails ONLY when that path runs
```

Powerful and flexible, but **errors can hide on untested paths** - which is why the testing
and error-handling sections matter.

### 2.3 Lists: general-purpose, ordered, heterogeneous sequences

```python
>>> [1,2,3,4] == [4,1,3,2]          # ordered -> not equal
False
>>> a = [21.42, 'foobar', 3, 4, 'bark', False, 3.14159]   # mixed types allowed
>>> a[-5]          # negative indexing
3
>>> a[2:4]         # slice: a[2] up to (not including) a[4]
[3, 4]
```

Lists can nest to arbitrary depth and are implemented as **dynamic arrays** with
over-allocation (so `append` is amortized O(1)).

### 2.4 Slicing (and strides)

```python
a[:n]   == a[0:n]
a[n:]   == a[n:len(a)]
a[:n] + a[n:] == a == a[:]          # full copy with a[:]
>>> a = ['foo','bar','baz','bark','qux','cor']
>>> a[0:5:2]      # start:stop:step
['foo', 'baz', 'qux']
>>> a[5:0:-1]     # negative stride walks backwards
['cor', 'qux', 'bark', 'baz', 'bar']
```

### 2.5 Mutability: the operations that surprise people

Starting each time from `a = [1, 'str', [3,[4,True]], 6, 7]; b = a`:

| Operation | Effect | `a is b` after? |
|---|---|---|
| `a.append([8,9])` | adds **one** object (the list) at the end | `True` (in-place) |
| `a.extend([8,9])` | adds the **elements** `8` and `9` | `True` (in-place) |
| `a += [8,9]` | in-place concatenation | `True` (in-place) |
| `a = a + [8,9]` | builds a **fresh** list, rebinds `a` | `False` (new object) |
| `a.insert(2, 'name')` | inserts at an index | `True` (in-place) |

The key contrast: `+=` mutates the object in place (others sharing it see the change), while
`a = a + [...]` creates a new object and only rebinds `a`.

### 2.6 List comprehensions

A compact way to build lists from **generators** (the `for` clauses) and **guards** (the `if`
clauses):

```python
>>> [x*x for x in [1,2,3,4,5,6,7] if x % 2 == 0]   # guard filters
[4, 16, 36]
>>> [x+y for x in [1,2,3] for y in [5,6,7]]        # two generators = nested loops
[6, 7, 8, 7, 8, 9, 8, 9, 10]
```

Equivalent expanded form of the first:

```python
result = []
for x in [1,2,3,4,5,6,7]:
    if x % 2 == 0:
        result.append(x*x)
```

A comprehension may have any number of generators/guards; a guard may only use variables from
preceding generators or the enclosing scope. Quicksort reads beautifully this way:

```python
def qsort(lst):
    if lst == []:
        return []
    pivot = lst[0]
    lower  = qsort([x for x in lst[1:] if x <  pivot])
    higher = qsort([x for x in lst[1:] if x >= pivot])
    return lower + [pivot] + higher
```

### 2.7 Memory management and garbage collection

In C/C++ every `malloc` is an obligation to `free` exactly once on **every** path - missing it
causes **leaks**, freeing twice is a **double free**, and using after free yields a **dangling
pointer** (aliasing makes ownership ambiguous).

Python removes that burden:

- Objects are heap-allocated; names, list slots, dict entries, and fields hold **references**.
- When an object becomes **unreachable**, it is reclaimed automatically.
- CPython uses **reference counting** plus a **cyclic garbage collector** (for reference
  cycles). The `gc` module exposes the collector.

### 2.8 Dictionaries (hash maps)

```python
>>> phonebook = {"bob": 7387, "alice": 3719, "jack": 7052}
>>> phonebook = {name: num for name, num in zip(["bob","alice"], [7387, 3719])}  # comprehension
>>> phonebook["bob"]
7387
```

Keys must be **hashable** (immutable values like strings, numbers, tuples). Core operations:

| Method | Meaning |
|---|---|
| `d.get(key[, default])` | value for `key`, or `default` if absent (no `KeyError`) |
| `d.items()` / `d.keys()` / `d.values()` | iterable **views** of pairs/keys/values |
| `d.pop(key[, default])` | remove `key` and return its value |
| `d.update(obj)` | merge another dict/iterable of pairs |
| `d.clear()` | empty the dict |

`d.get(k, 0)` is the idiomatic "counter increment" pattern: `agg[k] = agg.get(k, 0) + v`.

### 2.9 Other containers: tuples, `array.array`, sets

```python
point_3d = (4.6, 5.7, -2.1)               # tuple: immutable container
import array
arr = array.array("f", (1.0, 1.5, 2.0))   # C-like, homogeneous, compact & fast
vowels = {"a", "e", "i", "o", "u"}         # set: unordered, unique, O(1) membership
```

Tuples are immutable (hashable -> usable as dict keys); `array.array` is space/time efficient
because it stores raw same-typed values; sets give fast membership and de-duplication.

---

## 3. Abstractions: functions, classes, exceptions

### 3.1 First-class functions

Functions are values: assign, pass, return, and store them.

```python
def f(x, y):
    return x**2 + y

g = f                                  # assign to a variable
(lambda x, y: x**2 + y)(3, 2)          # anonymous one-expression function
list(map(square, [1, 2, 3]))           # pass as an argument

def make_power(n):                     # return a function (closure over n)
    def power(x):
        return x**n
    return power
square = make_power(2)

funcs = [square, cube]                 # store in a container
[fn(3) for fn in funcs]
```

The `key=` parameter is the workhorse application: `max(strategy, key=strategy.get)` picks the
dict key with the largest value; `sorted(items, key=lambda it: it[1], reverse=True)` sorts by a
computed field.

### 3.2 Classes and objects

```python
class Account:
    init_message = "Welcome customer"          # class variable (shared by all instances)

    def __init__(self, account_holder, balance):   # constructor
        self.account_holder = account_holder        # instance variables
        self.balance = balance

    def show(self):                            # methods take `self` explicitly
        print(self.account_holder, self.balance)

    def withdraw(self, amount):
        if amount <= self.balance:
            self.balance -= amount
            return self.balance
        return "Insufficient funds"
```

- **Class variables** belong to the class; **instance variables** (set via `self.x = ...`) belong
  to each object.
- Every method's first parameter is the receiver, conventionally `self`.

### 3.3 Inheritance

```python
class Protected_Account(Account):                  # derive from Account
    def __init__(self, passwd, account_holder, balance):
        super().__init__(account_holder, balance)  # call base constructor
        self.__password = passwd                   # name-mangled "private" member

    def withdraw(self, amount, passwd):            # override
        if passwd == self.__password:
            return super().withdraw(amount)        # delegate to base
        return "Transaction failed, wrong password"
```

- `super()` reaches the base class's methods/constructor.
- A leading `__name` is **name-mangled** (`_ClassName__name`), so `pacc.__password` raises
  `AttributeError` from outside - Python's convention for "private".
- Unoverridden methods (e.g. `show`) are inherited unchanged.

### 3.4 Classes are themselves first-class objects

A class is a runtime object: pass it, store it, return it, and call it to make instances.

```python
def open_account(account_class, holder, balance):
    return account_class(holder, balance)          # the class is just a value here

a = open_account(SavingsAccount, "Asha", 5000)     # factory pattern
b = open_account(CurrentAccount, "Ravi", 8000)
```

### 3.5 Worked example: dictionaries + sorting (IPL scores)

Reading structured text into nested dicts and producing a ranked list - the same shape as the
assignment's parsing tasks:

```python
num_matches = int(input())
match_dict, aggregate = {}, {}
for _ in range(num_matches):
    match_name, scores_str = input().strip().split(':')
    match_scores = {}
    for score in scores_str.split(','):
        player, run_str = score.split('-')
        run = int(run_str)
        match_scores[player] = run
        aggregate[player] = aggregate.get(player, 0) + run   # accumulate
    match_dict[match_name] = match_scores
sorted_aggregate = sorted(aggregate.items(), key=lambda item: item[1], reverse=True)
```

### 3.6 Worked example: regex + `Counter` (spy diary)

```python
import sys, re
from collections import Counter

local_part = r"(?:[A-Za-z0-9._%+-]+)"
domain     = r"(?:[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
re_email   = r"\b(" + local_part + "@" + domain + r")\b"
re_number  = r"(\b[1-9][0-9]{9}\b)"

emails, numbers = [], []
with open(sys.argv[1], "r") as fp:
    for line in fp:
        emails  += re.findall(re_email, line)
        numbers += re.findall(re_number, line)
count_emails  = Counter(emails)     # {value: count}
count_numbers = Counter(numbers)
```

`Counter` is a dict subclass that tallies occurrences in one pass - exactly the tool for
frequency problems.

### 3.7 Exceptions

```python
try:
    int("abc")
except ValueError as e:
    print(e)            # invalid literal for int() with base 10: 'abc'
```

Full shape with `else` and `finally`:

```python
try:
    result = 10 / 2
except ZeroDivisionError:
    print("Division by zero!")
else:
    print("Result is", result)   # runs only if no exception
finally:
    pass                         # ALWAYS runs (cleanup), even during unwinding
```

**Flow of control:** on an error Python stops the `try` block, searches for a matching
`except`, and performs **stack unwinding** - popping frames (running their `finally` blocks and
context-manager cleanup) until a handler is found; if none, the program ends with a traceback.

Retry-with-recovery pattern:

```python
for attempt in range(3):
    try:
        result = contact_server()
        break
    except TimeoutError:
        print("Server did not respond; retrying...")
        time.sleep(1)
else:                                   # the for/else runs if no break happened
    print("Server unavailable after three attempts.")
```

Commonly handled built-ins:

| Exception | Raised when |
|---|---|
| `IndexError` | sequence index out of range |
| `KeyError` | dict key not found |
| `TypeError` | operation applied to an inappropriate type |
| `ValueError` | right type but inappropriate value |
| `ZeroDivisionError` | division/modulo by zero |
| `FileNotFoundError` | file/dir requested but missing |
| `ImportError` | an `import` failed |

You define your own by subclassing `Exception` (e.g. Q2's `PolicyNotFoundError`).

---

## 4. The toolbox: modules, I/O, OS, CLI, debugging

### 4.1 Modules and imports

A module is a `.py` file; importing it exposes the names in its namespace.

```python
import stats              # PREFERRED - origins stay visible: stats.mean(...)
from stats import mean    # selective import
from numpy import *       # AVOID - imports an unknown set of names, risks clashes
```

`from M import *` is discouraged because it pollutes the namespace and can silently shadow
names (e.g. `numpy.mean` vs `stats.mean`).

### 4.2 Inspecting namespaces

- `globals()` / `locals()` - the global / local name->value mappings.
- `vars(obj)` / `obj.__dict__` - an object's (or class's) attribute mapping.
- `dir(obj)` - lists available **names** (not their values).

### 4.3 Packages, the standard library, PyPI

A **package** is a directory (historically with `__init__.py`) grouping modules under dotted
names:

```
project/
  analysis/
    __init__.py
    io.py
    stats.py
```

```python
from analysis import stats
from analysis.io import read_marks
```

The **standard library** ships with Python (`sys`, `os`, `pathlib`, `re`, `collections`,
`json`, `argparse`, ...). Third-party packages come from **PyPI** via `pip`.

### 4.4 File and JSON I/O

Always use `with` so files close automatically (even on exceptions):

```python
with open("marks.txt", "r", encoding="utf-8") as f:   # text mode -> str
    for line in f:
        roll, marks = line.split()

with open("image.png", "rb") as f:                    # binary mode -> bytes
    header = f.read(8)
```

Common modes: `"r"`, `"w"`, `"a"`, `"rb"`, `"wb"`. JSON serialization rides on the same
pattern (used directly in Q1/Q2):

```python
import json
with open("policy.json", "w", encoding="utf-8") as f:
    json.dump(obj, f, indent=2, sort_keys=True)   # dict -> JSON text
with open("policy.json", "r", encoding="utf-8") as f:
    obj = json.load(f)                            # JSON text -> dict
```

### 4.5 Paths with `pathlib`

```python
from pathlib import Path
data_dir   = Path("data")
input_file = data_dir / "marks.txt"     # `/` joins paths
input_file.name      # 'marks.txt'
input_file.suffix    # '.txt'
input_file.exists()  # bool
```

Prefer `Path` objects over manual string surgery; path operations become method calls.

### 4.6 The `os` module (filesystem access)

The deck frames `os` as the gateway to OS services (`os.getcwd`, `os.environ`, `os.makedirs`,
`os.system`). For Q5 the relevant calls are:

```python
import os
for dirpath, dirnames, filenames in os.walk(root):   # recursive top-down traversal
    ...
os.path.join(dirpath, name)        # build a path
os.path.splitext(path)             # ('base', '.ext')
os.path.getsize(path)              # size in bytes
os.rename(src, dst)                # move/rename
os.path.relpath(path, start)       # path relative to start
```

### 4.7 Command-line arguments and stdin

```python
import sys
if len(sys.argv) != 2:                 # argv[0] is the script name
    print("Usage: python3 prog.py FILE")
    sys.exit(1)
path = sys.argv[1]

data = sys.stdin.read().split()        # competitive-style bulk read (Q3, Q4)
```

`argparse` is the structured alternative for non-trivial CLIs.

### 4.8 Debugging

```python
assert count > 0, "Count must be positive"   # cheap invariants
breakpoint()                                  # drop into the debugger here
```

Run under `pdb`: `python3 -m pdb program.py`. Core commands: `next` (step over), `step` (step
into), `break 20` (and conditional `break 20, x==0`), `continue`, `where`, `up`/`down`,
`p expr`, `args`, `locals()`, `display x`. Good recipe: **reproduce, minimize, inspect, fix,
retest.**

### 4.9 Virtual environments and pip

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install requests pandas
python -m pip freeze > requirements.txt
deactivate
```

A venv isolates a project's dependencies from system Python. Use `python -m pip` so `pip`
belongs to the selected interpreter.

---

## 5. Idiom & tooling cheat-sheet

### 5.1 Language idioms

| Idiom | Use |
|---|---|
| `if __name__ == "__main__": main()` | run-as-script guard |
| `[f(x) for x in xs if cond]` | list comprehension (map + filter) |
| `{k: v for k, v in pairs}` | dict comprehension |
| `d.get(k, default)` | safe lookup with fallback |
| `agg[k] = agg.get(k, 0) + v` | accumulate counts |
| `max(d, key=d.get)` | key with the largest value |
| `sorted(xs, key=..., reverse=...)` | custom-ordered sort |
| `with open(...) as f:` | auto-closing resource |
| `try/except/else/finally` | structured error handling |
| `raise CustomError(...) from exc` | chain exceptions, preserve cause |
| `for ... else:` | else runs if loop didn't `break` |

### 5.2 Standard-library quick reference

| Module / name | Use |
|---|---|
| `json.dump` / `json.load` | dict <-> JSON file |
| `os.walk` / `os.path.*` / `os.rename` | recursive traversal, path ops, rename |
| `pathlib.Path` | object-oriented paths |
| `sys.argv` / `sys.stdin` / `sys.exit` | CLI args, bulk input, exit codes |
| `collections.defaultdict` | dict with automatic default values |
| `collections.deque` | O(1) FIFO queue (BFS) |
| `collections.Counter` | frequency tallies |
| `re.findall` | regex extraction |
| `dis.dis` | inspect bytecode |
| `math.inf` | sentinel for minimax bounds |
| `pdb` / `breakpoint()` | interactive debugging |

### 5.3 Tools / commands

| Command | Use |
|---|---|
| `python3 prog.py` | run a script |
| `python3 -m module` | run a module as a program |
| `python3 -m pdb prog.py` | debug under pdb |
| `python3 -m venv .venv` | create a virtual environment |
| `python -m pip install pkg` | install a dependency |
| `echo "in" \| python3 prog.py` | feed stdin to a stdin-reading script |

---

## 6. One-paragraph summary

Python is an **interpreted, dynamically typed, garbage-collected** language: source is compiled
to bytecode and run by the CPython VM, variables are **names bound to heap objects** (so `is`
checks identity while `==` checks value), and the runtime reclaims unreachable objects via
reference counting plus a cyclic collector. Its expressive core - **comprehensions**,
**first-class functions** with `key=`/`lambda`, **classes with inheritance**, and **exceptions**
with `try/except/else/finally` - sits on top of versatile built-in containers (lists, dicts,
tuples, sets) and a deep **standard library** (`json`, `os`, `pathlib`, `collections`, `sys`,
`re`). Mastering that combination is exactly what lets you express the assignment's minimax
solver, JSON-driven CLI, dynamic-programming allocator, BFS translator, and `os`-module file
sweeper concisely and correctly.

### Further reading

- *The Python Tutorial* - <https://docs.python.org/3/tutorial/> (esp. Data Structures, Modules,
  Errors and Exceptions, Classes).
- *The Python Standard Library* - <https://docs.python.org/3/library/> (`json`, `os`,
  `pathlib`, `collections`, `sys`, `re`).
- *The Python Language Reference - Execution & Data model* -
  <https://docs.python.org/3/reference/>.
- `dis` (bytecode), `pdb` (debugging), and `venv` module docs.
