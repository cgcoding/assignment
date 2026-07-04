"""Question 4 - The Parseltongue Log Translator.

Translate each log word into a valid English word using the fewest one-way
translation steps. Ties are broken by the lexicographically smallest English
word; unreachable words become [ERROR].

Translations U -> V form a directed graph. A multi-source BFS over the reversed
graph (starting from the English words) gives each word's distance to English.
Sweeping nodes by increasing distance then fixes the lexicographic tie-break.

Input (stdin):
    Line 1: E, D, W
    Line 2: E English words
    Next D lines: "U V"
    Final line: W log words
Output: W translated words.
"""

import sys
from collections import defaultdict, deque

ERROR_TOKEN = "[ERROR]"


def translate(english_words, edges, log):
    forward_adj = defaultdict(list)
    reverse_adj = defaultdict(list)
    for u, v in edges:
        forward_adj[u].append(v)
        reverse_adj[v].append(u)

    dist = {}
    queue = deque()
    for word in english_words:
        dist[word] = 0
        queue.append(word)
    while queue:
        current = queue.popleft()
        for predecessor in reverse_adj[current]:
            if predecessor not in dist:
                dist[predecessor] = dist[current] + 1
                queue.append(predecessor)

    layers = defaultdict(list)
    for word, d in dist.items():
        layers[d].append(word)

    best_eng = {}
    for d in sorted(layers):
        for word in layers[d]:
            if d == 0:
                best_eng[word] = word
                continue
            candidate = None
            for nxt in forward_adj[word]:
                if dist.get(nxt) == d - 1:
                    target = best_eng[nxt]
                    if candidate is None or target < candidate:
                        candidate = target
            best_eng[word] = candidate

    return [best_eng.get(word, ERROR_TOKEN) for word in log]


def main():
    data = sys.stdin.read().split()
    if not data:
        return
    idx = 0
    e = int(data[idx]); d = int(data[idx + 1]); w = int(data[idx + 2])
    idx += 3

    english_words = set(data[idx:idx + e])
    idx += e

    edges = []
    for _ in range(d):
        edges.append((data[idx], data[idx + 1]))
        idx += 2

    log = data[idx:idx + w]

    print(" ".join(translate(english_words, edges, log)))


if __name__ == "__main__":
    main()
