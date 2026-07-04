#!/usr/bin/env bash
set -e

# Directory that holds this script (the q1/ folder) — the submission logs are
# written straight here so they land next to git-history.sh as the spec's tree shows.
Q1_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# The provided passwords.h / new_passwords.h live in the assignment Resources folder.
RESOURCES_DIR="$Q1_DIR/../Resources"

BASE="${BASE:-$HOME/git-assignment}"
ROLLNO=x1chg956
USEREMAIL="cgodhandaraman@gmail.com"

# Remote repository. For grading against GitHub, set:
#   GIT_REMOTE="git@github.com:x1chg956/x1chg956-git.git"
# By default the script creates a local bare repository so the whole five-part
# workflow is reproducible offline with identical semantics (one shared remote,
# two clones). Both clones point at the SAME remote either way.
GIT_REMOTE="${GIT_REMOTE:-$BASE/${ROLLNO}-git.git}"

mkdir -p "$BASE"

# Start from a clean slate so the script is re-runnable end to end.
rm -rf "$BASE/$ROLLNO" "$BASE/${ROLLNO}-friend"
if [ "$GIT_REMOTE" = "$BASE/${ROLLNO}-git.git" ]; then
    rm -rf "$GIT_REMOTE"
    git init --bare --initial-branch=main "$GIT_REMOTE"
fi

# ============================================================================
# Part 1 — ME ($ROLLNO): first commits on main          (clone, add, commit, push)
# ============================================================================
cd "$BASE"
git clone "$GIT_REMOTE" "$ROLLNO"
cd "$BASE/$ROLLNO"
git checkout -b main 2>/dev/null || git checkout main

# Identify myself on THIS clone only (--local).
git config --local user.name  "$ROLLNO"
git config --local user.email "$USEREMAIL"
git config --local --list          # verify: remote.origin.url / user.name / user.email

# 1. passwords.h comes from the assignment resources folder.
cp "$RESOURCES_DIR/passwords.h" passwords.h

#    utils.h implements  bool login(string name, string password)  using the
#    auxiliary functions defined in passwords.h (works unchanged with
#    new_passwords.h too, since it exposes the same helpers).
cat > utils.h <<'EOF'
#ifndef UTILS_H
#define UTILS_H

#include <string>
#include "passwords.h"

using std::string;

bool login(string name, string password)
{
    return userExists(name) && getPassword(name) == password;
}

#endif
EOF

# 2. First version of main.cpp: reads name + password from stdin WITHOUT prompts.
cat > main.cpp <<'EOF'
#include <iostream>
#include <string>
#include "utils.h"

using std::cin;
using std::cout;
using std::endl;
using std::string;

int main()
{
    string name, password;
    cin >> name >> password;

    if (login(name, password)) {
        cout << "Success!" << endl;
    } else {
        cout << "Login Failed :(" << endl;
    }

    return 0;
}
EOF

# 3. Stage and commit with the required message.
git add passwords.h utils.h main.cpp
git commit -m "feat: Login API"

# This first commit created the main branch. View it and copy the 40-char hash.
git log
FIRST_HASH=$(git log -1 --format=%H)   # the hash to record in README.md

# 4. Create README.md reporting the hash of the commit above, then commit it.
cat > README.md <<EOF
# ${ROLLNO}-git

Login page for the Git assignment.

Hash of the first commit (feat: Login API): ${FIRST_HASH}
EOF
git add README.md
git commit -m "Adding README"

# 5. Push the main branch to the remote.
git push -u origin main

# ============================================================================
# Part 2 — FRIEND (${ROLLNO}-friend): branch off            (clone, pull, branch)
# ============================================================================
cd "$BASE"
git clone "$GIT_REMOTE" "${ROLLNO}-friend"
cd "$BASE/${ROLLNO}-friend"

# Identify the FRIEND on this clone.
git config --local user.name  "${ROLLNO}-friend"
git config --local user.email "$USEREMAIL"
git config --local --list

git pull origin main                  # get the latest commits on main
git checkout -b thisisabetteridea     # create and switch to the new branch

# Copy new_passwords.h contents over passwords.h (adds user-ids).
# new_passwords.h comes from the assignment resources folder.
cp "$RESOURCES_DIR/new_passwords.h" passwords.h

# utils.h needs NO change: new_passwords.h keeps the same auxiliary functions
# (userExists / getPassword), so login() still compiles and behaves correctly.

git add passwords.h
git commit -m "feat: The Better Idea"
git push -u origin thisisabetteridea

# ============================================================================
# Part 3 — ME ($ROLLNO): add login prompts on main       (commit, push)
# ============================================================================
cd "$BASE/$ROLLNO"

# Edit main.cpp to print "Enter Name:" and "Enter Password:" before reading.
cat > main.cpp <<'EOF'
#include <iostream>
#include <string>
#include "utils.h"

using std::cin;
using std::cout;
using std::endl;
using std::string;

int main()
{
    string name, password;

    cout << "Enter Name: ";
    cin >> name;
    cout << "Enter Password: ";
    cin >> password;

    if (login(name, password)) {
        cout << "Success!" << endl;
    } else {
        cout << "Login Failed :(" << endl;
    }

    return 0;
}
EOF

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
# Repeat until the rebase finishes. (Here main touched main.cpp while this
# branch touched passwords.h, so the rebase completes without conflicts.)
git push -f origin thisisabetteridea   # force-push: history was rewritten

# ============================================================================
# Part 5 — ME ($ROLLNO): merge friend's branch into main (merge, push)
# ============================================================================
cd "$BASE/$ROLLNO"
git fetch origin
git checkout main
git merge origin/thisisabetteridea     # fast-forward after the rebase
git push origin main

# ============================================================================
# Submission logs
# ============================================================================
# Run the same log command from each repo and save the output
git -C "$BASE/$ROLLNO"          log --oneline --graph --all --decorate > "$Q1_DIR/my-log.txt"
git -C "$BASE/${ROLLNO}-friend" log --oneline --graph --all --decorate > "$Q1_DIR/friend-log.txt"
