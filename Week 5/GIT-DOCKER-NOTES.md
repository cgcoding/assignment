# Git and Docker - Comprehensive Study Notes

> Distilled from the 54-slide *Software Management Tools* deck (Git, slides 1-32; Docker,
> slides 33-54), organized around what the assignment actually tests. Use this as the
> concept reference; use `ASSIGNMENT-APPROACH.md` for the step-by-step solving guide.

These two tools answer two different questions in the life of a project. **Git** answers
*"how did the code get to this state, and how do several people evolve it in parallel?"* -
it records the history of a codebase as a graph of snapshots. **Docker** answers *"how do I
make this code run the same way on every machine?"* - it packages an application together
with the exact userspace it needs, isolated from the host. The assignment exercises both:
Q1 walks a two-developer Git collaboration (branch -> rebase -> merge), and Q2 builds a
two-service Docker Compose application.

1. **Version control** - local vs centralized vs distributed; git's snapshot/hash model.
2. **The git object model** - blobs, trees, commits, refs, branches, `HEAD`.
3. **Everyday git** - the three areas, add/commit/log/diff, branching, merge vs rebase, remotes.
4. **Containers** - why they exist (environment drift), and how isolation works.
5. **Images and Dockerfiles** - build-time vs run-time instructions, layers.
6. **Docker Compose** - multi-container apps, health checks, service-name networking.

---

## 0. How the lecture maps to the assignment

