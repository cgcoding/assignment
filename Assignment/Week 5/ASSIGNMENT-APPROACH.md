# Git and Docker - Step-by-Step Assignment Approach

> Companion to `GIT-DOCKER-NOTES.md` (the concept reference). This file is the command-level
> playbook for solving both questions and cross-references the existing answers in
> [q1/](q1) and [q2/](q2). The assignment PDF is
> [Resources/Assignment GIT-and-Docker.pdf](<Resources/Assignment GIT-and-Docker.pdf>).

**Q1 (Git): 15 marks** = Part 1 (2) + Part 2 (3) + Part 3 (2) + Part 4 (4) + Part 5 (4).
**Q2 (Docker): marks to be decided** (the PDF header notes *"Marks for Q2 to be decided"*).

> **Reproducibility note.** Q1 is graded by *running* your `git-history.sh` and checking that
> it reproduces the two submitted logs, then checking the logs for correctness. Commit hashes
> are content+time+author dependent, so **your hashes will differ** from any sample here -
> what must match is the *structure* (commit messages, branch topology, ref decorations).
> Q2 is graded by building and running the Compose stack in a Docker daemon; this workspace
> performs **static inspection only** (no Docker run), consistent with the report-only scope.

---

## Q1 - Git: a two-developer collaboration (15 pts)

### The mental model

You simulate two collaborators against **one** GitHub remote using **two local clones**:

- Clone `you` - author name `<roll-no>`.
- Clone `friend` - author name `<roll-no>-friend`.

Both set their identity with **`git config --local`** (per-clone, not `--global`). The story
walks a realistic feature flow: you ship a login API, your friend branches off a "better
idea", you fix the main branch in parallel, the friend **rebases** to pick up your fix, and
finally you **merge** the friend's branch back into `main`.

### Setup (once)

```bash
# 1. Create a PRIVATE GitHub repo named <roll-no>-git (append digits if taken).
# 2. Two clones of the SAME remote, each with its own identity:
git clone git@github.com:<user>/<roll-no>-git.git you
cd you     && git config --local user.name "<roll-no>"         && git config --local user.email <email>
cd ../     && git clone git@github.com:<user>/<roll-no>-git.git friend
cd friend  && git config --local user.name "<roll-no>-friend"  && git config --local user.email <email>
git config --local --list      # verify remote.origin.url / user.name / user.email
```

### Part 1 - First commit: You (2 pts)

Restated requirement: in the `you` clone, create the login source, make the first commit on
`main`, record its hash in a `README.md`, commit that, and push.

1. Download [Resources/passwords.h](<Resources/passwords.h>) into the working dir. Create
   `utils.h` implementing `bool login(string name, string password)` that returns `true`
   only if the user exists **and** the password matches, reusing the helpers from
   `passwords.h` (`userExists`, `getPassword`):

```cpp
// utils.h
#include "passwords.h"
bool login(string name, string password) {
    return userExists(name) && getPassword(name) == password;
}
```

2. Create `main.cpp` that reads a name and a password from stdin, calls `login`, and prints
   `Success!` or `Login Failed :(` - **without** prompts at this stage (prompts come in
   Part 3).
3. Stage and commit:

```bash
git add passwords.h utils.h main.cpp
git commit -m "feat: Login API"          # creates the main branch + first commit
git log -1 --format=%H                    # copy this 40-char hash into README.md
```

4. Create `README.md` containing that commit hash, then commit it:

```bash
git add README.md
git commit -m "Adding README"
```

5. Push: `git push -u origin main`.

**Gotchas:** use the exact commit messages (`feat: Login API`, `Adding README`); the README
must hold the hash of the **`feat: Login API`** commit (the last commit *before* the README
commit), not the README commit's own hash.

### Part 2 - Branch off: Your Friend (3 pts)

Restated requirement: in the `friend` clone, branch off `main`, swap in the user-id version
of the password DB, commit, and push the new branch.

