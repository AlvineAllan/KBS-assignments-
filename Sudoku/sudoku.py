
from collections import deque, defaultdict

class Sudoku:
    def __init__(self, grid):
        self.n = int(len(grid) ** 0.5) if len(grid) == len(grid[0]) else 3  # Generalize for n^2 x n^2
        self.size = self.n * self.n
        self.grid = grid
        self.domains = {(i, j): {grid[i][j]} if grid[i][j] else set(range(1, self.size + 1)) for i in range(self.size) for j in range(self.size)}
        self.peers = self._build_peers()
        if not self._validate_initial_grid():
            raise ValueError("Invalid initial grid: duplicate values in a row, column, or box.")
        self._ac3()

    def _build_peers(self):
        peers = {}
        for i in range(self.size):
            for j in range(self.size):
                p = set()
                for k in range(self.size):
                    p.add((i, k))
                    p.add((k, j))
                bi, bj = self.n * (i // self.n), self.n * (j // self.n)
                for di in range(self.n):
                    for dj in range(self.n):
                        p.add((bi + di, bj + dj))
                p.remove((i, j))
                peers[(i, j)] = p
        return peers

    def _validate_initial_grid(self):
        # Check for duplicates in rows, columns, and boxes
        for i in range(self.size):
            row = [self.grid[i][j] for j in range(self.size) if self.grid[i][j]]
            if len(row) != len(set(row)):
                return False
            col = [self.grid[j][i] for j in range(self.size) if self.grid[j][i]]
            if len(col) != len(set(col)):
                return False
        for bi in range(0, self.size, self.n):
            for bj in range(0, self.size, self.n):
                block = [self.grid[bi+di][bj+dj] for di in range(self.n) for dj in range(self.n) if self.grid[bi+di][bj+dj]]
                if len(block) != len(set(block)):
                    return False
        return True

    def _ac3(self):
        # AC-3 constraint propagation
        queue = deque([(xi, xj) for xi in self.domains for xj in self.peers[xi]])
        while queue:
            xi, xj = queue.popleft()
            if self._revise(xi, xj):
                if not self.domains[xi]:
                    return False
                for xk in self.peers[xi] - {xj}:
                    queue.append((xk, xi))
        return True

    def _revise(self, xi, xj):
        revised = False
        to_remove = set()
        for x in self.domains[xi]:
            if all(x == y for y in self.domains[xj]):
                to_remove.add(x)
        if to_remove:
            self.domains[xi] -= to_remove
            revised = True
        return revised

    def assign(self, var, val):
        old_domains = {p: self.domains[p].copy() for p in self.peers[var]}
        self.domains[var] = {val}
        for p in self.peers[var]:
            self.domains[p].discard(val)
            if not self.domains[p]:
                return old_domains, False
        return old_domains, True

    def unassign(self, var, old_domains):
        for p, dom in old_domains.items():
            self.domains[p] = dom

    def _lcv(self, var):
        # Least Constraining Value heuristic
        counts = {}
        for val in self.domains[var]:
            count = 0
            for peer in self.peers[var]:
                if val in self.domains[peer]:
                    count += 1
            counts[val] = count
        return sorted(self.domains[var], key=lambda v: counts[v])

    def solve(self):
        if all(len(d) == 1 for d in self.domains.values()):
            return True
        # MRV heuristic
        var = min((v for v in self.domains if len(self.domains[v]) > 1), key=lambda v: len(self.domains[v]))
        for val in self._lcv(var):
            old, ok = self.assign(var, val)
            if ok and self._ac3() and self.solve():
                return True
            self.unassign(var, old)
        return False

    def get_grid(self):
        return [[list(self.domains[(i, j)])[0] for j in range(self.size)] for i in range(self.size)]

if __name__ == "__main__":
    # Example grid (book-style hard puzzle)
    grid = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]
    try:
        sudoku = Sudoku(grid)
        if sudoku.solve():
            solved = sudoku.get_grid()
            for row in solved:
                print(' '.join(map(str, row)))
        else:
            print("Unsolvable")
    except ValueError as e:
        print(e)