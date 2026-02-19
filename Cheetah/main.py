# ...existing code...
from collections import deque

# State: (farmer, cheetah, goat, grass) - 0 left, 1 right
initial_state = (0, 0, 0, 0)
goal_state = (1, 1, 1, 1)

# Check if state is safe
def is_safe(state):
    f, c, g, gr = state
    # For each bank, if the farmer is NOT there, ensure no forbidden pairs remain alone
    for bank in (0, 1):
        if f != bank:
            if c == g == bank:   # cheetah eats goat
                return False
            if g == gr == bank:  # goat eats grass
                return False
    return True

# Get possible moves from current state
def get_moves(state):
    f, c, g, gr = state
    moves = []
    # Farmer crosses alone
    new_state = (1 - f, c, g, gr)
    if is_safe(new_state):
        moves.append(new_state)
    # Farmer with cheetah
    if f == c:
        new_state = (1 - f, 1 - c, g, gr)
        if is_safe(new_state):
            moves.append(new_state)
    # Farmer with goat
    if f == g:
        new_state = (1 - f, c, 1 - g, gr)
        if is_safe(new_state):
            moves.append(new_state)
    # Farmer with grass
    if f == gr:
        new_state = (1 - f, c, g, 1 - gr)
        if is_safe(new_state):
            moves.append(new_state)
    return moves

# BFS to find shortest path
def bfs():
    queue = deque([(initial_state, [])])  # (state, path)
    visited = set([initial_state])
    while queue:
        state, path = queue.popleft()
        if state == goal_state:
            return path + [state]
        for next_state in get_moves(state):
            if next_state not in visited:
                visited.add(next_state)
                queue.append((next_state, path + [state]))
    return None

# DFS with depth limit
def dfs(state, path, visited, depth_limit):
    if len(path) > depth_limit:
        return None
    if state == goal_state:
        return path + [state]
    visited.add(state)
    for next_state in get_moves(state):
        if next_state not in visited:
            result = dfs(next_state, path + [state], visited, depth_limit)
            if result:
                return result
    visited.remove(state)
    return None

# Iterative deepening DFS
def iddfs():
    depth = 0
    while True:
        visited = set()
        result = dfs(initial_state, [], visited, depth)
        if result:
            return result
        depth += 1

def format_path(path):
    if not path:
        return "No solution"
    return " -> ".join(str(s) for s in path)

# run selected solver via CLI
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cheetah-Goat-Grass solvers")
    parser.add_argument(
        "--method",
        choices=("bfs", "dfs"),
        default="bfs",
        help="Select solver: 'bfs' (Breadth-First Search) or 'dfs' (iterative deepening DFS)"
    )
    args = parser.parse_args()

    if args.method == "bfs":
        solution = bfs()
        print("BFS Solution (states):", format_path(solution))
    else:
        # CLI 'dfs' maps to the existing iterative deepening DFS implementation
        solution = iddfs()
        print("DFS Solution (states):", format_path(solution))
