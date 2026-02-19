# Implementing the Cheetah–Goat–Grass Riddle Using BFS and DFS
The Cheetah–Goat–Grass riddle is a classic river-crossing puzzle, similar to the Missionaries and Cannibals problem discussed in Artificial Intelligence: A Modern Approach (Exercise 3.9, page 134). In this puzzle, a farmer must transport a cheetah, a goat, and grass across a river using a boat that can carry only the farmer and one other item at a time.

The problem is subject to the following constraints: the cheetah cannot be left alone with the goat in the absence of the farmer, and the goat cannot be left alone with the grass in the absence of the farmer.

This project models the riddle as a state-space search problem and applies uninformed search strategies, specifically Breadth-First Search (BFS) and Depth-First Search (DFS), to systematically explore valid states and find solution paths from the initial state to the goal state.

### Problem Formulation
State Representation

Each state is represented as a tuple (farmer, cheetah, goat, grass), where each element takes the value 0 (left bank) or 1 (right bank). 
   - The initial state is (0, 0, 0, 0), representing all entities on the left bank.
   - The goal state is (1, 1, 1, 1), representing all entities on the right bank.

A state is considered valid if it satisfies the problem constraints. Specifically, when the farmer is not present on a bank, the cheetah must not be left alone with the goat, and the goat must not be left alone with the grass.

### Actions

The farmer may cross the river either alone or accompanied by one item (cheetah, goat, or grass). Each action changes the position of the farmer and, if applicable, the accompanying item.
Only actions that result in valid states are permitted.

### Search Strategy

Breadth-First Search (BFS):
BFS explores the state space level by level and guarantees finding the shortest solution path in terms of the number of moves. Since all actions have equal cost, BFS is both complete and optimal for this problem (Artificial Intelligence: A Modern Approach, pp. 82–84).

Depth-First Search (DFS):
DFS explores as deeply as possible along each branch before backtracking. While DFS is not guaranteed to find the shortest solution, it uses less memory compared to BFS. A depth limit is applied to prevent infinite exploration of cyclic states (pp. 84–86).

## Quick Start

### Prerequisites
- Python 3.8 or higher

### Installation
If the project includes external dependencies, install them using:
```bash
pip install -r requirements.txt
### Running the Solver
```bash
# Breadth-First Search
python main.py --method bfs

# Depth-First Search
python main.py --method dfs