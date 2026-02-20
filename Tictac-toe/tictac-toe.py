# tic_tac_toe.py
import tkinter as tk
from tkinter import ttk
import math
import time
import random

class TicTacToeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic-Tac-Toe - Minimax vs Alpha-Beta Pruning")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Game state
        self.board = [' '] * 9  # 3x3 board
        self.current_player = 'X'  # X is Human (MIN), O is AI (MAX)
        self.game_over = False
        self.winner = None
        
        # Statistics
        self.minimax_nodes = 0
        self.alphabeta_nodes = 0
        self.pruned_branches = 0
        self.scores = {'X': 0, 'O': 0, 'Draws': 0}
        
        # Pruned nodes visualization
        self.pruned_nodes = set()
        self.root_nodes = set()
        
        self.setup_ui()
        self.draw_board()
    
    def setup_ui(self):
        # Title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=10)
        
        title_label = ttk.Label(title_frame, text="Adversarial Search — Agent vs Agent", 
                                font=('Arial', 18, 'bold'))
        title_label.pack()
        
        subtitle = ttk.Label(title_frame, 
                            text="MIN Player (X) vs MAX Player (O) - Amber cells = pruned subtrees",
                            font=('Arial', 10))
        subtitle.pack()
        
        # Algorithm selection
        algo_frame = ttk.LabelFrame(self.root, text="Algorithm Settings", padding=10)
        algo_frame.pack(pady=10, fill=tk.X, padx=20)
        
        ttk.Label(algo_frame, text="AI Algorithm:", font=('Arial', 11)).pack(side=tk.LEFT, padx=5)
        self.algorithm_var = tk.StringVar(value="Alpha-Beta Pruning")
        algo_combo = ttk.Combobox(algo_frame, textvariable=self.algorithm_var,
                                  values=["Basic Minimax", "Alpha-Beta Pruning"],
                                  width=20, state='readonly')
        algo_combo.pack(side=tk.LEFT, padx=5)
        
        # Control buttons
        control_frame = ttk.Frame(algo_frame)
        control_frame.pack(side=tk.RIGHT)
        
        ttk.Button(control_frame, text="New Game", command=self.new_game).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Reset Scores", command=self.reset_scores).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Compare", command=self.compare_algorithms).pack(side=tk.LEFT, padx=5)
        
        # Main content area
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left side - Game board
        board_frame = ttk.LabelFrame(content_frame, text="Game Board", padding=20)
        board_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.board_canvas = tk.Canvas(board_frame, width=400, height=400, bg='white', 
                                      highlightthickness=2, highlightbackground='#ccc')
        self.board_canvas.pack()
        self.board_canvas.bind('<Button-1>', self.on_board_click)
        
        # Game status
        self.status_label = ttk.Label(board_frame, text="Your turn (X)", 
                                      font=('Arial', 14, 'bold'))
        self.status_label.pack(pady=10)
        
        # Right side - Statistics
        stats_frame = ttk.LabelFrame(content_frame, text="Search Statistics", padding=15)
        stats_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Score display
        score_container = ttk.Frame(stats_frame)
        score_container.pack(fill=tk.X, pady=10)
        
        self.score_labels = {}
        for i, (player, color) in enumerate([('X (MIN)', '#ff9999'), 
                                             ('O (MAX)', '#99ff99'), 
                                             ('Draws', '#9999ff')]):
            frame = ttk.Frame(score_container)
            frame.grid(row=0, column=i, padx=10)
            
            # Colored indicator
            canvas = tk.Canvas(frame, width=20, height=20, bg=color, highlightthickness=0)
            canvas.pack()
            
            ttk.Label(frame, text=player, font=('Arial', 10)).pack()
            self.score_labels[player] = ttk.Label(frame, text="0", font=('Arial', 16, 'bold'))
            self.score_labels[player].pack()
        
        # Separator
        ttk.Separator(stats_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Last move statistics
        ttk.Label(stats_frame, text="Last Move Statistics:", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        self.stats_vars = {}
        stats_items = [
            ("Agent", "O (MAX)"),
            ("Role", "MAX — maximises score"),
            ("Algorithm used", "Alpha-Beta Pruning"),
            ("Nodes explored", "0"),
            ("Time taken", "0 ms"),
            ("Pruned branches", "0"),
            ("Pruning efficiency", "0%")
        ]
        
        for label, value in stats_items:
            frame = ttk.Frame(stats_frame)
            frame.pack(fill=tk.X, pady=3)
            ttk.Label(frame, text=f"{label}:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
            self.stats_vars[label] = ttk.Label(frame, text=value, font=('Arial', 10))
            self.stats_vars[label].pack(side=tk.RIGHT)
        
        # Pruning visualization note
        note_frame = ttk.Frame(stats_frame)
        note_frame.pack(fill=tk.X, pady=20)
        
        # Amber color indicator
        amber_canvas = tk.Canvas(note_frame, width=20, height=20, bg='#ffb84d', highlightthickness=0)
        amber_canvas.pack(side=tk.LEFT, padx=(0, 5))
        
        note_label = ttk.Label(note_frame, 
                              text="Amber cells = considered at root\nbut subtree PRUNED (β ≤ α cutoff)",
                              justify=tk.LEFT)
        note_label.pack(side=tk.LEFT)
    
    def draw_board(self):
        """Draw the tic-tac-toe board"""
        self.board_canvas.delete("all")
        
        cell_size = 400 // 3
        offset = 0
        
        # Draw grid
        for i in range(1, 3):
            # Vertical lines
            x = i * cell_size
            self.board_canvas.create_line(x, 0, x, 400, width=3, fill='#333')
            
            # Horizontal lines
            y = i * cell_size
            self.board_canvas.create_line(0, y, 400, y, width=3, fill='#333')
        
        # Draw X's and O's
        for i in range(9):
            row = i // 3
            col = i % 3
            x = col * cell_size + cell_size // 2
            y = row * cell_size + cell_size // 2
            
            if self.board[i] == 'X':
                # Draw X
                self.board_canvas.create_line(x-40, y-40, x+40, y+40, width=4, fill='#ff4444')
                self.board_canvas.create_line(x+40, y-40, x-40, y+40, width=4, fill='#ff4444')
            elif self.board[i] == 'O':
                # Draw O
                self.board_canvas.create_oval(x-40, y-40, x+40, y+40, width=4, outline='#4444ff')
        
        # Highlight winning line if game is over
        if self.game_over and self.winner and self.winner != 'draw':
            self.highlight_winning_line()
    
    def highlight_winning_line(self):
        """Highlight the winning line"""
        lines = [
            [(0, 0), (0, 1), (0, 2)],  # Row 0
            [(1, 0), (1, 1), (1, 2)],  # Row 1
            [(2, 0), (2, 1), (2, 2)],  # Row 2
            [(0, 0), (1, 0), (2, 0)],  # Column 0
            [(0, 1), (1, 1), (2, 1)],  # Column 1
            [(0, 2), (1, 2), (2, 2)],  # Column 2
            [(0, 0), (1, 1), (2, 2)],  # Diagonal
            [(0, 2), (1, 1), (2, 0)]   # Anti-diagonal
        ]
        
        cell_size = 400 // 3
        
        for line in lines:
            cells = [r * 3 + c for r, c in line]
            if all(self.board[i] == self.winner for i in cells):
                # Draw highlight line
                start_col, start_row = line[0][1], line[0][0]
                end_col, end_row = line[2][1], line[2][0]
                
                start_x = start_col * cell_size + cell_size // 2
                start_y = start_row * cell_size + cell_size // 2
                end_x = end_col * cell_size + cell_size // 2
                end_y = end_row * cell_size + cell_size // 2
                
                self.board_canvas.create_line(start_x, start_y, end_x, end_y, 
                                             width=8, fill='#ffd700', dash=(10, 5))
                break
    
    def on_board_click(self, event):
        """Handle board clicks"""
        if self.game_over or self.current_player != 'X':
            return
        
        # Calculate which cell was clicked
        cell_size = 400 // 3
        col = event.x // cell_size
        row = event.y // cell_size
        
        if 0 <= row < 3 and 0 <= col < 3:
            index = row * 3 + col
            if self.board[index] == ' ':
                self.make_move(index, 'X')
                
                # AI move
                if not self.game_over and self.current_player == 'O':
                    self.root.after(500, self.ai_move)
    
    def make_move(self, position, player):
        """Make a move on the board"""
        if self.board[position] == ' ' and not self.game_over:
            self.board[position] = player
            
            # Check win/draw
            winner = self.check_winner()
            if winner:
                self.game_over = True
                self.winner = winner
                if winner == 'X':
                    self.scores['X'] += 1
                    self.status_label.config(text="X wins!")
                elif winner == 'O':
                    self.scores['O'] += 1
                    self.status_label.config(text="O wins!")
                elif winner == 'draw':
                    self.scores['Draws'] += 1
                    self.status_label.config(text="It's a draw!")
                    self.winner = 'draw'
                
                self.update_scores()
            else:
                self.current_player = 'O' if player == 'X' else 'X'
                self.status_label.config(text=f"{'Your' if self.current_player == 'X' else 'AI'} turn ({self.current_player})")
            
            self.draw_board()
    
    def ai_move(self):
        """Make AI move using selected algorithm"""
        if self.game_over or self.current_player != 'O':
            return
        
        # Reset statistics
        self.minimax_nodes = 0
        self.alphabeta_nodes = 0
        self.pruned_branches = 0
        self.pruned_nodes = set()
        self.root_nodes = set()
        
        start_time = time.time()
        
        if self.algorithm_var.get() == "Basic Minimax":
            score, move = self.minimax(self.board, 0, False)
            nodes = self.minimax_nodes
            algorithm_name = "Basic Minimax"
            pruned = 0
            efficiency = 0
        else:
            score, move = self.alphabeta(self.board, 0, -math.inf, math.inf, False, "")
            nodes = self.alphabeta_nodes
            algorithm_name = "Alpha-Beta Pruning"
            pruned = self.pruned_branches
            efficiency = (pruned / nodes * 100) if nodes > 0 else 0
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        if move is not None:
            self.make_move(move, 'O')
            
            # Update statistics
            self.stats_vars["Agent"].config(text="O (MAX)")
            self.stats_vars["Algorithm used"].config(text=algorithm_name)
            self.stats_vars["Nodes explored"].config(text=f"{nodes:,}")
            self.stats_vars["Time taken"].config(text=f"{elapsed_time:.2f}")
            self.stats_vars["Pruned branches"].config(text=f"{pruned:,}")
            self.stats_vars["Pruning efficiency"].config(text=f"{efficiency:.1f}%")
    
    def minimax(self, board, depth, is_maximizing):
        """Minimax algorithm"""
        self.minimax_nodes += 1
        
        winner = self.check_winner(board)
        if winner == 'O':
            return 10 - depth, None
        elif winner == 'X':
            return -10 + depth, None
        elif winner == 'draw' or ' ' not in board:
            return 0, None
        
        if is_maximizing:
            best_score = -math.inf
            best_move = None
            
            for i in range(9):
                if board[i] == ' ':
                    board[i] = 'O'
                    score, _ = self.minimax(board, depth + 1, False)
                    board[i] = ' '
                    
                    if score > best_score:
                        best_score = score
                        best_move = i
            
            return best_score, best_move
        else:
            best_score = math.inf
            best_move = None
            
            for i in range(9):
                if board[i] == ' ':
                    board[i] = 'X'
                    score, _ = self.minimax(board, depth + 1, True)
                    board[i] = ' '
                    
                    if score < best_score:
                        best_score = score
                        best_move = i
            
            return best_score, best_move
    
    def alphabeta(self, board, depth, alpha, beta, is_maximizing, path):
        """Minimax with alpha-beta pruning"""
        self.alphabeta_nodes += 1
        
        # Track root level nodes for pruning visualization
        if depth == 1:
            self.root_nodes.add(path)
        
        winner = self.check_winner(board)
        if winner == 'O':
            return 10 - depth, None
        elif winner == 'X':
            return -10 + depth, None
        elif winner == 'draw' or ' ' not in board:
            return 0, None
        
        if is_maximizing:
            best_score = -math.inf
            best_move = None
            
            for i in range(9):
                if board[i] == ' ':
                    board[i] = 'O'
                    score, _ = self.alphabeta(board, depth + 1, alpha, beta, False, path + str(i))
                    board[i] = ' '
                    
                    if score > best_score:
                        best_score = score
                        best_move = i
                    
                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        # Beta cutoff - mark pruned branch
                        self.pruned_branches += 1
                        if depth == 0:
                            self.pruned_nodes.add(path + str(i))
                        break
            
            return best_score, best_move
        else:
            best_score = math.inf
            best_move = None
            
            for i in range(9):
                if board[i] == ' ':
                    board[i] = 'X'
                    score, _ = self.alphabeta(board, depth + 1, alpha, beta, True, path + str(i))
                    board[i] = ' '
                    
                    if score < best_score:
                        best_score = score
                        best_move = i
                    
                    beta = min(beta, best_score)
                    if beta <= alpha:
                        # Alpha cutoff - mark pruned branch
                        self.pruned_branches += 1
                        if depth == 0:
                            self.pruned_nodes.add(path + str(i))
                        break
            
            return best_score, best_move
    
    def check_winner(self, board=None):
        """Check if there's a winner"""
        if board is None:
            board = self.board
        
        # All possible winning lines
        lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]               # Diagonals
        ]
        
        for line in lines:
            if board[line[0]] != ' ' and all(board[line[0]] == board[i] for i in line):
                return board[line[0]]
        
        # Check for draw
        if ' ' not in board:
            return 'draw'
        
        return None
    
    def new_game(self):
        """Start a new game"""
        self.board = [' '] * 9
        self.current_player = 'X'
        self.game_over = False
        self.winner = None
        self.status_label.config(text="Your turn (X)")
        self.draw_board()
    
    def reset_scores(self):
        """Reset all scores"""
        self.scores = {'X': 0, 'O': 0, 'Draws': 0}
        self.update_scores()
        self.new_game()
    
    def update_scores(self):
        """Update score display"""
        self.score_labels['X (MIN)'].config(text=str(self.scores['X']))
        self.score_labels['O (MAX)'].config(text=str(self.scores['O']))
        self.score_labels['Draws'].config(text=str(self.scores['Draws']))
    
    def compare_algorithms(self):
        """Run comparison between algorithms"""
        # Create comparison window
        compare_window = tk.Toplevel(self.root)
        compare_window.title("Algorithm Comparison")
        compare_window.geometry("600x400")
        compare_window.transient(self.root)
        compare_window.grab_set()
        
        # Title
        ttk.Label(compare_window, text="Minimax vs Alpha-Beta Pruning Comparison",
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Test multiple board positions
        test_positions = [
            (['X', ' ', ' ', ' ', 'O', ' ', ' ', ' ', 'X'], "Position 1"),
            (['X', 'O', 'X', ' ', 'O', ' ', ' ', ' ', ' '], "Position 2"),
            (['X', ' ', ' ', ' ', 'O', ' ', ' ', ' ', ' '], "Position 3")
        ]
        
        # Create results frame
        results_frame = ttk.Frame(compare_window)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Headers
        headers = ["Position", "Minimax Nodes", "Alpha-Beta Nodes", "Pruned", "Speedup"]
        for i, header in enumerate(headers):
            ttk.Label(results_frame, text=header, font=('Arial', 10, 'bold')).grid(row=0, column=i, padx=5, pady=5)
        
        total_minimax = 0
        total_alphabeta = 0
        total_pruned = 0
        
        # Test each position
        for row, (board, name) in enumerate(test_positions, start=1):
            # Test Minimax
            self.minimax_nodes = 0
            start_time = time.time()
            score, move = self.minimax(board, 0, True)
            minimax_time = (time.time() - start_time) * 1000
            minimax_nodes = self.minimax_nodes
            
            # Test Alpha-Beta
            self.alphabeta_nodes = 0
            self.pruned_branches = 0
            start_time = time.time()
            score, move = self.alphabeta(board, 0, -math.inf, math.inf, True, "")
            alphabeta_time = (time.time() - start_time) * 1000
            alphabeta_nodes = self.alphabeta_nodes
            pruned = self.pruned_branches
            
            total_minimax += minimax_nodes
            total_alphabeta += alphabeta_nodes
            total_pruned += pruned
            
            speedup = (minimax_nodes - alphabeta_nodes) / minimax_nodes * 100 if minimax_nodes > 0 else 0
            
            # Display results
            ttk.Label(results_frame, text=name).grid(row=row, column=0, padx=5, pady=2)
            ttk.Label(results_frame, text=f"{minimax_nodes:,}").grid(row=row, column=1, padx=5)
            ttk.Label(results_frame, text=f"{alphabeta_nodes:,}").grid(row=row, column=2, padx=5)
            ttk.Label(results_frame, text=f"{pruned:,}").grid(row=row, column=3, padx=5)
            ttk.Label(results_frame, text=f"{speedup:.1f}%").grid(row=row, column=4, padx=5)
        
        # Totals
        ttk.Separator(results_frame, orient='horizontal').grid(row=len(test_positions)+1, column=0, columnspan=5, sticky='ew', pady=10)
        
        total_speedup = (total_minimax - total_alphabeta) / total_minimax * 100 if total_minimax > 0 else 0
        
        ttk.Label(results_frame, text="TOTAL", font=('Arial', 10, 'bold')).grid(row=len(test_positions)+2, column=0, padx=5, pady=2)
        ttk.Label(results_frame, text=f"{total_minimax:,}", font=('Arial', 10, 'bold')).grid(row=len(test_positions)+2, column=1, padx=5)
        ttk.Label(results_frame, text=f"{total_alphabeta:,}", font=('Arial', 10, 'bold')).grid(row=len(test_positions)+2, column=2, padx=5)
        ttk.Label(results_frame, text=f"{total_pruned:,}", font=('Arial', 10, 'bold')).grid(row=len(test_positions)+2, column=3, padx=5)
        ttk.Label(results_frame, text=f"{total_speedup:.1f}%", font=('Arial', 10, 'bold')).grid(row=len(test_positions)+2, column=4, padx=5)
        
        # Summary
        summary = f"""Alpha-Beta Pruning explores {((total_alphabeta/total_minimax)*100):.1f}% of nodes
compared to basic Minimax, with {total_pruned:,} nodes pruned."""
        
        ttk.Label(compare_window, text=summary, font=('Arial', 11)).pack(pady=10)
        
        # Close button
        ttk.Button(compare_window, text="Close", command=compare_window.destroy).pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = TicTacToeGUI(root)
    root.mainloop()