```bash
cd friend
git pull                               # get the latest main
git checkout -b thisisabetteridea      # create + switch to the branch
cp new_passwords.h passwords.h         # overwrite with the user-id version
# (optionally adjust login() in utils.h for the new struct-based DB)
git add passwords.h                    # (+ utils.h if changed)
git commit -m "feat: The Better Idea"
git push -u origin thisisabetteridea
```

The new DB ([Resources/new_passwords.h](<Resources/new_passwords.h>)) replaces
`map<string,string>` with `map<string,UserRecord>` (each record adds a `userId`) and exposes
`getUserId`. `getPassword(name)` still exists but now returns `record.password`, so the
existing `login` keeps compiling - which is why step 3 is *"you may or may not need"* to edit
`utils.h`.

**Gotchas:** branch name must be exactly `thisisabetteridea`; push it to its **own** remote
branch (`-u origin thisisabetteridea`), not to `main`.

### Part 3 - Fixes: You (2 pts)

Restated requirement: back in the `you` clone on `main`, add the missing user prompts.

```bash
cd you
# Edit main.cpp to print "Enter Name:" and "Enter Password:" BEFORE each read.
git add main.cpp
git commit -m "Fix: Adding Login Prompts"
git push origin main
```

**Gotchas:** this happens on `main` *after* the friend already branched - that divergence is
the whole reason Part 4 needs a rebase.

### Part 4 - Rebase / Merge: Your Friend (4 pts)

Restated requirement: the friend pulls your new `main` work into `thisisabetteridea` via
**rebase** (chosen over merge), resolves any conflicts, and pushes.

```bash
cd friend
git fetch origin
git checkout thisisabetteridea
git rebase origin/main                 # replay "feat: The Better Idea" on top of your fix
# If conflicts (likely in passwords.h):
#   1) edit the conflicted file(s) to the desired final content
#   2) git add <resolved-files>
#   3) git rebase --continue           # repeat until rebase finishes
git push -f origin thisisabetteridea   # force-push: rebase rewrote history (new hashes)
```

**Gotchas:** rebasing rewrites commit hashes, so the push **must** be `-f` (force).
A conflict on `passwords.h` is expected (your `main` may differ from the friend's user-id
version) - resolve it to the intended final DB, then continue.

### Part 5 - Merge: You (4 pts)

Restated requirement: in the `you` clone, merge the friend's branch into `main` and push.

```bash
cd you
git fetch origin
git checkout main
git merge origin/thisisabetteridea     # fast-forward, because friend rebased onto your main
git push origin main
```

**Gotchas:** because Part 4 rebased `thisisabetteridea` directly on top of `main`, this merge
is a **fast-forward** - `main` simply advances to the friend's tip and the final history is
**linear** (no merge commit).

### Submission artifacts

```bash
git -C you    log --oneline --graph --all --decorate > q1/my-log.txt
git -C friend log --oneline --graph --all --decorate > q1/friend-log.txt
# Record EVERY command you actually ran into q1/git-history.sh
```

Expected `q1/` tree:

```
q1
|-- git-history.sh
|-- my-log.txt
`-- friend-log.txt
```

**Expected output shape** - a linear graph (one `*` per commit) in `my-log.txt`, with the
final commit decorated by all the converged refs, e.g.:

```
* <hash> (HEAD -> main, origin/main, origin/thisisabetteridea) feat: The Better Idea
* <hash> Fix: Adding Login Prompts
* <hash> Adding README
* <hash> feat: Login API
```

and `friend-log.txt` showing `thisisabetteridea` sitting on top of `origin/main`, with the
friend's stale local `main` decoration further down the graph.

---

## Q2 - Docker Compose: a two-service app (marks TBD)

### The mental model

Two services on a private Compose network:

- **`api`** - a stdlib-only Python HTTP server on `0.0.0.0:5000` with four fixed endpoints.
- **`tester`** - a script that waits for `api` to be **healthy**, calls all four endpoints
  via the hostname `api`, prints five exact lines, and exits 0 (non-zero on any mismatch).

Required tree (names must match **exactly**):

```
q2
|-- docker-compose.yml
|-- api
|   |-- Dockerfile
|   `-- server.py
`-- tester
    |-- Dockerfile
    `-- test_api.py
```

