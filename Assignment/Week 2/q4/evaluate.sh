#!/bin/bash

# Usage check — this script takes no arguments
if [ "$#" -ne 0 ]; then
    echo "Usage: evaluate.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MOCK_DIR="$SCRIPT_DIR/mock_grading"
INPUTS_DIR="$MOCK_DIR/inputs"
OUTPUTS_DIR="$MOCK_DIR/outputs"
ORGANISED_DIR="$SCRIPT_DIR/organised"
ROLL_LIST="$MOCK_DIR/roll_list"

# macOS usually does not ship GNU timeout; prefer timeout, then gtimeout.
TIMEOUT_BIN=""
if command -v timeout >/dev/null 2>&1; then
    TIMEOUT_BIN="timeout"
elif command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_BIN="gtimeout"
fi

# Collect sorted list of .in files into an array
INPUT_FILES=()
while IFS= read -r input_file; do
    INPUT_FILES+=("$input_file")
done < <(find "$INPUTS_DIR" -maxdepth 1 -type f -name "*.in" | sort)
NUM_INPUTS=${#INPUT_FILES[@]}

# distribution[i] = number of students who got input i correct
declare -a distribution
for ((i = 0; i < NUM_INPUTS; i++)); do
    distribution[$i]=0
done

# Initialise output files (clear any previous run)
> "$SCRIPT_DIR/marksheet.csv"
> "$SCRIPT_DIR/distribution.txt"

# ── Process each student ──────────────────────────────────────────────────────
while IFS= read -r roll; do
    [ -z "$roll" ] && continue

    STUDENT_DIR="$ORGANISED_DIR/$roll"
    score=0

    # Create the directory that will hold this student's generated outputs
    mkdir -p "$STUDENT_DIR/student_outputs"

    # Compile the student's .cpp file (if one exists) into an executable named
    # "executable", running g++ from within the student's directory.
    # Compilation errors are suppressed (2>/dev/null).
    CPP_FILE=$(ls "$STUDENT_DIR"/*.cpp 2>/dev/null | head -1)
    if [ -n "$CPP_FILE" ]; then
        CPP_BASENAME=$(basename "$CPP_FILE")
        (cd "$STUDENT_DIR" && g++ -o executable "$CPP_BASENAME" 2>/dev/null)
    fi

    # ── Run against every test input ─────────────────────────────────────────
    for ((i = 0; i < NUM_INPUTS; i++)); do
        INPUT_FILE="${INPUT_FILES[$i]}"
        INPUT_NAME=$(basename "$INPUT_FILE" .in)
        EXPECTED="$OUTPUTS_DIR/${INPUT_NAME}.out"
        STUDENT_OUT="$STUDENT_DIR/student_outputs/${INPUT_NAME}.out"

        # Run executable (or just create an empty output file if it doesn't exist).
        # The redirect '>' always creates/truncates the output file regardless of
        # whether the executable exists or crashes — that is why no explicit check
        # is needed.
        # 2>/dev/null  : suppress stderr (segfaults, missing-file errors, etc.)
        # | :           : pipe to the null command to suppress bash "Killed" messages
        #                 from timeout; stdout still goes to the file because '>'
        #                 takes precedence over '|' for the left-hand command.
        if [ -n "$TIMEOUT_BIN" ]; then
            (cd "$STUDENT_DIR" && \
                "$TIMEOUT_BIN" 5 ./executable < "$INPUT_FILE" \
                    > "student_outputs/${INPUT_NAME}.out" \
                    2>/dev/null | :)
        else
            # Fallback for macOS: enforce a 5s timeout via Perl alarm.
            (cd "$STUDENT_DIR" && \
                perl -e 'alarm shift @ARGV; exec @ARGV' 5 ./executable < "$INPUT_FILE" \
                    > "student_outputs/${INPUT_NAME}.out" \
                    2>/dev/null | :)
        fi

        # Compare generated output with expected output (exact match)
        if diff -q "$STUDENT_OUT" "$EXPECTED" > /dev/null 2>&1; then
            score=$((score + 1))
            distribution[$i]=$((distribution[$i] + 1))
        fi
    done

    # Append this student's result to marksheet.csv
    echo "$roll,$score" >> "$SCRIPT_DIR/marksheet.csv"

done < "$ROLL_LIST"

# Sort marksheet lexicographically by roll number (which is the first field)
sort "$SCRIPT_DIR/marksheet.csv" -o "$SCRIPT_DIR/marksheet.csv"

# Write distribution.txt — one line per test input: "<input_number>, <correct_count>"
for ((i = 0; i < NUM_INPUTS; i++)); do
    INPUT_NAME=$(basename "${INPUT_FILES[$i]}" .in)
    echo "$INPUT_NAME, ${distribution[$i]}" >> "$SCRIPT_DIR/distribution.txt"
done
