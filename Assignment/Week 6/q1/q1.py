"""Question 1 - The Wizard's Chess Solver.

Solves the 3x3 Wizard's Chess variant with minimax / backward induction and
writes the optimal policies for both houses to policy_gryffindor.json and
policy_slytherin.json.

Gryffindor ('G') moves first and maximises; Slytherin ('S') minimises.
Utility is +1 for a Gryffindor win, -1 for a Slytherin win, 0 for a draw.
"""

import json
import math
import os

WINNING_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

EMPTY = "0"
GRYFFINDOR = "G"
SLYTHERIN = "S"

policy_gryffindor = {}
policy_slytherin = {}


class ChessState:
    def __init__(self, history=None):
        self.history = list(history) if history else []
        self.grid = [EMPTY] * 9
        for turn, square in enumerate(self.history):
            self.grid[square] = GRYFFINDOR if turn % 2 == 0 else SLYTHERIN
        self.actor = GRYFFINDOR if len(self.history) % 2 == 0 else SLYTHERIN

    def get_valid_moves(self):
        return [i for i, val in enumerate(self.grid) if val == EMPTY]

    def is_checkmate(self):
        for a, b, c in WINNING_LINES:
            if self.grid[a] != EMPTY and self.grid[a] == self.grid[b] == self.grid[c]:
                return True
        return False

    def is_terminal(self):
        return self.is_checkmate() or len(self.history) == 9

    def get_utility(self):
        if self.is_checkmate():
            last_mover_was_gryffindor = (len(self.history) - 1) % 2 == 0
            return 1.0 if last_mover_was_gryffindor else -1.0
        return 0.0

    def history_key(self):
        return "".join(str(square) for square in self.history)


def backward_induction(state):
    if state.is_terminal():
        return state.get_utility()

    maximizing = state.actor == GRYFFINDOR
    best_val = -math.inf if maximizing else math.inf
    move_values = {}

    for move in state.get_valid_moves():
        value = backward_induction(ChessState(state.history + [move]))
        move_values[move] = value
        best_val = max(best_val, value) if maximizing else min(best_val, value)

    chosen_move = min(m for m, v in move_values.items() if v == best_val)
    strategy = {str(i): (1.0 if i == chosen_move else 0.0) for i in sorted(move_values)}

    target = policy_gryffindor if maximizing else policy_slytherin
    target[state.history_key()] = strategy

    return best_val


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backward_induction(ChessState())

    for name, policy in (
        ("policy_gryffindor.json", policy_gryffindor),
        ("policy_slytherin.json", policy_slytherin),
    ):
        path = os.path.join(base_dir, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(policy, handle, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