| Deck topic | Slides | Assignment problem it supports |
|---|---|---|
| VCS models (local / central / distributed) | 3-5 | Q1 background (why a remote + two clones) |
| git design goals + snapshot/SHA-1 model | 6-7 | Q1 (commits as content-addressed snapshots) |
| Setup + workflow (`config`, `init`, the three areas) | 8-13 | Q1 Part 1 (`git config --local`, `add`, `commit`) |
| Git objects (blob/tree/commit) + refs/branches/tags | 14, 20 | Q1 (README records the commit hash; refs) |
| `git diff` variants, `git log` options | 15-18 | Q1 submission (`log --oneline --graph --all --decorate`) |
| Undoing (`amend`, `reset`, `checkout`) | 19 | Q1 (conflict cleanup, fixups) |
| Branching + `stash` | 20-23 | Q1 Part 2 (`checkout -b thisisabetteridea`) |
| `git merge` (preserves history, merge commit) | 24-26 | Q1 Part 5 (merge friend's branch into main) |
| `git rebase` (linear history, rewrites hashes) | 27-28 | Q1 Part 4 (rebase `thisisabetteridea` onto main) |
| Remotes (`clone`/`fetch`/`push`/`pull`/`remote add`) | 29-30 | Q1 (one remote, two clones, push/pull) |
| Why Docker + container isolation | 34-40 | Q2 background (reproducible API + tester) |
| Dockerfile + image build (RUN/COPY/WORKDIR/CMD) | 41-43 | Q2 (`api/Dockerfile`, `tester/Dockerfile`) |
| Image -> container, `docker run`, mounts/volumes | 44-47 | Q2 background (how images become services) |
| Docker Compose (services, `depends_on`, healthcheck) | 48-52 | Q2 (`docker-compose.yml`, health gating) |

The two halves of the deck line up with the two halves of the assignment:
**Git (slides 1-32) = Q1**, **Docker (slides 33-54) = Q2**.

---

## 1. Version control systems

### 1.1 Three generations of VCS

A version control system *records changes to a set of files over time so you can recall
specific versions later*. Two pieces of vocabulary recur:

- **Checkout** - the version you are currently working on.
- **Patch set** - the difference (delta) between one version and another.

The models evolved to remove single points of failure:

| Model | Examples | Strength | Weakness |
|---|---|---|---|
| **Local** | RCS | Simple, on one machine | No collaboration |
| **Centralized** | CVS, SVN | Collaboration via a central server | Central server is a single point of failure |
| **Distributed** | Git, Mercurial | Every client fully mirrors the repo | More concepts to learn |

In a **distributed** VCS, each client holds a *complete* copy of the repository and its
history. If the server dies, any client can restore it. Collaboration happens by syncing
between repositories rather than locking files on a server.

### 1.2 Git's design goals

- **Simple design.**
- **Speed** - most operations are local (no network round-trip).
- **Strong support for non-linear development** - thousands of parallel branches.
- **Fully distributed** - able to handle huge projects (e.g. the Linux kernel) efficiently.

### 1.3 The two ideas that make git different

1. **Every commit is a snapshot, not a diff.** Git stores a *complete record of all files*
   at each commit, not just the change from the previous one. (It deduplicates identical
   files internally, but conceptually a commit is a full snapshot.)
2. **Everything is content-addressed by a SHA-1 hash.** A file or directory is referred to
   by the 40-character hash of its contents, e.g.
   `4b9da6552252987aa493b52f8696cd6d3b000373`. This gives git **integrity**: if a byte
   changes, the hash changes, so corruption is detectable.

```
Version 1   Version 2   Version 3   Version 4   Version 5
   A           A           A           A1          A2
   B           B1          B1          B2          B2
   C           C1          C2          C2          C3
   -------------- commits over time -------------->
```

Each column is one commit - a full snapshot of every file as it stood at that point.

---

## 2. The git object model

### 2.1 Three kinds of object

Git's store is a **content-addressable filesystem**. Three object types, each named by its
own hash, build up a snapshot:

- **Blob** - the contents of a single file.
- **Tree** - a directory listing: names mapped to blobs (files) and other trees
  (subdirectories).
- **Commit** - metadata (author, committer, time, message) plus a pointer to one **root
  tree** and to its **parent commit(s)**.

```
commit  -> tree (root directory)
   |        |-- blob   (a file)
   |        |-- tree   (a subdirectory)
   |        |     |-- blob  (a file)
   |        ...
   |-- parent commit -> ...
```

Because a commit points to its parent(s), the history forms a **directed acyclic graph
(DAG)** of commits. Following parent pointers walks backwards through history.

### 2.2 Refs: human-friendly names for commits

Remembering 40-character hashes is painful, so git lets you attach names - **refs** - to
important commits. The two most common:

- **Branch** - a *movable* pointer. As you commit on the current branch, the branch pointer
  advances to the newest commit.
- **Tag** - a *static* pointer, used as a milestone/version marker; it does not move.

`HEAD` is a special **symbolic reference** that points to the current branch (and thus,
indirectly, to the commit you have checked out). Switching branches moves `HEAD` and changes
the files visible in your working directory.

> Everything - objects, refs, logs - lives inside the `.git` directory at the repo root.

---

## 3. Everyday git

### 3.1 Setup

```bash
sudo apt-get install git
git config --global user.name  "<user name>"
git config --global user.email "<email address>"
git config --global core.editor emacs
git config --global merge.tool  meld
git config --list                 # show the effective configuration

mkdir git-experiments && cd git-experiments
git init                          # create a new empty repository
```

`--global` writes to `~/.gitconfig` (applies to all repos). **`--local`** writes to
`.git/config` (applies to *this repo only*) - this is exactly what the assignment needs to
give the "you" clone and the "friend" clone different author identities.

### 3.2 The three areas

Every tracked file lives in one of three places, and the basic commands move files between
them:

```
Working directory --(git add)--> Staging area (index) --(git commit)--> Commit (repo)
        ^                                                                    |
        |---------------------- git restore / checkout ----------------------|
```

| Command | Moves | Meaning |
|---|---|---|
| `git add <file>` | working dir -> staging | Stage a change for the next commit |
| `git commit -m "msg"` | staging -> commit | Snapshot the staged changes |
| `git status` | - | Show what is staged / modified / untracked |
| `git restore <file>` | commit -> working dir | Discard working-dir changes |

A worked sequence (file moving through the areas):

```bash
touch file1.txt file2.txt
git add file1.txt          # file1.txt is now staged; file2.txt is untracked
git status                 # "Changes to be committed: new file: file1.txt"
git commit file1.txt -m "Committing the file file1.txt"
git log                    # shows the single commit, HEAD -> master/main
```

A subtle point the slides stress: `git add` snapshots the file *as it is at that moment*. If
you edit the file again **after** `git add` but **before** `git commit`, the commit captures
the *staged* version (v2), not the newer working-dir version (v3) - unless you `git add`
again or use `git commit <file>` to fold the working-dir version in.

### 3.3 Inspecting history: `git log`

```bash
git log                                        # full history with author/date/message
git log --oneline                              # one line per commit (short hash + subject)
git log --graph                                # ASCII art of the branch structure
git log -p                                     # show the diff each commit introduced
git log <file>                                 # history of one file
git log --oneline --graph --all --decorate     # the assignment's submission command
```

The submission command is worth dissecting, because Q1 is graded on its output:

| Flag | Effect |
|---|---|
| `--oneline` | One compact line per commit (`<short-hash> <subject>`) |
| `--graph` | Draw the commit DAG with `*` / `|` / `/` connectors |
| `--all` | Include **all** refs (every branch + remote-tracking branch), not just `HEAD` |
| `--decorate` | Annotate each commit with the refs pointing at it (`HEAD -> main`, `origin/main`, ...) |

### 3.4 `git diff` and its before/after framing

`diff file1 file2` answers *"what changes turn file1 into file2?"* - so you must identify a
**before** file and an **after** file. Git's diff variants differ only in which two states
they treat as before/after:

| Command | Compares | before | after |
|---|---|---|---|
| `git diff --no-index f1 f2` | f1 vs f2 | f1 | f2 |
| `git diff` | index vs working dir | index | working dir |
| `git diff --cached` | HEAD vs index | HEAD | index |
| `git diff HEAD` | HEAD vs working dir | HEAD | working dir |
| `git diff commitA commitB` | commitA vs commitB | commitA | commitB |

Reading a unified diff hunk: lines starting with `-` exist in *before* and are removed;
lines with `+` are added in *after*; unprefixed lines are unchanged context.

### 3.5 Undoing (handle with care)

| Goal | Command | Effect |
|---|---|---|
| Redo the last commit | `git commit --amend` | Replace the current commit with the staged files + a new message |
| Unstage a file | `git reset HEAD <file>` | Move file back from index to modified (commit -> index) |
| Discard a modification | `git checkout <file>` | Replace the working-dir file with the last committed version |

> The slides flag these as *"dangerous operations done under the guidance of trained
> professionals"* - they discard work or rewrite history. Know exactly what each does first.

---

## 4. Branching and stashing

### 4.1 Branches

- A single branch is a **sequential line of development**.
- A new branch starts a **parallel line** that does not interfere with the original -
  perfect for trying an idea that may or may not be merged later.
- Commits in a branch are **backward-chained** (each points to its parent).
- `HEAD` tracks the current branch; switching branches also switches the files in the
  working directory.

```bash
git checkout -b bname     # create branch bname and switch to it
git checkout bname        # switch to an existing branch bname
git branch                # list all branches (current one marked with *)
git branch -d bname       # delete branch bname
```

### 4.2 `git stash` - park work without committing

To change branch when you have uncommitted work but are not ready to commit, **stash** it:

```bash
git stash                              # push working area + index onto a stash stack
git stash list                         # show the stack of stashes
git stash apply --index stash@{n}      # restore the nth stash (with its staged state)
```

---

## 5. Combining branches: merge vs rebase

Both bring the work of one branch into another. They differ in **what history they leave
behind** - this is the conceptual heart of Q1.

### 5.1 `git merge` - preserve history

```bash
git checkout master      # be on the branch you want to merge INTO
git merge feature        # bring feature's history into master
```

- Merges the histories of two branches and creates a **merge commit with two parents**,
  preserving both lineages.
- **Does not rewrite history** - existing commit hashes are untouched.
- `master` advances to a new commit combining `master` and `feature`; the original
  `feature` commits remain intact.

```
Before:                          After merge:
A - B - C  (master)              A - B - C ------ M  (master)
     \                                \          /
      D - E  (feature)                 D - E ---   (feature)
```

> **Fast-forward special case.** If the target branch has *no* commits that the source
> branch lacks (the target is a strict ancestor), git just slides the branch pointer
> forward - **no merge commit is created** and history stays linear. This is exactly what
> happens in Q1 Part 5: after the friend rebases `thisisabetteridea` on top of `main`,
> merging it back into `main` is a fast-forward.

Useful merge commands:

```bash
git merge <branch>        # merge branch into the current branch
git merge --continue      # continue a merge after resolving conflicts
git merge --abort         # cancel a conflicted merge, reset to the pre-merge state
git log --merge           # show commits causing the merge conflict
git diff <branch>         # preview what would be merged
```

### 5.2 `git rebase` - rewrite for a linear history

```bash
git checkout feature        # be on the branch whose commits you want to replay
git rebase master           # replay feature's commits on top of master
```

- **Replays** commits from one branch onto the tip of another.
- Produces a **linear history** - no merge commits.
- **Rewrites history**: replayed commits get **new hashes** (`D -> D'`, `E -> E'`).

```
Before:                          After rebase (feature onto master):
A - B - C  (master)              A - B - C  (master)
     \                                    \
      D - E  (feature)                     D' - E'  (feature)
```

If conflicts arise during the replay, git pauses; you resolve the files, `git add` them, and
run `git rebase --continue`. Because rebasing changes hashes of already-pushed commits, the
branch usually must be **force-pushed** afterwards (`git push -f`).

### 5.3 When to use which

| | `merge` | `rebase` |
|---|---|---|
| History | Preserved (true graph, with merge commits) | Rewritten (linear, cleaner) |
| Commit hashes | Unchanged | Changed for replayed commits |
| Safe on shared/pushed branches? | Yes | Risky - needs force-push, coordinate first |
| Resulting graph | Shows where branches diverged/joined | Looks like one straight line |

---

## 6. Working with remotes

A **remote** is another copy of the repository (typically on GitHub/Bitbucket) that you sync
with.

```bash
# Link a local repo to a remote and name it "origin":
git remote add origin git@github.com:<user>/<repo>.git

git fetch origin              # bring in remote metadata/commits, but don't touch working dir
git push -u origin main       # publish local commits on branch main to origin
git pull origin main          # fetch + merge remote main into local main

# Start from an existing remote:
git clone git@github.com:<user>/<repo>.git
#   - copies the project into a new local repo
#   - checks out the default branch (usually main or master)
#   - auto-runs `git remote add origin <url>`
```

- **`fetch`** updates remote-tracking refs (e.g. `origin/main`) without changing your
  working files - safe to run anytime.
- **`pull`** = `fetch` + integrate (merge or rebase) into your current branch.
- **`push`** uploads your commits; `-u` sets the upstream so later `push`/`pull` need no
  arguments.

> **The git way:** work locally and independently; sync when ready by pushing. Q1's
> "two clones of one remote" setup is the minimal model of real collaboration: each clone is
> a full repo with its own identity, and `origin` is the shared meeting point.

---

## 7. Docker: why containers exist

### 7.1 The problem - environment drift

You build an app on Python 3.5.2 / Ubuntu 16.04; it works for you. A user on Python 3.10
runs it and it breaks, because an API you relied on was removed:

```python
import time
try:
    print(time.clock())          # removed in Python 3.8+
except AttributeError:
    print("time.clock() is not available in this Python version")
# 3.5.2  -> 0.036259
# 3.10.12-> time.clock() is not available in this Python version
```

The code didn't change - the *environment* did. **Containers freeze the environment** so the
app always sees the libraries, binaries, and config it was built against.

### 7.2 The high-level solution

- The host provides a sandboxed environment called a **container**.
- The container carries a **minimal userspace** compatible with the app (e.g. a slice of
  Ubuntu 16.04: glibc, libstdc++, libm, threading/linking/networking/security libs, core
  shell utilities, essential config files).
- The containerized app runs on the **host's kernel** but sees only its own userspace.

```
        +-------------------------------------------------+
        |  Docker Container: 16.04 userspace + 16.04 app  |
        +-------------------------------------------------+
        |  22.04 userspace (host) + dockerd               |
        +-------------------------------------------------+
        |  Kernel (6.8.0-...)                              |
        +-------------------------------------------------+
        |  x86-64 processor                               |
        +-------------------------------------------------+
```

A container is **not** a virtual machine: it shares the host kernel, so it starts in
milliseconds and uses far fewer resources than booting a full OS.

### 7.3 The three isolations

| Isolation | What it means |
|---|---|
| **Filesystem** | The app sees only the container's files; its filesystem ops never touch the host. |
| **Process** | A separate PID namespace - PID 1 in the container is not PID 1 on the host. A container process cannot signal (`kill`) processes outside its namespace; the host *can* signal into the container. |
| **Network** | The container has its own interfaces and IP. The host network cannot directly reach it, but the container can **expose ports** that map to the host for external access. |

### 7.4 What the host kernel must provide

Because the app runs on the host kernel, that kernel must be **compatible**:

- **System-call compatibility** - the syscalls the app uses must exist:
  memory (`mmap`, `brk`), process control (`fork`, `clone3`), filesystem
  (`open`/`read`/`write`/`close`), networking (`socket`/`connect`/`send`/`recv`), signals
  (`kill`, `sigaction`).
- **ABI compatibility** - calling conventions, data type sizes/alignment, endianness, and
  executable format (ELF) must match.

---

## 8. Images and Dockerfiles

### 8.1 Two steps: image, then container

1. From a **Dockerfile**, **build** a **docker image** - a static snapshot of a filesystem
   plus configuration.
2. **Run** the image to create a live **container**.

An example Dockerfile:

```dockerfile
FROM ubuntu:16.04                                  # start from a base 16.04 image
RUN apt-get update && apt-get install -y python3   # run a command, commit the result
RUN mkdir app                                       # run a command, commit the result
COPY date-time.py /app                              # copy host file into the image
WORKDIR /app                                         # set working dir (baked into metadata)
CMD python3 date-time.py                            # default command when a container starts
```

```bash
docker build -t my-python-app .                     # build the image, tag it my-python-app
```

### 8.2 Build-time vs run-time instructions (and layers)

Each instruction that changes the filesystem produces a new **image layer** stacked on the
previous one. The lecture splits the instructions by behaviour:

| Kind | Instructions | What happens during `build` |
|---|---|---|
| **Active modification** | `RUN` | Spins a temporary container, runs the command in `/bin/sh -c "..."`, **commits** the changed filesystem as the next layer |
| **Passive setup** | `COPY`, `WORKDIR`, `ENV` | No container started. `COPY` adds files; `WORKDIR`/`ENV` are baked into image **metadata** |
| **Startup instruction** | `CMD` | **Not executed at build**; saved as metadata to run when the container starts (only one effective `CMD`) |

### 8.3 Key Dockerfile instruction reference

| Instruction | Purpose | Example |
|---|---|---|
| `FROM` | Base image to start from | `FROM python:3.10-slim` |
| `RUN` | Execute a build command, commit a layer | `RUN pip install mysql-connector-python` |
| `COPY` | Copy files host -> image | `COPY server.py /app/` |
| `WORKDIR` | Set working dir for later instructions | `WORKDIR /app` |
| `CMD` | Default command at container start | `CMD ["python", "server.py"]` |
| `ENV` | Set an environment variable in the image | `ENV CXX=/usr/bin/g++` |
| `ARG` | Build-time variable | `ARG VERSION=16.04` (`FROM ubuntu:$VERSION`) |
| `VOLUME` | Declare a persistent storage location | `VOLUME /app` |
| `EXPOSE` | Document the port the app listens on | `EXPOSE 8080` |
| `USER` | Run as a non-root user | `USER appuser` |
| `SHELL` | Change the default shell for `RUN` | `SHELL ["/bin/bash", "-c"]` |

> `EXPOSE` is **documentation only** - it does not publish the port. Publishing happens at
> run time (`-p`) or via Compose. Q2 deliberately does **not** publish a port, because the
> tester talks to the API over the private Compose network.

---

## 9. From image to container

### 9.1 What `docker run` does

When you run a container, the Docker Engine allocates resources, sets up the isolated
environment, and launches the process named in `CMD` (or on the command line). The process
runs on the host kernel - no OS boot, so startup is fast.

```bash
docker build -t my-python-app .
docker run -it --name my-python-container my-python-app bash
#   -i  keep STDIN open
#   -t  allocate a pseudo-TTY
#   -it together => an interactive terminal session inside the container
```

### 9.2 Mounts and volumes (persistent / shared storage)

```bash
# Bind mount: expose a host directory inside the container
docker run -it --mount type=bind,source=/home/as/data,target=/app/data my-python-app bash

# Named volume: docker-managed persistent storage
docker run -it --mount type=volume,source=myvol,target=/app/data my-python-app bash
```

- **bind mount** - maps an existing host path into the container (host owns the data).
- **volume** - docker-managed storage that outlives the container (good for databases).

### 9.3 Useful `docker run` options

| Option | Effect | Example |
|---|---|---|
| `-u <user>` | Run as a specific user | `docker run -u root my-python-app whoami` |
| `-e KEY=VALUE` | Set an env var in the container | `docker run -e CXX=/opt/.../g++ my-python-app` |
| `-w <path>` | Working dir before running `CMD` | `docker run -w /app my-python-app pwd` |
| `--cap-add <cap>` | Grant a Linux capability | `docker run --cap-add=SYS_PTRACE my-python-app` |

### 9.4 Managing containers and images

```bash
docker ps -a                       # list all containers (running + exited)
docker images                      # list local images
docker exec -it <ctr> <cmd>        # run an extra process in a running container
docker attach <ctr>                # attach your terminal to the main process
docker stop <ctr>                  # graceful stop (a container also stops when CMD exits)
docker start <ctr>                 # relaunch a stopped container's original command
docker rm <ctr>                    # delete a stopped container
```

---

## 10. Docker Compose

### 10.1 What it is

Docker Compose runs and manages **multiple containers at once**, described in a single
`docker-compose.yml`. It manages containers, networks, and volumes together, and -
crucially for Q2 - **automatically connects services on an isolated private network so they
can reach each other by service name**.

### 10.2 Anatomy of a compose file

```yaml
version: '3.8'                 # optional in modern Compose
services:
  app:
    build:
      context: .
      dockerfile: MyDockerfile
    depends_on:
      db:
        condition: service_healthy   # wait until db is HEALTHY, not just started
  db:
    image: mysql:8
    volumes:
      - mysql-data:/var/lib/mysql
    environment:
      MYSQL_ROOT_PASSWORD: example
      MYSQL_DATABASE: mydb
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -u root -p$$MYSQL_ROOT_PASSWORD"]
      interval: 5s
      retries: 10
    command:
      - "--bind-address=0.0.0.0"
volumes:
  mysql-data:
```

Key ideas, each of which maps directly to a Q2 requirement:

- **`services`** - each named service becomes a container. The service name is also its
  **hostname** on the private network (so `app` reaches `db` at `host="db"`).
- **`build`** - build the service's image from a directory/Dockerfile (vs `image:` to pull a
  prebuilt one).
