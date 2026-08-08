# Rust Assignment — Solution Approach

Submission location: `Week 11/x1chg956/`. Reference material used throughout: [Rust by Example](https://doc.rust-lang.org/rust-by-example/), particularly the modules, ownership/borrowing, lifetimes, and `Rc`/`RefCell` chapters.

---

## Q1 — Reconstructing a Cargo Package from Rust Sources

**Location:** `x1chg956/Q1/course_results/`

**Step 1: Map each flat file to its intended module role.**
The 14 supplied files were read to find their function bodies' natural call graph (e.g. `library_root.rs` calls `load_records`, `build_summary` — clearly the lib crate root; `parser.rs` defines `parse_records`, called only from `input_root.rs` — clearly a submodule of `input`). This produced the required tree:

```
course_results (lib)                     course_results (default bin)   rankings (secondary bin)
├── model.rs                             src/main.rs                    src/bin/rankings/main.rs
├── input/mod.rs  (input_root.rs)        └── display/mod.rs             └── output/mod.rs
│   └── input/parser.rs                      └── display/table.rs           └── output/row.rs
└── analysis/mod.rs (analysis_root.rs)
    ├── analysis/classification.rs
    ├── analysis/statistics.rs
    └── analysis/ranking.rs
```

**Step 2: Create the Cargo layout.** `Cargo.toml` declares `edition = "2024"` and `default-run = "course_results"` — the latter is what makes `cargo run` pick the default binary without prompting, now that two `[[bin]]` targets exist (the second, `rankings`, is auto-discovered from `src/bin/rankings/main.rs` — no explicit `[[bin]]` entry needed).

**Step 3: Move each file to its new path/name, unchanged internally.** File bodies (function logic, struct fields, `DATA` constants, output strings) were copied verbatim — nothing computational was edited, per the restrictions.

**Step 4: Wire the module tree together.** Every new file needed the `mod` declarations for its children plus `use` statements for whatever it calls in sibling/ancestor modules (e.g. `input/mod.rs` needed `use crate::model::StudentRecord;` and `mod parser;`).

**Step 5: Get the public interface right with visibility, not blanket `pub`.**
Rust's privacy rule: an item (or module) is visible to the module it's defined in *and that module's descendants* — **not** its ancestors. So anything called from a parent module (e.g. `lib.rs` calling `analysis::build_summary`) needs at least `pub(crate)` on the callee. Everything that is purely an implementation detail (`parse_records`, `summarize`, `rank_records`, `passed`, `render_row`, …) was marked `pub(crate)` rather than `pub`, per the instruction "items used only inside the library should not be made public merely to silence an error." Only `analyse`, `rankings`, `CourseSummary`, and `StudentRecord` are truly `pub`.

**Step 6: Re-export the two public types without moving their definitions.**
`StudentRecord` lives in `model.rs`, `CourseSummary` lives in `analysis/statistics.rs`. Both are re-exported up the chain with `pub use` so external callers can reach them as `course_results::StudentRecord` / `course_results::CourseSummary`.
One subtlety hit and fixed here: `pub use analysis::CourseSummary;` at the crate root fails (`E0365`) if the intermediate re-export inside `analysis/mod.rs` is only `pub(crate) use statistics::CourseSummary;` — Rust does not allow laundering a `pub(crate)`-visible re-export into a fully `pub` one. The intermediate re-export had to be `pub use statistics::CourseSummary;` (the `analysis` *module* itself stays private, so this doesn't leak anything extra — only the crate root's own `pub use` decides what's actually externally visible).

**Step 7: Verify.**
```
cargo check --all-targets   # clean
cargo run                   # matches the required "Course summary" block exactly
cargo run --bin rankings    # matches the required "Rankings" block exactly
```

---

## Q2 — Ownership/Borrowing Fix (`reward` function)

**Location:** `x1chg956/Q2/`

**Diagnosis.** Three separate problems in the supplied program:
1. Missing `;` after `let additional_marks = 75` — syntax error.
2. `reward(s, additional_marks)` takes `Student` **by value**, so `s` is moved into the call and can't be used afterward in `main`'s final `println!`.
3. Inside `reward`, `let name = student.name;` **moves** the `name` field out of `student`, so the later `println!("Updated student: {student:?}")` — which needs to `Debug`-print the whole struct — fails (partial move).
4. `let top = student.marks.iter_mut().max().unwrap();` holds a `&mut i32` borrow into `student.marks` that (per the original code's control flow) stays alive until the final `*top` at the end of the function — but `student.marks.push(add_marks)` in between needs its own exclusive borrow of the same field, and the `struct.marks` reference `top` would still be needed after — an unresolvable borrow conflict as originally structured.

**Fix, in order of minimal necessary change:**
- Changed `reward`'s signature from `fn reward(mut student: Student, ...)` to `fn reward(student: &mut Student, ...)` — this alone fixes problem 2, since `main` now only lends `s` via `&mut s`.
- Changed `let name = student.name;` to `let name = &student.name;` — borrows instead of moves, fixing problem 3. This borrow and the later `iter_mut()` borrow of `student.marks` coexist fine because they touch disjoint fields.
- Added `let top = *top;` immediately after `*top += 5;` — this copies the `i32` value out and shadows `top`, ending the mutable borrow of `student.marks` right there, *before* `student.marks.push(...)` runs. This fixes problem 4 without reordering any of the required print/push/return steps.
- Fixed the missing semicolon and changed the call site to `reward(&mut s, additional_marks)`.

No `clone()`, no reconstructing `Student`, no field changes — only the signature, two let-bindings, and the call site changed.

**Verified output:**
```
Rewarding Priyanka; old highest mark = 81
Updated student: Student { name: "Priyanka", marks: [72, 86, 76, 75] }
Student { name: "Priyanka", marks: [72, 86, 76, 75] }; rewarded mark = 86
```
81 (the pre-existing max) + 5 = 86; the appended mark (75) correctly does not affect the max; `s` remains usable after the call.

---

## Q3 — Borrow-Checker Fix (`longest` / `add_name`)

**Location:** `x1chg956/Q3/`

**Diagnosis.** `longest(roster: &Roster) -> &str` returns a reference borrowed from `roster.names`. In `add_name`, `previous` holds that borrow, but it's still needed at the *final* `println!`, which comes *after* `roster.names.push(name)` — a mutable borrow of the same field. The borrow checker can't prove this safe (even though, physically, `Vec<String>` reallocation wouldn't move the heap data a `&str` points into — the checker is conservative about the *Vec's* buffer, not the `String`'s).

**Constraints that ruled out the "obvious" fixes:**
- Can't use `.clone()` or `.to_string()` to get an owned copy.
- Can't move the final `println!` before `push`.

**Fix.** Rewrote `longest` to return the **index** of the longest name (`usize`) instead of a `&str`. A `usize` is `Copy` and carries no lifetime tied to the `Vec`, so it survives `push` (which only appends — existing indices stay valid and point at the same, unmoved `String` elements). `add_name` then re-indexes `roster.names[previous]` at each point it needs the name (log entry, final print) — a fresh, short-lived borrow each time, never overlapping the `push`.

**Verified output:**
```
Previous longest name was Aniruddha
Roster { names: ["Mira", "Aniruddha", "Christopher"], log: ["Previous longest name: Aniruddha"] }
```

---

## Q4 — Two-Lifetime Enum (`lookup` / `Found<'a, 'b>`)

**Location:** `x1chg956/Q4/`

**Diagnosis.** The original `lookup<'a>(official: &'a [String], aliases: &'a [String], ...) -> Option<&'a str>` forces a *single* lifetime `'a` on both input slices. Rust then has to pick `'a` as the shorter of the two — `aliases`, which is dropped at the end of the inner block — even when the match actually came from `official` (which lives until the end of `main`). So `saved` is rejected as escaping its borrow, despite being safe in the case that matters.

**Fix.**
1. Introduced `enum Found<'a, 'b> { Official(&'a str), Alias(&'b str) }` — two *independent* lifetime parameters, one per source slice.
2. Rewrote `lookup<'a, 'b>(official: &'a [String], aliases: &'b [String], ...) -> Option<Found<'a, 'b>>` — `official` and `aliases` are no longer forced to share a lifetime.
3. Completed the match in `main` so a reference can only escape the inner block when it came from `official`:
   ```rust
   saved = match found {
       Some(Found::Official(name)) => Some(name),  // tied only to 'a — safe to keep
       Some(Found::Alias(_)) => None,               // tied to 'b — discarded, can't escape
       None => None,
   };
   ```
   Since `saved`'s type only ever holds data borrowed via `'a`, the compiler is happy for it to outlive the block where `aliases` (`'b`) is dropped.

**Verified output:** `Found name Mira` (compiles and runs; one harmless `#[allow(dead_code)]` on the intentionally-unused `Alias` payload).

---

## Q5 — TaskGraph (`Rc` / `Weak` / `RefCell`)

**Location:** `x1chg956/Q5/task_graph/` (binary crate `task_graph`, module `taskgraph`)

**Why these types are needed** (per Rust by Example's "Rc" and "RefCell" chapters):
- `Rc<RefCell<Task>>` — a `Task` needs **shared ownership** (the same task is referenced both from the `tasks` map and, potentially, from other tasks' successor lists) plus **interior mutability** (`add_dependency` needs to mutate a task's `successors` through a shared `Rc`, which alone only gives `&Task`).
- `Weak<RefCell<Task>>` for `successors` — a plain `Rc` here would create the possibility of reference cycles (task A depends on B, B depends on A — the assignment's own `main` deliberately creates a cycle: `parse → typecheck → codegen → parse`) which would leak memory under `Rc`'s reference counting. `Weak` breaks the cycle: it doesn't keep the pointee alive, and `.upgrade()` safely handles the case where the target has since been dropped.

**Implementation steps:**
1. `Task::new` — a plain constructor filling `name`, `duration`, and an empty `successors: Vec::new()`.
2. `TaskGraph::new(root_name, duration)` — builds one `Task`, wraps it in `Rc<RefCell<_>>`, stores a clone of that `Rc` both as `root` and as the first entry in the `tasks` map (`Rc::clone`, not a fresh task, so `root` and `tasks[root_name]` start out `Rc::ptr_eq`).
3. `TaskGraph::add_task(&mut self, name, duration)` — wraps a new `Task` and inserts it into `tasks`. (The spec's pseudocode showed `-> Self`, which isn't constructible from `&mut self`; implemented as returning `()` instead, matching how `main` actually calls and discards the result — treated as a documentation typo in the "fill this up" skeleton.)
4. `TaskGraph::get_task(&self, name) -> Option<Rc<RefCell<Task>>>` — `self.tasks.get(name).map(Rc::clone)`, handing the caller a new strong reference rather than a borrow tied to `&self`.
5. `TaskGraph::add_dependency(&mut self, before, after)` — looks up both tasks via `get_task`, then `before_task.borrow_mut().successors.push(Rc::downgrade(&after_task))`. Using `Rc::downgrade` (not `Rc::clone`) is exactly what avoids the reference-cycle leak from step 5's deliberate cycle.
6. `print_task_graph` — copied verbatim from the supplied `print_task_graph.rs` (unmodified, as instructed): sorts task names for deterministic output, marks the root with `*` via `Rc::ptr_eq`, and resolves each `Weak` successor with `.upgrade()`, printing `<dropped task>` for any that no longer exist.
7. `main.rs` — copied verbatim from the assignment text.

**Verified output:**
```
s1 = "4"
Building task graph...
  codegen (duration: 8) -> parse
  parse (duration: 3) -> typecheck
  typecheck (duration: 5) -> codegen
```
(Note: `main` calls `add_task("parse", 3)` again after `TaskGraph::new` already created `"parse"` as root — this replaces the map's `"parse"` entry with a *new* `Rc`, so it's no longer `Rc::ptr_eq` to `self.root`, hence no `*` marker on that line. This falls directly out of running the assignment's own `main` unmodified — not something introduced by this solution.)

---

## Q6 — Generic `best_by` with Trait Bounds

**Location:** `x1chg956/Q6/`

**Filling the blanks:**
- `impl Scored for Student { fn score(&self) -> i32 { self.mark } }` — trivial projection.
- `F: FnMut(&T) -> i32` — the closure passed by the caller captures `calls` **by mutable reference** (`calls += 1`), so it must be `FnMut` (not `Fn`, which couldn't mutate its capture, and not `FnOnce`, which could only be called once total).
- `best_score = score(best)` — evaluate the closure once on the first element to seed the running best.
- Loop body: `let item_score = score(item); if item_score > best_score { best = item; best_score = item_score; }` — one closure call per remaining element, updating `best`/`best_score` only on strict improvement.

**Why the closure is called exactly once per student:** the seed call handles `items[0]`, and the loop calls it exactly once for each of `items[1..]` — no re-scoring, no calling it during comparison logic itself. No `clone`, `sort`, or consuming of the slice — `best_by` only ever holds `&T` references into the caller's `items` slice.

**Verified output:** `Ravi scored 84; scoring function called 3 times` (3 students → 3 calls; Ravi has the highest mark).

---

## Verification summary

All six packages were built and run with the stock toolchain (`cargo 1.97.1`, edition 2024):

| Question | Command(s) run | Result |
|---|---|---|
| Q1 | `cargo check --all-targets`, `cargo run`, `cargo run --bin rankings` | Output matches spec exactly |
| Q2 | `cargo run` | Compiles, correct values, `s` still usable |
| Q3 | `cargo run` | Compiles, correct ordering preserved |
| Q4 | `cargo run` | Compiles, prints `Found name Mira` |
| Q5 | `cargo run` | Compiles, graph output matches spec |
| Q6 | `cargo run` | Compiles, correct winner and call count |

Build artifacts (`target/` directories) were removed before submission; only source files (`Cargo.toml`, `src/**/*.rs`) are included.
