#!/usr/bin/env bash

# Directory that holds this script (the q1/ folder) — the submission logs are
# written straight here so they land next to git-history.sh as the spec's tree shows.
Q1_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BASE="$HOME/git-assignment"
ROLLNO=x1chg956
USERNAME=x1chg956
USEREMAIL="cgodhandaraman@gmail.com"
GIT_REMOTE_HTTPS="https://github.com/x1chg956/x1chg956-git.git"
GIT_REMOTE_SSH="git@github.com:x1chg956/x1chg956-git.git"

mkdir -p "$BASE"

# ============================================================================
# Part 1 — ME ($ROLLNO): first commits on main          (clone, add, commit, push)
# ============================================================================
cd "$BASE"
git clone "$GIT_REMOTE_SSH" "$ROLLNO"
cd "$BASE/$ROLLNO"


# Identify myself on THIS clone only (--local).
git config --local user.name  "$ROLLNO"
git config --local user.email "$USEREMAIL"
git config --local --list          # verify: remote.origin.url / user.name / user.email

# Add the source files: passwords.h, utils.h, and the FIRST version of main.cpp
# (main.cpp at this point reads name + password from stdin WITHOUT prompts).
git add passwords.h utils.h main.cpp
git commit -m "feat: Login API"

# This first commit created the main branch. View it and copy the 40-char hash.
git log
git log -1 --format=%H               # the hash to record in README.md

# Example of what `git log -1` prints here (illustrative only — hashes will
# differ on every real run, so do NOT rely on this exact value):
#   commit <40-char-hash> (HEAD -> main)
#   Author: $ROLLNO <cgodhandaraman@gmail.com>
#   Date:   <date>
#
#       feat: Login API

# Create README.md reporting the hash of the commit above, then commit it.
git add README.md
git commit -m "Adding README"

# Push the main branch to the remote.
git push -u origin main

# ============================================================================
# Part 2 — FRIEND (${ROLLNO}-friend): branch off            (clone, pull, branch)
# ============================================================================
cd "$BASE"
git clone "$GIT_REMOTE_SSH" "${ROLLNO}-friend"
cd "$BASE/${ROLLNO}-friend"

# Identify the FRIEND on this clone.
git config --local user.name  "${ROLLNO}-friend"
git config --local user.email "$USEREMAIL"
git config --local --list

git pull                              # get the latest commits on main
git checkout -b thisisabetteridea     # create and switch to the new branch

# Copy new_passwords.h contents over passwords.h (adds user-ids).
cp new_passwords.h passwords.h

git add passwords.h
git commit -m "feat: The Better Idea"
git push -u origin thisisabetteridea

# ============================================================================
# Part 3 — ME ($ROLLNO): add login prompts on main       (commit, push)
# ============================================================================
cd "$BASE/$ROLLNO"

# Edit main.cpp to print "Enter Name:" and "Enter Password:" before reading.
# (Make that change in  editor, then:)
git add main.cpp
git commit -m "Fix: Adding Login Prompts"
git push origin main

# ============================================================================
# Part 4 — FRIEND (${ROLLNO}-friend): rebase onto main      (rebase)
# ============================================================================
cd "$BASE/${ROLLNO}-friend"
git fetch origin
git checkout thisisabetteridea
git rebase origin/main
# If git reports conflicts:
#   1) open the conflicted files and resolve them
#   2) git add <resolved-files>
#   3) git rebase --continue
# Repeat until the rebase finishes.
git push -f origin thisisabetteridea   # force-push: history was rewritten

# ============================================================================
# Part 5 — ME ($ROLLNO): merge friend's branch into main (merge, push)
# ============================================================================
cd "$BASE/$ROLLNO"
git fetch origin
git checkout main
git merge origin/thisisabetteridea
git push origin main

# ============================================================================
# Submission logs
# ============================================================================
# Run the same log command from each repo and save the output
git -C "$BASE/$ROLLNO"          log --oneline --graph --all --decorate > "$Q1_DIR/my-log.txt"
git -C "$BASE/${ROLLNO}-friend" log --oneline --graph --all --decorate > "$Q1_DIR/friend-log.txt"
