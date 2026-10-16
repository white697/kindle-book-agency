"""Programmatic puzzle generators: word search, sudoku, maze. Seeded for reproducibility."""

import random
import re

DIRS_EASY = [(0, 1), (1, 0)]
DIRS_MED = DIRS_EASY + [(1, 1)]
DIRS_HARD = DIRS_MED + [(0, -1), (-1, 0), (-1, -1), (1, -1), (-1, 1)]


# ── Word search ───────────────────────────────────────────────────────────

def make_wordsearch(words: list[str], size: int = 15, difficulty: str = "medium",
                    rng: random.Random | None = None) -> dict:
    rng = rng or random.Random()
    dirs = {"easy": DIRS_EASY, "medium": DIRS_MED, "hard": DIRS_HARD}[difficulty]
    clean = []
    skipped = []
    for w in words:
        k = re.sub(r"[^A-Z]", "", w.upper())
        (clean if 2 <= len(k) <= size else skipped).append(k or w)
    clean = sorted(set(clean), key=len, reverse=True)
    grid = [[""] * size for _ in range(size)]
    placed = []
    for w in clean:
        for _ in range(300):
            dr, dc = rng.choice(dirs)
            r, c = rng.randrange(size), rng.randrange(size)
            er, ec = r + dr * (len(w) - 1), c + dc * (len(w) - 1)
            if not (0 <= er < size and 0 <= ec < size):
                continue
            cells = [(r + dr * i, c + dc * i) for i in range(len(w))]
            if all(grid[y][x] in ("", w[i]) for i, (y, x) in enumerate(cells)):
                for i, (y, x) in enumerate(cells):
                    grid[y][x] = w[i]
                placed.append({"word": w, "cells": cells})
                break
        else:
            skipped.append(w)
    for y in range(size):
        for x in range(size):
            if not grid[y][x]:
                grid[y][x] = rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return {"grid": grid, "placed": placed, "skipped": skipped, "size": size}


# ── Sudoku ────────────────────────────────────────────────────────────────

CLUES = {"easy": 38, "medium": 32, "hard": 27, "expert": 24}


def _candidates(g, r, c):
    used = set(g[r]) | {g[i][c] for i in range(9)}
    br, bc = r // 3 * 3, c // 3 * 3
    used |= {g[i][j] for i in range(br, br + 3) for j in range(bc, bc + 3)}
    return [v for v in range(1, 10) if v not in used]


def _solve(g, rng=None, limit=1) -> int:
    """Backtracking with MRV; returns number of solutions found (up to limit). Fills g if limit==1."""
    best, best_c = None, None
    for r in range(9):
        for c in range(9):
            if g[r][c] == 0:
                cand = _candidates(g, r, c)
                if best is None or len(cand) < len(best_c):
                    best, best_c = (r, c), cand
                    if len(cand) <= 1:
                        break
        if best_c is not None and len(best_c) <= 1:
            break
    if best is None:
        return 1
    if not best_c:
        return 0
    if rng:
        rng.shuffle(best_c)
    r, c = best
    count = 0
    for v in best_c:
        g[r][c] = v
        count += _solve(g, rng, limit - count)
        if count >= limit:
            return count  # leave g filled (callers needing the grid pass limit=1)
        g[r][c] = 0
    return count


def _count_solutions(g) -> int:
    work = [row[:] for row in g]
    # Count up to 2 on a copy; _solve resets cells it backtracks over.
    return _count(work, 2)


def _count(g, limit) -> int:
    cells = [(r, c) for r in range(9) for c in range(9) if g[r][c] == 0]
    if not cells:
        return 1
    best, best_c = None, None
    for r, c in cells:
        cand = _candidates(g, r, c)
        if best is None or len(cand) < len(best_c):
            best, best_c = (r, c), cand
            if len(cand) <= 1:
                break
    if not best_c:
        return 0
    r, c = best
    total = 0
    for v in best_c:
        g[r][c] = v
        total += _count(g, limit - total)
        g[r][c] = 0
        if total >= limit:
            break
    return total


def make_sudoku(difficulty: str = "medium", rng: random.Random | None = None) -> dict:
    rng = rng or random.Random()
    solution = [[0] * 9 for _ in range(9)]
    _solve(solution, rng)
    puzzle = [row[:] for row in solution]
    target = CLUES[difficulty]
    cells = [(r, c) for r in range(9) for c in range(9)]
    rng.shuffle(cells)
    clues = 81
    for r, c in cells:
        if clues <= target:
            break
        keep = puzzle[r][c]
        puzzle[r][c] = 0
        if _count_solutions(puzzle) != 1:
            puzzle[r][c] = keep
        else:
            clues -= 1
    return {"puzzle": puzzle, "solution": solution, "clues": clues}


# ── Maze ──────────────────────────────────────────────────────────────────

def make_maze(cols: int = 20, rows: int = 28, rng: random.Random | None = None) -> dict:
    """Perfect maze. walls[(r,c)] = set of open neighbours; start top-left, exit bottom-right."""
    rng = rng or random.Random()
    open_ = {(r, c): set() for r in range(rows) for c in range(cols)}
    stack, seen = [(0, 0)], {(0, 0)}
    while stack:
        r, c = stack[-1]
        nbrs = [(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if (r + dr, c + dc) in open_ and (r + dr, c + dc) not in seen]
        if not nbrs:
            stack.pop()
            continue
        n = rng.choice(nbrs)
        open_[(r, c)].add(n)
        open_[n].add((r, c))
        seen.add(n)
        stack.append(n)
    # unique path via DFS
    goal, parent, st = (rows - 1, cols - 1), {(0, 0): None}, [(0, 0)]
    while st:
        cur = st.pop()
        if cur == goal:
            break
        for n in open_[cur]:
            if n not in parent:
                parent[n] = cur
                st.append(n)
    path, cur = [], goal
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return {"open": open_, "cols": cols, "rows": rows, "path": path[::-1]}