### Step 1 - The API server (`api/server.py`)

Restated requirement: listen on `0.0.0.0:5000`, stdlib only, four endpoints with **exact**
bodies and status 200.

| Endpoint | Request | Status | Exact body |
|---|---|---|---|
| Health | `GET /health` | 200 | `OK` |
| Square | `GET /square/7` | 200 | `49` |
| Reverse | `GET /reverse/docker-compose` | 200 | `esopmoc-rekcod` |
| Sum | `GET /sum?x=13&y=29` | 200 | `42` |

Approach - one `BaseHTTPRequestHandler.do_GET` that routes on the parsed path:

```python
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
# /health -> "OK"; /square/<n> -> str(n*n); /reverse/<s> -> s[::-1];
# /sum?x=&y= -> str(x+y).  Serve on ("0.0.0.0", 5000).
```

**Gotchas:** bodies must be byte-exact (no trailing text); bind `0.0.0.0` (not `127.0.0.1`)
so peers can reach it; use a *threading* server so the health check and the tester can hit it
concurrently; reverse of `docker-compose` is `esopmoc-rekcod` (13+13 chars, hyphen in the
middle).

### Step 2 - The API Dockerfile (`api/Dockerfile`)

Restated requirement: Python base image, set `WORKDIR`, copy **only** required files, run
`server.py`.

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY server.py ./
EXPOSE 5000          # documentation only; not strictly required
CMD ["python", "server.py"]
```

**Gotchas:** `COPY server.py ./` keeps the image minimal (don't `COPY . .`). `EXPOSE` does
not publish a port - and Q2 explicitly does **not** publish to the host.

### Step 3 - The tester (`tester/test_api.py`)

Restated requirement: call the API at base URL `http://api:5000`, check all four endpoints,
and on success print exactly these five lines in order, then exit 0:

```
HEALTH=OK
SQUARE=49
REVERSE=esopmoc-rekcod
SUM=42
ALL_TESTS_PASSED
```

On any incorrect response, exit with a **non-zero** status.

```python
BASE_URL = "http://api:5000"      # service name, NOT localhost / 127.0.0.1 / host IP
# fetch each path with urllib; if status != 200 or body != expected -> sys.exit(1)
# else print the five lines and sys.exit(0)
```

**Gotchas:** the hostname **must** be `api` (the Compose service name); print order matters;
`ALL_TESTS_PASSED` must be the last line; any failure path must return a non-zero exit code
so `--exit-code-from tester` fails the run.