- **`healthcheck`** - a command run periodically inside the container; the service is
  `healthy` only when it succeeds. `interval`/`timeout`/`retries`/`start_period` tune it.
- **`depends_on ... condition: service_healthy`** - start ordering: a dependent service
  waits until its dependency reports **healthy** (not merely "started"). This is the correct
  alternative to a fragile `sleep`.
- **`volumes`** - declare persistent named storage.

### 10.3 Service-name networking (the Q2 linchpin)

Inside the Compose network, a service contacts another by its **service name**, e.g.
`http://api:5000` - never `localhost`, `127.0.0.1`, or the host IP (those would refer to the
*caller's own* container or the host, not the peer service). A health check, however, runs
*inside* the target container and so legitimately talks to `127.0.0.1` (itself).

### 10.4 Useful compose commands

```bash
docker compose up                       # build if needed, then start all services
docker compose up -d                    # ... detached (in the background)
docker compose build --no-cache         # force a clean rebuild (no cached layers)
docker compose down                     # stop and remove containers + networks
docker compose down --volumes           # ... also remove named volumes
docker compose logs                     # show logs from all services
docker compose logs -f                  # follow live logs

# How a grader exercises a tester-style app:
docker compose up --build --abort-on-container-exit --exit-code-from tester
```

`--abort-on-container-exit` stops the whole stack as soon as one container exits, and
`--exit-code-from tester` makes the overall command's exit code equal the tester's - so a
non-zero tester exit fails the run.

---

## 11. Tooling cheat-sheet

### 11.1 Git command reference

| Command | Use |
|---|---|
| `git init` | Create a new repository |
| `git clone <url>` | Copy a remote repo locally (sets up `origin`) |
| `git config [--global\|--local] k v` | Set config (global = all repos, local = this repo) |
| `git add <file>` | Stage changes |
| `git commit -m "msg"` | Snapshot staged changes |
| `git status` | Show staged / modified / untracked state |
| `git log [--oneline --graph --all --decorate]` | View history (the Q1 submission form) |
| `git diff [--cached] [HEAD] [A B]` | Compare two states (see the before/after table) |
| `git branch [-d] [name]` | List / delete branches |
| `git checkout [-b] <branch>` | Switch to (or create) a branch |
| `git stash [list\|apply]` | Park / restore uncommitted work |
| `git merge <branch>` | Merge a branch in (preserves history) |
| `git rebase <branch>` | Replay commits onto another branch (linear, rewrites hashes) |
| `git rebase --continue` / `git merge --abort` | Drive conflict resolution |
| `git remote add origin <url>` | Link to a remote |
| `git fetch` / `git pull` / `git push [-u] [-f]` | Sync with the remote |

### 11.2 Docker / Compose command reference

| Command | Use |
|---|---|
| `docker build -t <tag> .` | Build an image from a Dockerfile |
| `docker run [-it] [--name n] <img> [cmd]` | Create + start a container |
| `docker run --mount type=bind\|volume,...` | Attach host dir / named volume |
| `docker ps -a` / `docker images` | List containers / images |
| `docker exec -it <ctr> <cmd>` | Run an extra process in a running container |
| `docker stop\|start\|rm <ctr>` | Lifecycle operations |
| `docker compose up [--build] [-d]` | Start the multi-service app |
| `docker compose down [--volumes] [--remove-orphans]` | Tear it down |
| `docker compose logs [-f] [svc]` | View service logs |

### 11.3 Dockerfile instruction quick map

| Build-time (make a layer / metadata) | Run-time (metadata only) |
|---|---|
| `FROM`, `RUN`, `COPY`, `WORKDIR`, `ENV`, `ARG`, `USER`, `SHELL`, `VOLUME`, `EXPOSE` | `CMD` (and `ENTRYPOINT`) |

---

## 12. One-paragraph summary

Git models the evolution of a codebase as a **directed acyclic graph of commits**, where each
commit is a complete, SHA-1-addressed snapshot rather than a delta; branches are movable
pointers that enable concurrent strands of development, and the two ways to recombine them -
**merge** (which preserves history with a two-parent merge commit) and **rebase** (which
rewrites history into a clean linear sequence) - are the conceptual core of collaboration.
Docker solves the orthogonal problem of **environment drift** by packaging an application
with the exact userspace it needs into an **image** (built layer-by-layer from a Dockerfile),
then running that image as an isolated **container** on the host kernel; **Docker Compose**
composes several such containers into one application, wiring them onto a private network
where they address each other by service name and start in dependency order gated by health
checks. Together they make software both **traceable** (git) and **reproducible** (docker).

### Further reading

- *Pro Git*, Scott Chacon & Ben Straub - free at <https://git-scm.com/book> (the deck draws
  on this). Especially the chapters on Git internals, branching, and rebasing.
- Official git docs: <https://git-scm.com/docs>. Interactive: *Learn Git Branching*.
- *Docker Deep Dive*, Nigel Poulton (Publishdrive, 2023); *Using Docker*, Adrian Mouat
  (O'Reilly, 2016).
- Docker docs and *Play with Docker* (browser sandbox): <https://docs.docker.com>.
- Source deck: [Resources/Lecture - Git and Docker.pdf](<Resources/Lecture - Git and Docker.pdf>).
