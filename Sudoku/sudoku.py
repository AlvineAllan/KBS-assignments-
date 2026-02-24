from collections import deque, defaultdict
import time
import tkinter as tk
from tkinter import messagebox

class Sudoku:
    def __init__(self, grid):
        """
        Initialize Sudoku CSP problem.
        Variables: Each cell (i,j) is a variable
        Domains: {1..9} for empty cells, single value for filled cells
        Constraints: All different for rows, columns, and boxes
        """
        self.n = 3  # Standard 9x9 Sudoku
        self.size = 9
        self.grid = grid
        
      
        self.domains = {}
        for i in range(self.size):
            for j in range(self.size):
                if grid[i][j] != 0:
                    self.domains[(i, j)] = {grid[i][j]}
                else:
                    self.domains[(i, j)] = set(range(1, 10))
        
        self.peers = self._build_peers()
        
        # Statistics tracking
        self.nodes_explored = 0
        self.backtracks = 0
        self.start_time = None
        self.end_time = None
        
        # Validate initial grid
        if not self._validate_initial_grid():
            raise ValueError("Invalid initial grid: duplicate values in a row, column, or box.")
        
       
        self._ac3()

    def _build_peers(self):
        """Build peer relationships for all cells."""
        peers = {}
        for i in range(self.size):
            for j in range(self.size):
                cell_peers = set()
                
                # Add all cells in same row
                for k in range(self.size):
                    if k != j:
                        cell_peers.add((i, k))
                
                # Add all cells in same column
                for k in range(self.size):
                    if k != i:
                        cell_peers.add((k, j))
                
                # Add all cells in same 3x3 box
                box_row, box_col = 3 * (i // 3), 3 * (j // 3)
                for di in range(3):
                    for dj in range(3):
                        r, c = box_row + di, box_col + dj
                        if (r, c) != (i, j):
                            cell_peers.add((r, c))
                
                peers[(i, j)] = cell_peers
        return peers

    def _validate_initial_grid(self):
        """Check for duplicate values in rows, columns, and boxes."""
        # Check rows
        for i in range(self.size):
            row_vals = [self.grid[i][j] for j in range(self.size) if self.grid[i][j] != 0]
            if len(row_vals) != len(set(row_vals)):
                return False
        
        # Check columns
        for j in range(self.size):
            col_vals = [self.grid[i][j] for i in range(self.size) if self.grid[i][j] != 0]
            if len(col_vals) != len(set(col_vals)):
                return False
        
        # Check boxes
        for box_row in range(0, self.size, 3):
            for box_col in range(0, self.size, 3):
                box_vals = []
                for i in range(3):
                    for j in range(3):
                        val = self.grid[box_row + i][box_col + j]
                        if val != 0:
                            box_vals.append(val)
                if len(box_vals) != len(set(box_vals)):
                    return False
        
        return True

    def _ac3(self):
        """
        AC-3 constraint propagation algorithm.
        Ensures arc consistency for all constraints.
        """
        # Initialize queue with all arcs (xi, xj)
        queue = deque()
        for xi in self.domains:
            for xj in self.peers[xi]:
                queue.append((xi, xj))
        
        while queue:
            xi, xj = queue.popleft()
            if self._revise(xi, xj):
                # If domain becomes empty, inconsistency detected
                if not self.domains[xi]:
                    return False
                
                # Add all arcs (xk, xi) back to queue where xk != xj
                for xk in self.peers[xi]:
                    if xk != xj:
                        queue.append((xk, xi))
        
        return True

    def _revise(self, xi, xj):
        """
        Remove values from domain[xi] that have no support in domain[xj].
        Returns True if domain was revised.
        """
        revised = False
        to_remove = set()
        
        for x in self.domains[xi]:
           
            has_support = False
            for y in self.domains[xj]:
                if x != y:  # Binary constraint: different values
                    has_support = True
                    break
            
            if not has_support:
                to_remove.add(x)
        
        if to_remove:
            self.domains[xi] -= to_remove
            revised = True
        
        return revised

    def select_unassigned_variable(self):
        """
        MRV (Minimum Remaining Values) heuristic.
        Select the unassigned variable with the smallest domain.
        """
        unassigned = [v for v in self.domains if len(self.domains[v]) > 1]
        if not unassigned:
            return None
        return min(unassigned, key=lambda v: len(self.domains[v]))

    def order_domain_values(self, var):
        """
        LCV (Least Constraining Value) heuristic.
        Order values by how few constraints they remove from peers.
        """
        def count_constraints(value):
            """Count how many peers would lose this value from their domain."""
            count = 0
            for peer in self.peers[var]:
                if value in self.domains[peer]:
                    count += 1
            return count
        
        return sorted(self.domains[var], key=count_constraints)

    def forward_check(self, var, value):
        """
        Forward checking: remove value from peers' domains.
        Returns (inferences, is_consistent) where inferences are domain changes made.
        """
        inferences = {}
        
        for peer in self.peers[var]:
            if value in self.domains[peer]:
                # Store original domain for backtracking
                if peer not in inferences:
                    inferences[peer] = self.domains[peer].copy()
                self.domains[peer].discard(value)
                
                
                if not self.domains[peer]:
                    return inferences, False
        
        return inferences, True

    def restore_domains(self, inferences):
        """Restore domains after backtracking."""
        for var, domain in inferences.items():
            self.domains[var] = domain

    def is_complete(self):
        """Check if all variables are assigned (domains size 1)."""
        return all(len(self.domains[v]) == 1 for v in self.domains)

    def backtrack(self):
        """
        Backtracking search algorithm with forward checking.
        Returns True if solution found, False otherwise.
        """
        self.nodes_explored += 1
        
        # Check if puzzle is solved
        if self.is_complete():
            return True
        
        # Select unassigned variable using MRV
        var = self.select_unassigned_variable()
        if var is None:
            return True
        
        # Try values in LCV order
        for value in self.order_domain_values(var):
            # Save current state
            old_value = self.domains[var].copy()
            self.domains[var] = {value}
            
            # Forward checking
            inferences, consistent = self.forward_check(var, value)
            
            if consistent:
                # Recursively search
                result = self.backtrack()
                if result:
                    return True
            
            # Backtrack: restore domains
            self.backtracks += 1
            self.domains[var] = old_value
            self.restore_domains(inferences)
        
        return False

    def solve(self):
        """Solve the Sudoku puzzle and return solution with statistics."""
        self.start_time = time.time()
        self.nodes_explored = 0
        self.backtracks = 0
        
        solution_found = self.backtrack()
        
        self.end_time = time.time()
        
        if solution_found:
            return self.get_grid(), {
                'nodes': self.nodes_explored,
                'backtracks': self.backtracks,
                'time': self.end_time - self.start_time
            }
        else:
            return None, None

    def solve_with_steps(self):
        """
        Generator version that yields each assignment step for visualization.
        Yields: ('assign', var, value, current_grid) for each assignment
                ('solution', final_grid) when solved
        """
        if self.is_complete():
            yield ('solution', self.get_grid())
            return
        
        var = self.select_unassigned_variable()
        if var is None:
            yield ('solution', self.get_grid())
            return
        
        for value in self.order_domain_values(var):
            # Save current state
            old_value = self.domains[var].copy()
            self.domains[var] = {value}
            
            # Forward checking
            inferences, consistent = self.forward_check(var, value)
            
            if consistent:
                # Yield current assignment for visualization
                yield ('assign', var, value, self.get_grid())
                
                # Recursively solve
                result = yield from self.solve_with_steps()
                if result:
                    return
            
            # Backtrack: restore domains
            self.domains[var] = old_value
            self.restore_domains(inferences)
        
        return False

    def get_grid(self):
        """Convert current domains to grid format."""
        grid = []
        for i in range(self.size):
            row = []
            for j in range(self.size):
                domain = self.domains[(i, j)]
                if len(domain) == 1:
                    row.append(next(iter(domain)))
                else:
                    row.append(0)
            grid.append(row)
        return grid

    def print_solution_stats(self):
        """Print solving statistics."""
        if self.end_time and self.start_time:
            print(f"\n=== Solving Statistics ===")
            print(f"Nodes explored: {self.nodes_explored}")
            print(f"Backtracks: {self.backtracks}")
            print(f"Time taken: {self.end_time - self.start_time:.3f} seconds")
            print(f"Constraint propagation: AC-3 + Forward Checking")
            print(f"Heuristics: MRV + LCV")


class SudokuGUI:
    def __init__(self, initial_grid):
        self.initial_grid = initial_grid
        self.sudoku = Sudoku([row[:] for row in initial_grid])
        self.size = 9
        self.n = 3
        
        # Setup GUI
        self.root = tk.Tk()
        self.root.title("Sudoku CSP Solver")
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI components."""
        # Colors for 3x3 boxes
        self.colors = ["#e6f7ff", "#fffbe6"]
        
        # Main frame
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack()
        
        # Title
        title = tk.Label(main_frame, text="Sudoku Solver - CSP with AC-3 + Forward Checking", 
                        font=("Arial", 14, "bold"))
        title.grid(row=0, column=0, columnspan=9, pady=(0, 10))
        
        # Grid frame
        grid_frame = tk.Frame(main_frame)
        grid_frame.grid(row=1, column=0, columnspan=9)
        
        # Create labels for each cell
        self.labels = [[None for _ in range(self.size)] for _ in range(self.size)]
        self.fixed = [[self.initial_grid[i][j] != 0 for j in range(self.size)] for i in range(self.size)]
        
        for i in range(self.size):
            for j in range(self.size):
                # Determine cell color based on box
                bg_color = self.colors[((i // self.n) + (j // self.n)) % 2]
                
                # Text color: dark blue for fixed, gray for empty
                fg_color = "#1a237e" if self.fixed[i][j] else "#616161"
                
                # Create label
                label = tk.Label(
                    grid_frame,
                    text=str(self.initial_grid[i][j]) if self.initial_grid[i][j] != 0 else "",
                    width=3,
                    height=1,
                    font=("Arial", 16, "bold"),
                    borderwidth=2,
                    relief="solid",
                    bg=bg_color,
                    fg=fg_color
                )
                label.grid(row=i, column=j, padx=1, pady=1, sticky="nsew")
                self.labels[i][j] = label
                
                # Make cells expandable
                grid_frame.grid_rowconfigure(i, weight=1)
                grid_frame.grid_columnconfigure(j, weight=1)
        
        # Statistics frame
        stats_frame = tk.Frame(main_frame, pady=10)
        stats_frame.grid(row=2, column=0, columnspan=9)
        
        self.stats_text = tk.Text(stats_frame, height=4, width=50, font=("Arial", 10))
        self.stats_text.pack()
        
        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=9, pady=10)
        
        solve_btn = tk.Button(button_frame, text="Solve Step by Step", 
                             command=self.solve_step_by_step,
                             bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                             padx=10, pady=5)
        solve_btn.pack(side=tk.LEFT, padx=5)
        
        solve_fast_btn = tk.Button(button_frame, text="Solve Fast (No Visualization)", 
                                  command=self.solve_fast,
                                  bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                  padx=10, pady=5)
        solve_fast_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = tk.Button(button_frame, text="Reset", 
                             command=self.reset,
                             bg="#f44336", fg="white", font=("Arial", 10, "bold"),
                             padx=10, pady=5)
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Delay between steps (ms)
        self.delay = 50
        
    def update_grid(self, grid, highlight=None, highlight_color="#81c784"):
        """Update the GUI grid display."""
        for i in range(self.size):
            for j in range(self.size):
                val = grid[i][j]
                
                # Fixed cells show initial values
                if self.fixed[i][j]:
                    self.labels[i][j]['text'] = str(self.initial_grid[i][j])
                    self.labels[i][j]['fg'] = "#1a237e"
                else:
                    self.labels[i][j]['text'] = str(val) if val != 0 else ""
                    self.labels[i][j]['fg'] = "#388e3c" if val != 0 else "#616161"
                
                # Set background color
                if highlight and (i, j) == highlight and not self.fixed[i][j]:
                    self.labels[i][j]['bg'] = highlight_color
                else:
                    self.labels[i][j]['bg'] = self.colors[((i // self.n) + (j // self.n)) % 2]
        
        self.root.update()
    
    def update_stats(self, stats):
        """Update statistics display."""
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, 
            f"Nodes Explored: {stats['nodes']}\n"
            f"Backtracks: {stats['backtracks']}\n"
            f"Time: {stats['time']:.3f} seconds\n"
            f"Method: AC-3 + Forward Checking with MRV & LCV"
        )
    
    def solve_step_by_step(self):
        """Solve the puzzle step by step with visualization."""
        # Reset solver
        self.sudoku = Sudoku([row[:] for row in self.initial_grid])
        self.steps = self.sudoku.solve_with_steps()
        self.step_through()
    
    def step_through(self):
        """Process one step of the solution."""
        try:
            step = next(self.steps)
            
            if step[0] == 'assign':
                _, var, value, grid = step
                i, j = var
                if not self.fixed[i][j]:
                    self.update_grid(grid, highlight=(i, j), highlight_color="#81c784")
                else:
                    self.update_grid(grid)
                self.root.after(self.delay, self.step_through)
                
            elif step[0] == 'solution':
                _, grid = step
                self.update_grid(grid)
                
                # Get final statistics
                stats = {
                    'nodes': self.sudoku.nodes_explored,
                    'backtracks': self.sudoku.backtracks,
                    'time': 0  # Not tracking time for step-by-step
                }
                self.update_stats(stats)
                
                messagebox.showinfo("Sudoku Solver", 
                    f"Puzzle Solved!\n\n"
                    f"Nodes explored: {stats['nodes']}\n"
                    f"Backtracks: {stats['backtracks']}")
                
        except StopIteration:
            messagebox.showinfo("Sudoku Solver", "No solution found.")
    
    def solve_fast(self):
        """Solve the puzzle without visualization and show statistics."""
        # Reset solver
        self.sudoku = Sudoku([row[:] for row in self.initial_grid])
        
        # Solve and get statistics
        solution, stats = self.sudoku.solve()
        
        if solution:
            self.update_grid(solution)
            self.update_stats(stats)
            messagebox.showinfo("Sudoku Solver", 
                f"Puzzle Solved!\n\n"
                f"Nodes explored: {stats['nodes']}\n"
                f"Backtracks: {stats['backtracks']}\n"
                f"Time: {stats['time']:.3f} seconds")
        else:
            messagebox.showerror("Sudoku Solver", "No solution exists!")
    
    def reset(self):
        """Reset the grid to initial state."""
        self.sudoku = Sudoku([row[:] for row in self.initial_grid])
        self.update_grid(self.initial_grid)
        self.stats_text.delete(1.0, tk.END)
    
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    # Example puzzle (hard)
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
        # Test solver without GUI first
        print("Testing Sudoku CSP Solver...")
        test_sudoku = Sudoku([row[:] for row in grid])
        solution, stats = test_sudoku.solve()
        
        if solution:
            print("\nInitial Puzzle:")
            for row in grid:
                print(row)
            print("\nSolution:")
            for row in solution:
                print(row)
            test_sudoku.print_solution_stats()
        else:
            print("No solution found!")
        
        # Launch GUI
        print("\nLaunching GUI...")
        app = SudokuGUI(grid)
        app.run()
        
    except ValueError as e:
        print(f"Error: {e}")
        messagebox.showerror("Sudoku Error", str(e))


if __name__ == "__main__":
    main()