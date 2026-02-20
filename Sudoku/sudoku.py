# sudoku_csp.py
import tkinter as tk
from tkinter import ttk
import copy
import time
import random
from collections import deque

class SudokuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku - Constraint Satisfaction Problem (CSP) Solver")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Initial puzzle (easy)
        self.initial_board = [
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
        
        self.current_board = copy.deepcopy(self.initial_board)
        self.domains = {}  # Domain for each variable (cell)
        self.selected_cell = None
        self.solving = False
        self.stats = {
            'nodes': 0,
            'backtracks': 0,
            'arc_checks': 0,
            'prunes': 0,
            'time': 0
        }
        
        self.setup_ui()
        self.initialize_domains()
        self.draw_board()
    
    def setup_ui(self):
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=10)
        
        title_label = ttk.Label(title_frame, text="SUDOKU", 
                                font=('Arial', 24, 'bold'))
        title_label.pack()
        
        subtitle = ttk.Label(title_frame, 
                            text="Constraint Satisfaction Problem (CSP) - AI Demo",
                            font=('Arial', 12))
        subtitle.pack()
        
        # Main content area
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left side - Sudoku board and CSP concepts
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Sudoku board
        board_frame = ttk.LabelFrame(left_frame, text="Sudoku Puzzle", padding=10)
        board_frame.pack(pady=10)
        
        self.board_canvas = tk.Canvas(board_frame, width=450, height=450, bg='white', 
                                      highlightthickness=2, highlightbackground='#333')
        self.board_canvas.pack()
        self.board_canvas.bind('<Button-1>', self.on_cell_click)
        
        # CSP Concepts frame
        concepts_frame = ttk.LabelFrame(left_frame, text="CONSTRAINT SATISFACTION PROBLEM (CSP) CONCEPTS", 
                                        padding=10)
        concepts_frame.pack(fill=tk.X, pady=10)
        
        concepts = [
            ("VAR: Variables", "Each empty cell is a variable Xi"),
            ("DOM: Domains", "Domain D(Xi) = {1, ..., 9}, legal values per cell"),
            ("CON: Constraints", "All Different: every row, column & 3x3 box"),
            ("AC-3: Arc-Consistency", "Enforce arc-consistency, prune domains via arcs"),
            ("MRV: Minimum Remaining Values", "select variable with smallest domain first"),
            ("FC: Forward Checking", "prune values from peers' domains"),
            ("BT: Backtracking", "Undo assignment when domain becomes empty")
        ]
        
        for i, (title, desc) in enumerate(concepts):
            frame = ttk.Frame(concepts_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=title, font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Label(frame, text=desc, font=('Arial', 9)).pack(side=tk.LEFT)
        
        # Right side - Statistics and controls
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Control panel
        control_frame = ttk.LabelFrame(right_frame, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Puzzle difficulty
        diff_frame = ttk.Frame(control_frame)
        diff_frame.pack(fill=tk.X, pady=5)
        ttk.Label(diff_frame, text="Puzzle:").pack(side=tk.LEFT)
        self.difficulty_var = tk.StringVar(value="Easy")
        diff_combo = ttk.Combobox(diff_frame, textvariable=self.difficulty_var,
                                  values=["Easy", "Medium", "Hard"], width=10, state='readonly')
        diff_combo.pack(side=tk.LEFT, padx=5)
        
        # Speed control
        speed_frame = ttk.Frame(control_frame)
        speed_frame.pack(fill=tk.X, pady=5)
        ttk.Label(speed_frame, text="Speed (ms):").pack(side=tk.LEFT)
        self.speed_var = tk.StringVar(value="100")
        speed_spin = ttk.Spinbox(speed_frame, from_=10, to=500, textvariable=self.speed_var, width=10)
        speed_spin.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="New Puzzle", command=self.new_puzzle).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Solve", command=self.solve).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Stop", command=self.stop_solving).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Reset", command=self.reset).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Show Domains", command=self.show_domains).pack(side=tk.LEFT, padx=2)
        
        # Live solver statistics
        stats_frame = ttk.LabelFrame(right_frame, text="LIVE SOLVER STATISTICS", padding=10)
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.stats_vars = {}
        stat_items = [
            ("Nodes Explored:", "0"),
            ("Backtracks:", "0"),
            ("Arc-Consistency (AC-3) Arc Checks:", "0"),
            ("Forward Checking Domain Prunes:", "0"),
            ("Elapsed Time:", "0.000s"),
            ("Domain Size & Selected Cell:", "—")
        ]
        
        for label, default in stat_items:
            frame = ttk.Frame(stats_frame)
            frame.pack(fill=tk.X, pady=3)
            ttk.Label(frame, text=label, font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            self.stats_vars[label] = ttk.Label(frame, text=default, font=('Arial', 9))
            self.stats_vars[label].pack(side=tk.RIGHT)
        
        # Selected cell domain
        domain_frame = ttk.LabelFrame(right_frame, text="SELECTED CELL DOMAIN", padding=10)
        domain_frame.pack(fill=tk.X, pady=10)
        
        self.domain_label = ttk.Label(domain_frame, text="Click a cell to view its domain", 
                                      font=('Arial', 10), wraplength=250)
        self.domain_label.pack()
        
        # Event log
        log_frame = ttk.LabelFrame(right_frame, text="CONSTRAINT SATISFACTION PROBLEM (CSP) EVENT LOG", 
                                   padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, height=10, width=40, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log("CSP Solver initialized")
        self.log("Ready to solve...")
    
    def initialize_domains(self):
        """Initialize domains for all cells"""
        self.domains = {}
        for row in range(9):
            for col in range(9):
                if self.current_board[row][col] == 0:
                    # Empty cell - domain is all possible values
                    self.domains[(row, col)] = set(range(1, 10))
                else:
                    # Filled cell - domain is just that value
                    self.domains[(row, col)] = {self.current_board[row][col]}
        
        # Apply initial constraints to prune domains
        self.ac3()
    
    def draw_board(self):
        """Draw the Sudoku board"""
        self.board_canvas.delete("all")
        
        cell_size = 450 // 9
        
        # Draw grid
        for i in range(10):
            width = 3 if i % 3 == 0 else 1
            color = '#333' if i % 3 == 0 else '#999'
            
            # Vertical lines
            x = i * cell_size
            self.board_canvas.create_line(x, 0, x, 450, width=width, fill=color)
            
            # Horizontal lines
            y = i * cell_size
            self.board_canvas.create_line(0, y, 450, y, width=width, fill=color)
        
        # Draw numbers
        for row in range(9):
            for col in range(9):
                value = self.current_board[row][col]
                if value != 0:
                    x = col * cell_size + cell_size // 2
                    y = row * cell_size + cell_size // 2
                    
                    # Different color for initial vs solved
                    if self.initial_board[row][col] != 0:
                        color = '#000'  # Original clues - black
                        font_weight = 'bold'
                    else:
                        color = '#00F'  # Solved cells - blue
                        font_weight = 'normal'
                    
                    self.board_canvas.create_text(x, y, text=str(value), 
                                                  font=('Arial', 16, font_weight),
                                                  fill=color)
        
        # Highlight selected cell
        if self.selected_cell:
            row, col = self.selected_cell
            x1 = col * cell_size
            y1 = row * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            self.board_canvas.create_rectangle(x1, y1, x2, y2, outline='#ffd700', 
                                               width=3, tags='highlight')
    
    def on_cell_click(self, event):
        """Handle cell click"""
        cell_size = 450 // 9
        col = event.x // cell_size
        row = event.y // cell_size
        
        if 0 <= row < 9 and 0 <= col < 9:
            self.selected_cell = (row, col)
            self.draw_board()
            self.update_domain_display()
    
    def update_domain_display(self):
        """Update the domain display for selected cell"""
        if self.selected_cell and self.selected_cell in self.domains:
            domain = sorted(self.domains[self.selected_cell])
            value = self.current_board[self.selected_cell[0]][self.selected_cell[1]]
            
            if value != 0:
                text = f"Cell [{self.selected_cell[0]+1},{self.selected_cell[1]+1}]\nFixed value: {value}"
            else:
                text = f"Cell [{self.selected_cell[0]+1},{self.selected_cell[1]+1}]\nDomain: {{{', '.join(map(str, domain))}}}"
                text += f"\nSize: {len(domain)}"
            
            self.domain_label.config(text=text)
    
    def log(self, message):
        """Add message to event log"""
        self.log_text.insert(tk.END, f"> {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def update_stats(self):
        """Update statistics display"""
        self.stats_vars["Nodes Explored:"].config(text=str(self.stats['nodes']))
        self.stats_vars["Backtracks:"].config(text=str(self.stats['backtracks']))
        self.stats_vars["Arc-Consistency (AC-3) Arc Checks:"].config(text=str(self.stats['arc_checks']))
        self.stats_vars["Forward Checking Domain Prunes:"].config(text=str(self.stats['prunes']))
        self.stats_vars["Elapsed Time:"].config(text=f"{self.stats['time']:.3f}s")
        
        if self.selected_cell and self.selected_cell in self.domains:
            domain_size = len(self.domains[self.selected_cell])
            self.stats_vars["Domain Size & Selected Cell:"].config(
                text=f"{domain_size} at [{self.selected_cell[0]+1},{self.selected_cell[1]+1}]")
    
    def ac3(self):
        """AC-3 algorithm for arc consistency"""
        queue = deque()
        
        # Create all arcs (i, j) where i and j are related by constraints
        for row in range(9):
            for col in range(9):
                var1 = (row, col)
                # Add arcs to peers in same row
                for c in range(9):
                    if c != col:
                        var2 = (row, c)
                        queue.append((var1, var2))
                
                # Add arcs to peers in same column
                for r in range(9):
                    if r != row:
                        var2 = (r, col)
                        queue.append((var1, var2))
                
                # Add arcs to peers in same 3x3 box
                box_row, box_col = 3 * (row // 3), 3 * (col // 3)
                for r in range(box_row, box_row + 3):
                    for c in range(box_col, box_col + 3):
                        if r != row or c != col:
                            var2 = (r, c)
                            queue.append((var1, var2))
        
        # Process arcs
        while queue:
            (xi, xj) = queue.popleft()
            self.stats['arc_checks'] += 1
            
            if self.revise(xi, xj):
                if len(self.domains[xi]) == 0:
                    return False  # Domain wipe out
                
                # Add all neighbors of xi except xj back to queue
                for neighbor in self.get_neighbors(xi):
                    if neighbor != xj:
                        queue.append((neighbor, xi))
        
        return True
    
    def revise(self, xi, xj):
        """Revise domain of xi based on xj"""
        revised = False
        
        # For each value in domain of xi
        for val in list(self.domains[xi]):
            # Check if there's a value in domain of xj that satisfies constraint
            consistent = False
            for other_val in self.domains[xj]:
                if val != other_val:  # Different constraint
                    consistent = True
                    break
            
            if not consistent:
                self.domains[xi].remove(val)
                self.stats['prunes'] += 1
                revised = True
        
        return revised
    
    def get_neighbors(self, var):
        """Get all neighbors of a variable"""
        row, col = var
        neighbors = set()
        
        # Same row
        for c in range(9):
            if c != col:
                neighbors.add((row, c))
        
        # Same column
        for r in range(9):
            if r != row:
                neighbors.add((r, col))
        
        # Same box
        box_row, box_col = 3 * (row // 3), 3 * (col // 3)
        for r in range(box_row, box_row + 3):
            for c in range(box_col, box_col + 3):
                if r != row or c != col:
                    neighbors.add((r, c))
        
        return neighbors
    
    def select_unassigned_variable(self):
        """MRV - select variable with smallest domain"""
        min_domain_size = 10
        selected_var = None
        
        for (row, col), domain in self.domains.items():
            if self.current_board[row][col] == 0:  # Unassigned
                if len(domain) < min_domain_size:
                    min_domain_size = len(domain)
                    selected_var = (row, col)
        
        return selected_var
    
    def solve(self):
        """Start solving the puzzle"""
        if self.solving:
            return
        
        self.solving = True
        self.stats['time'] = 0
        self.start_time = time.time()
        
        # Reset statistics
        self.stats['nodes'] = 0
        self.stats['backtracks'] = 0
        self.stats['arc_checks'] = 0
        self.stats['prunes'] = 0
        
        self.log("Starting CSP solver...")
        self.log(f"Using AC-3 for arc consistency, MRV for variable selection")
        
        # Start recursive backtracking
        self.root.after(100, self.backtrack)
    
    def backtrack(self):
        """Recursive backtracking with visualization"""
        if not self.solving:
            return
        
        self.stats['nodes'] += 1
        self.stats['time'] = time.time() - self.start_time
        self.update_stats()
        
        # Select unassigned variable using MRV
        var = self.select_unassigned_variable()
        
        if var is None:  # All variables assigned
            self.log("Solution found!")
            self.solving = False
            return True
        
        row, col = var
        original_domain = self.domains[var].copy()
        
        # Try each value in domain
        for value in sorted(original_domain):
            self.log(f"Trying {value} at [{row+1},{col+1}]")
            
            # Assign value
            self.current_board[row][col] = value
            self.draw_board()
            self.root.update()
            
            # Save current domains for backtracking
            old_domains = copy.deepcopy(self.domains)
            
            # Update domain for this variable
            self.domains[var] = {value}
            
            # Apply forward checking
            if self.forward_check(var, value):
                # Run AC-3
                if self.ac3():
                    # Check if any domain is empty
                    if all(len(domain) > 0 for domain in self.domains.values()):
                        # Recurse
                        speed = int(self.speed_var.get())
                        self.root.after(speed, lambda: self.continue_backtrack(var, value, old_domains))
                        return
        
        # All values failed - backtrack
        self.stats['backtracks'] += 1
        self.log(f"Backtracking at [{row+1},{col+1}]")
        self.current_board[row][col] = 0
        self.draw_board()
        self.update_stats()
        
        # Continue backtracking
        self.root.after(50, self.backtrack)
        return False
    
    def continue_backtrack(self, var, value, old_domains):
        """Continue backtracking after delay"""
        if self.backtrack():
            return True
        
        # Restore domains and try next value
        self.domains = old_domains
        return False
    
    def forward_check(self, var, value):
        """Forward checking - prune values from neighbors"""
        row, col = var
        
        # Check all peers
        for neighbor in self.get_neighbors(var):
            if value in self.domains[neighbor]:
                self.domains[neighbor].remove(value)
                self.stats['prunes'] += 1
                
                if len(self.domains[neighbor]) == 0:
                    return False  # Domain wipe out
        
        return True
    
    def stop_solving(self):
        """Stop the solving process"""
        self.solving = False
        self.log("Solving stopped by user")
    
    def new_puzzle(self):
        """Load a new puzzle"""
        self.stop_solving()
        
        if self.difficulty_var.get() == "Easy":
            self.initial_board = [
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
        elif self.difficulty_var.get() == "Medium":
            self.initial_board = [
                [0, 0, 0, 2, 6, 0, 7, 0, 1],
                [6, 8, 0, 0, 7, 0, 0, 9, 0],
                [1, 9, 0, 0, 0, 4, 5, 0, 0],
                [8, 2, 0, 1, 0, 0, 0, 4, 0],
                [0, 0, 4, 6, 0, 2, 9, 0, 0],
                [0, 5, 0, 0, 0, 3, 0, 2, 8],
                [0, 0, 9, 3, 0, 0, 0, 7, 4],
                [0, 4, 0, 0, 5, 0, 0, 3, 6],
                [7, 0, 3, 0, 1, 8, 0, 0, 0]
            ]
        else:  # Hard
            self.initial_board = [
                [0, 2, 0, 6, 0, 8, 0, 0, 0],
                [5, 8, 0, 0, 0, 9, 7, 0, 0],
                [0, 0, 0, 0, 4, 0, 0, 1, 0],
                [3, 7, 0, 2, 0, 0, 0, 6, 0],
                [0, 0, 0, 0, 9, 0, 0, 0, 0],
                [0, 5, 0, 0, 0, 3, 0, 9, 2],
                [0, 1, 0, 0, 6, 0, 0, 0, 0],
                [0, 0, 9, 4, 0, 0, 0, 7, 5],
                [0, 0, 0, 9, 0, 2, 0, 3, 0]
            ]
        
        self.reset()
        self.log(f"New {self.difficulty_var.get()} puzzle loaded")
    
    def reset(self):
        """Reset to initial puzzle"""
        self.stop_solving()
        self.current_board = copy.deepcopy(self.initial_board)
        self.selected_cell = None
        self.initialize_domains()
        self.draw_board()
        self.domain_label.config(text="Click a cell to view its domain")
        
        # Reset stats
        self.stats = {
            'nodes': 0,
            'backtracks': 0,
            'arc_checks': 0,
            'prunes': 0,
            'time': 0
        }
        self.update_stats()
        self.log("Puzzle reset")
    
    def show_domains(self):
        """Show all domains in a new window"""
        domain_window = tk.Toplevel(self.root)
        domain_window.title("Current Domains")
        domain_window.geometry("600x500")
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(domain_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Display domains
        for row in range(9):
            for col in range(9):
                var = (row, col)
                if var in self.domains:
                    domain = sorted(self.domains[var])
                    value = self.current_board[row][col]
                    
                    if value != 0:
                        text_widget.insert(tk.END, f"Cell [{row+1},{col+1}]: {value} (fixed)\n")
                    else:
                        text_widget.insert(tk.END, f"Cell [{row+1},{col+1}]: {{{', '.join(map(str, domain))}}} (size: {len(domain)})\n")
            
            text_widget.insert(tk.END, "\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuGUI(root)
    root.mainloop()