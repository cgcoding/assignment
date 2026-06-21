"""Question 2 - The Marauder's Simulation Engine.

Command-line interface where a human plays Slytherin against the optimal
Gryffindor bot. The bot loads policy_gryffindor.json (from Question 1), moves
first, and plays the policy's move for the current history. Unknown histories
fall back to a random valid move.
"""

import json
import os
import random

EMPTY = "-"
GRYFFINDOR = "G"
SLYTHERIN = "S"
BOARD_SIZE = 9

WINNING_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)


class PolicyNotFoundError(Exception):
    pass


class GameEngine:
    def __init__(self, policy_path):
        try:
            with open(policy_path, "r", encoding="utf-8") as handle:
                self.policy = json.load(handle)
        except FileNotFoundError as exc:
            raise PolicyNotFoundError(
                f"Policy JSON not found at '{policy_path}'. Run Q1 first."
            ) from exc
        except json.JSONDecodeError as exc:
            raise PolicyNotFoundError(
                f"Policy JSON at '{policy_path}' is malformed: {exc}"
            ) from exc

        self.history = []
        self.grid = [EMPTY] * BOARD_SIZE

    def history_key(self):
        return "".join(str(square) for square in self.history)

    def valid_moves(self):
        return [i for i, cell in enumerate(self.grid) if cell == EMPTY]

    def winner(self):
        for a, b, c in WINNING_LINES:
            if self.grid[a] != EMPTY and self.grid[a] == self.grid[b] == self.grid[c]:
                return self.grid[a]
        return None

    def display(self):
        for row in range(0, BOARD_SIZE, 3):
            print(" " + " | ".join(self.grid[row:row + 3]))
            if row < 6:
                print("-----------")
        print()

    def bot_move(self):
        try:
            strategy = self.policy[self.history_key()]
            move = int(max(strategy, key=strategy.get))
            if self.grid[move] != EMPTY:
                raise KeyError(self.history_key())
            return move
        except KeyError:
            return random.choice(self.valid_moves())

    def read_human_move(self):
        while True:
            raw = input("Enter your move (0-8): ").strip()
            if not raw.lstrip("-").isdigit():
                print("Please enter an integer between 0 and 8.")
                continue
            move = int(raw)
            if move < 0 or move >= BOARD_SIZE:
                print("Out of range. Choose a square from 0 to 8.")
                continue
            if self.grid[move] != EMPTY:
                print("That square is already claimed. Try again.")
                continue
            return move

    def play_match(self):
        print("You are Slytherin (S). Gryffindor (G) moves first.\n")
        self.display()

        while len(self.history) < BOARD_SIZE:
            if len(self.history) % 2 == 0:
                move = self.bot_move()
                self.grid[move] = GRYFFINDOR
                self.history.append(move)
                print(f"Gryffindor claims square {move}.")
            else:
                move = self.read_human_move()
                self.grid[move] = SLYTHERIN
                self.history.append(move)
                print(f"You claim square {move}.")

            self.display()

            champion = self.winner()
            if champion:
                house = "Gryffindor" if champion == GRYFFINDOR else "Slytherin (you)"
                print(f"Checkmate! {house} wins.")
                return

        print("Stalemate - the board is full with no checkmate.")


def resolve_policy_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local = os.path.join(base_dir, "policy_gryffindor.json")
    if os.path.exists(local):
        return local
    return os.path.join(base_dir, "..", "q1", "policy_gryffindor.json")


def main():
    engine = GameEngine(resolve_policy_path())
    engine.play_match()


if __name__ == "__main__":
    main()