### Step 4 - The tester Dockerfile (`tester/Dockerfile`)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY test_api.py ./
CMD ["python", "test_api.py"]
```

### Step 5 - Compose (`docker-compose.yml`)

Restated requirement: define `api` and `tester`; build each from its directory; give `api` a
health check; make `tester` start only after `api` is **healthy**; let `tester` reach `api`
by service name; no host port publishing needed.

```yaml
services:
  api:
    build: ./api
    healthcheck:
      test: ["CMD", "python", "-c", "<urllib GET http://127.0.0.1:5000/health == 'OK'>"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 3s
  tester:
    build: ./tester
    depends_on:
      api:
        condition: service_healthy
```

**Gotchas:** the health check runs *inside* the api container, so it targets
`http://127.0.0.1:5000/health` (itself) - that is the one legitimate use of `127.0.0.1`. The
`python:slim` image has **no `curl`/`wget`**, so the health check must use Python (`urllib`).
A `sleep`-based wait is explicitly **not** acceptable; use `condition: service_healthy`.

### How it is graded

```bash
docker compose down --volumes --remove-orphans
docker compose up --build --abort-on-container-exit --exit-code-from tester
docker compose logs tester        # must contain the five exact lines
docker compose down --volumes --remove-orphans
```

The grader also inspects `docker-compose.yml` to confirm `api` has a health check and
`tester` depends on the healthy `api`.

---

## Solution Validation

> **Report-only.** The following is a static inspection of the submitted solution files
> against the assignment spec. No solution code was modified or executed; Q1's git workflow
> and Q2's Docker stack were **not** run. Hash-level and runtime claims are reasoned from the
> source text.

### Q1 - Git history - Status: **Incorrect (script not runnable as written) + log inconsistency**

**Files checked:** [q1/git-history.sh](q1/git-history.sh),
[q1/my-log.txt](q1/my-log.txt), [q1/friend-log.txt](q1/friend-log.txt).

**What is right (the workflow is sound):**

- The five-part flow is faithfully reproduced: clone + `git config --local` identities,
  `git add`/`commit` of `passwords.h utils.h main.cpp` with **`feat: Login API`**, README
  with the recorded hash + **`Adding README`**, push `main`; friend `git checkout -b
  thisisabetteridea` + `cp new_passwords.h passwords.h` + **`feat: The Better Idea`**; your
  **`Fix: Adding Login Prompts`**; friend `git rebase origin/main` + `push -f`; your
  `git merge origin/thisisabetteridea` + push. Commit messages and branch names all match the
  spec.
- The submission logs use the exact required command (`git log --oneline --graph --all
  --decorate`).
- The graph topology is internally plausible in each file: `my-log.txt` is linear with all
  refs converged on the tip (consistent with a fast-forward merge after the friend rebased),
  and `friend-log.txt` shows `thisisabetteridea` on top of `origin/main` with a stale local
  `main` below.

**Concrete gaps:**

1. **Bash-illegal variable names break the clones (blocker).** Lines 7-8 of
   [q1/git-history.sh](q1/git-history.sh) declare `GIT-REMOTE-HTTPS=...` and
   `GIT-REMOTE-SSH=...`. Hyphens are not allowed in shell variable names, so these are **not
   assignments** - bash treats each as a command word and fails with *command not found*; the
   variables are never set. Worse, the later use `git clone "${GIT-REMOTE-SSH}" $ROLLNO`
   parses as the `${parameter-default}` form: parameter `GIT` is unset, so it expands to the
   literal `REMOTE-SSH`, i.e. the script runs `git clone "REMOTE-SSH" x1chg956` and aborts.
   Both clone steps (Part 1 and Part 2) therefore fail, so the grader's *"run git-history.sh
   and reproduce the logs"* check cannot pass. Fix: rename to underscore identifiers
   (`GIT_REMOTE_SSH`) and reference them as `"$GIT_REMOTE_SSH"`.
2. **Raw `git log` output pasted into the script body (lines 34-38).** The block
   `commit dd7d5bd... / Author: ... / Date: ... / feat: Login API` is neither quoted nor
   commented, so when the script runs, bash tries to execute `commit`, `Author:`, `Date:` as
   commands. With no `set -e` it won't halt, but it emits spurious *command not found* errors
   and is invalid as a runnable submission. Move it into a `#` comment or delete it.
3. **The two logs are mutually inconsistent.** [q1/my-log.txt](q1/my-log.txt) and
   [q1/friend-log.txt](q1/friend-log.txt) share the same commit *messages* and *structure*
   but have **completely disjoint hash sets** (`e898d19/0d835a0/6ea27ea/14d961f` vs
   `dd7d5bd/3037682/346d7e9/3973397`). Two clones of one shared remote must share the hashes
   of commits that came through that remote - e.g. the friend's `origin/main`
   *"Fix: Adding Login Prompts"* should equal your *"Fix: Adding Login Prompts"*, and after
   the fast-forward merge your `main` tip should equal the friend's `thisisabetteridea` tip.
   They don't, which indicates the two logs were captured from independent runs rather than a
   single consistent remote. Regenerate both logs from the *same* end-state.
4. **Minor - log redirection.** The final lines use `>>` (append, so re-running duplicates
   the logs; prefer `>`) and write `my-log.txt`/`friend-log.txt` into the current directory
   (after Part 5 that is `~/git-assignment/x1chg956`), not into `q1/` as the spec's tree
   shows. The committed files are in `q1/`, so they were evidently moved by hand; make the
   script write straight to the `q1/` paths.

**Net:** the *approach* encoded in the comments is correct and complete, but the script will
not execute as written and the two logs cannot both come from one remote - so against the
stated grading method (run the script, then check the logs) this needs fixing.

### Q2 - Docker Compose - Status: **Appropriate**

**Files checked:** [q2/docker-compose.yml](q2/docker-compose.yml),
[q2/api/Dockerfile](q2/api/Dockerfile), [q2/api/server.py](q2/api/server.py),
[q2/tester/Dockerfile](q2/tester/Dockerfile), [q2/tester/test_api.py](q2/tester/test_api.py).

**What was checked vs the spec:**

- **Structure** - the `q2/` tree matches the required layout (`docker-compose.yml`, `api/{Dockerfile,server.py}`, `tester/{Dockerfile,test_api.py}`) exactly.
- **`api/server.py`** - binds `0.0.0.0:5000`, stdlib only (`http.server`, `urllib.parse`),
  `ThreadingHTTPServer` for concurrency. Endpoint bodies verified by tracing the routing:
  `/health` -> `OK`; `/square/7` -> `str(7*7)` = `49`; `/reverse/docker-compose` ->
  `"docker-compose"[::-1]` = `esopmoc-rekcod`; `/sum?x=13&y=29` -> `str(13+29)` = `42`.
  All return status 200; bad inputs return 400 and unknown paths 404.
- **`docker-compose.yml`** - defines exactly `api` and `tester`; `api` built from `./api`,
  `tester` from `./tester`; `api` has a `healthcheck` that GETs
  `http://127.0.0.1:5000/health` via Python `urllib` (correct, since `slim` has no
  curl/wget) and checks the body equals `OK`; `tester` has
  `depends_on: api: condition: service_healthy`; no host port is published. Every Compose
  requirement (1-5) is satisfied.
- **`tester/test_api.py`** - base URL `http://api:5000` (the service name, as required, not
  `localhost`/`127.0.0.1`/host IP); checks all four endpoints; on success prints exactly
  `HEALTH=OK` / `SQUARE=49` / `REVERSE=esopmoc-rekcod` / `SUM=42` / `ALL_TESTS_PASSED` in
  order and `sys.exit(0)`; on any mismatch or request error writes a diagnostic to stderr and
  exits non-zero - matching the grader's expectations.
- **Dockerfiles** - both use `python:3.10-slim`, set `WORKDIR /app`, `COPY` only the single
  required file, and run the right script via `CMD`.

**Concrete gaps:** none material. Minor observations only:

- The compose file omits a top-level `version:` key - this is fine (and preferred) for modern
  Docker Compose, which ignores it; no action needed.
- `EXPOSE 5000` in [q2/api/Dockerfile](q2/api/Dockerfile) is informational only and harmless;
  the port is intentionally not published to the host, per the spec.

**Net:** Q2 fully satisfies the API, tester, health-check, startup-ordering, service-name
networking, and Dockerfile requirements; on a working Docker daemon it should produce the
exact five-line tester output and a zero exit code. (Runtime confirmation is out of scope
here per the report-only constraint.)

### Validation summary

| Question | Files | Status | Headline finding |
|---|---|---|---|
| Q1 - Git | [git-history.sh](q1/git-history.sh), [my-log.txt](q1/my-log.txt), [friend-log.txt](q1/friend-log.txt) | **Incorrect / Incomplete** | Hyphenated bash vars + pasted `git log` output make the script non-runnable; the two logs have disjoint hashes (not one shared remote). Workflow logic itself is correct. |
| Q2 - Docker | [docker-compose.yml](q2/docker-compose.yml), [api/](q2/api), [tester/](q2/tester) | **Appropriate** | All endpoints, health check, `service_healthy` gating, service-name networking, and Dockerfiles meet the spec. |
