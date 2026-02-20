# river_crossing.py
import tkinter as tk
from tkinter import ttk
from collections import deque
import time
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class RiverCrossingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("River Crossing Puzzle - BFS/DFS Visualizer")
        self.root.geometry("1200x800")
        
        # Game state
        self.left_bank = ['👨 Man', '🐐 Goat', '🐆 Leopard', '🌾 Grass']
        self.right_bank = []
        self.boat_side = 'left'  # 'left' or 'right'
        
        # Search state
        self.search_tree = None
        self.current_node = None
        self.solution_path = []
        self.states_explored = []
        self.node_colors = {}
        self.node_positions = {}
        self.level_positions = {}  # For level-based visualization
        
        self.setup_ui()
        self.update_display()
        
    def setup_ui(self):
        # Control panel
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10)
        
        ttk.Label(control_frame, text="Algorithm:").pack(side=tk.LEFT, padx=5)
        self.algorithm_var = tk.StringVar(value="BFS")
        algo_combo = ttk.Combobox(control_frame, textvariable=self.algorithm_var, 
                                  values=["BFS", "DFS"], width=10, state='readonly')
        algo_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Start Search", 
                  command=self.start_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Step", 
                  command=self.step_search).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Reset", 
                  command=self.reset).pack(side=tk.LEFT, padx=5)
        
        # Speed control
        ttk.Label(control_frame, text="Speed (ms):").pack(side=tk.LEFT, padx=5)
        self.speed_var = tk.StringVar(value="1000")
        speed_spin = ttk.Spinbox(control_frame, from_=100, to=2000, 
                                 textvariable=self.speed_var, width=10)
        speed_spin.pack(side=tk.LEFT, padx=5)
        
        # Main display area with notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: River Visualization
        self.river_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.river_tab, text="River Crossing")
        
        # River visualization
        self.river_canvas = tk.Canvas(self.river_tab, height=200, bg='#e0f7fa')
        self.river_canvas.pack(fill=tk.X, pady=20)
        
        # Tab 2: Search Tree Visualization
        self.tree_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.tree_tab, text="Search Tree")
        
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tree_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(self.root, text="Search Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_vars = {}
        stats = ['States Explored:', 'Solution Depth:', 'Nodes in Memory:', 'Time (s):', 'Branching Factor:']
        for i, label in enumerate(stats):
            frame = ttk.Frame(stats_frame)
            frame.pack(side=tk.LEFT, expand=True)
            ttk.Label(frame, text=label, font=('Arial', 10, 'bold')).pack()
            self.stats_vars[label] = tk.StringVar(value="0")
            ttk.Label(frame, textvariable=self.stats_vars[label], 
                     font=('Arial', 12, 'bold')).pack()
        
        # Legend
        legend_frame = ttk.Frame(self.root)
        legend_frame.pack(pady=5)
        
        legend_items = [
            ('Unvisited', '#ddd', 'Nodes not yet explored'),
            ('Current', '#ffd700', 'Currently exploring'),
            ('Visited', '#87CEEB', 'Already explored'),
            ('Solution', '#90EE90', 'Part of solution path'),
            ('Goal', '#32CD32', 'Goal state reached')
        ]
        
        for text, color, tooltip in legend_items:
            frame = ttk.Frame(legend_frame)
            frame.pack(side=tk.LEFT, padx=10)
            canvas = tk.Canvas(frame, width=20, height=20, bg=color, highlightthickness=1)
            canvas.pack(side=tk.LEFT)
            label = ttk.Label(frame, text=text)
            label.pack(side=tk.LEFT)
            
            # Add tooltip
            self.create_tooltip(label, tooltip)
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
            
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    
    def is_valid_state(self, left, right, boat_side):
        """Check if state is valid (no eating happens)"""
        # Check left bank
        if boat_side == 'right':  # Boat on right, check left bank
            if '🐐 Goat' in left and '🌾 Grass' in left and '👨 Man' not in left:
                return False
            if '🐐 Goat' in left and '🐆 Leopard' in left and '👨 Man' not in left:
                return False
        else:  # Boat on left, check right bank
            if '🐐 Goat' in right and '🌾 Grass' in right and '👨 Man' not in right:
                return False
            if '🐐 Goat' in right and '🐆 Leopard' in right and '👨 Man' not in right:
                return False
        return True
    
    def get_possible_moves(self, state):
        """Get all possible next states"""
        left, right, boat_side = state
        possible_states = []
        
        # Determine which bank has the boat and items
        current_bank = left if boat_side == 'left' else right
        other_bank = right if boat_side == 'left' else left
        
        # Can take 1 or 2 items (but at least 1 if possible)
        items = current_bank.copy()
        
        # Try taking 1 item
        for item in items:
            new_current = [x for x in current_bank if x != item]
            new_other = other_bank + [item]
            
            if boat_side == 'left':
                new_state = (sorted(new_current), sorted(new_other), 'right')
            else:
                new_state = (sorted(new_other), sorted(new_current), 'left')
            
            if self.is_valid_state(new_state[0], new_state[1], new_state[2]):
                if new_state not in possible_states:
                    possible_states.append(new_state)
        
        # Try taking 2 items
        if len(items) >= 2:
            for i in range(len(items)):
                for j in range(i+1, len(items)):
                    new_current = [x for x in current_bank if x != items[i] and x != items[j]]
                    new_other = other_bank + [items[i], items[j]]
                    
                    if boat_side == 'left':
                        new_state = (sorted(new_current), sorted(new_other), 'right')
                    else:
                        new_state = (sorted(new_other), sorted(new_current), 'left')
                    
                    if self.is_valid_state(new_state[0], new_state[1], new_state[2]):
                        if new_state not in possible_states:
                            possible_states.append(new_state)
        
        return possible_states
    
    def state_to_string(self, state):
        """Convert state to string for node labeling"""
        left, right, boat = state
        left_items = ''.join([item[2] for item in left])  # Get emoji characters
        right_items = ''.join([item[2] for item in right])
        return f"L:{left_items}\nR:{right_items}\nB:{boat[0].upper()}"
    
    def bfs_search(self):
        """Breadth-First Search with level tracking"""
        start_state = (sorted(self.left_bank.copy()), sorted(self.right_bank.copy()), self.boat_side)
        goal_state = (sorted([]), sorted(['👨 Man', '🐐 Goat', '🐆 Leopard', '🌾 Grass']), 'right')
        
        # Queue stores (state, path, level)
        queue = deque([(start_state, [start_state], 0)])
        visited = {self.state_to_string(start_state): 0}  # state -> level
        
        self.search_tree = nx.DiGraph()
        self.node_levels = {self.state_to_string(start_state): 0}
        self.search_tree.add_node(self.state_to_string(start_state), 
                                 state=start_state, level=0)
        
        nodes_explored = 0
        max_branching = 0
        
        while queue:
            nodes_explored += 1
            current_state, path, level = queue.popleft()
            current_str = self.state_to_string(current_state)
            
            if current_state == goal_state:
                self.solution_path = path
                # Mark solution path nodes
                for i, s in enumerate(path):
                    s_str = self.state_to_string(s)
                    if s_str in self.search_tree.nodes:
                        self.search_tree.nodes[s_str]['solution'] = True
                        self.search_tree.nodes[s_str]['solution_level'] = i
                return True, path, nodes_explored, max_branching
            
            moves = self.get_possible_moves(current_state)
            max_branching = max(max_branching, len(moves))
            
            for next_state in moves:
                next_str = self.state_to_string(next_state)
                
                if next_str not in visited:
                    visited[next_str] = level + 1
                    self.node_levels[next_str] = level + 1
                    self.search_tree.add_node(next_str, state=next_state, 
                                             level=level + 1,
                                             goal=next_state == goal_state)
                    self.search_tree.add_edge(current_str, next_str)
                    queue.append((next_state, path + [next_state], level + 1))
        
        return False, [], nodes_explored, max_branching
    
    def dfs_search(self):
        """Depth-First Search with level tracking"""
        start_state = (sorted(self.left_bank.copy()), sorted(self.right_bank.copy()), self.boat_side)
        goal_state = (sorted([]), sorted(['👨 Man', '🐐 Goat', '🐆 Leopard', '🌾 Grass']), 'right')
        
        # Stack stores (state, path, level)
        stack = [(start_state, [start_state], 0)]
        visited = {self.state_to_string(start_state): 0}
        
        self.search_tree = nx.DiGraph()
        self.node_levels = {self.state_to_string(start_state): 0}
        self.search_tree.add_node(self.state_to_string(start_state), 
                                 state=start_state, level=0)
        
        nodes_explored = 0
        max_branching = 0
        
        while stack:
            nodes_explored += 1
            current_state, path, level = stack.pop()
            current_str = self.state_to_string(current_state)
            
            if current_state == goal_state:
                self.solution_path = path
                # Mark solution path nodes
                for i, s in enumerate(path):
                    s_str = self.state_to_string(s)
                    if s_str in self.search_tree.nodes:
                        self.search_tree.nodes[s_str]['solution'] = True
                        self.search_tree.nodes[s_str]['solution_level'] = i
                return True, path, nodes_explored, max_branching
            
            moves = self.get_possible_moves(current_state)
            max_branching = max(max_branching, len(moves))
            
            # Reverse to maintain order (optional)
            for next_state in reversed(moves):
                next_str = self.state_to_string(next_state)
                
                if next_str not in visited:
                    visited[next_str] = level + 1
                    self.node_levels[next_str] = level + 1
                    self.search_tree.add_node(next_str, state=next_state, 
                                             level=level + 1,
                                             goal=next_state == goal_state)
                    self.search_tree.add_edge(current_str, next_str)
                    stack.append((next_state, path + [next_state], level + 1))
        
        return False, [], nodes_explored, max_branching
    
    def draw_search_tree(self):
        """Draw the search tree with level-based layout"""
        self.ax.clear()
        
        if not self.search_tree or len(self.search_tree.nodes) == 0:
            return
        
        # Create level-based layout
        pos = {}
        levels = {}
        
        # Group nodes by level
        for node in self.search_tree.nodes:
            level = self.search_tree.nodes[node].get('level', 0)
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
        
        # Position nodes by level
        max_level = max(levels.keys()) if levels else 0
        for level, nodes in levels.items():
            y = 1 - (level / (max_level + 1))  # Top to bottom
            for i, node in enumerate(sorted(nodes)):
                x = (i + 1) / (len(nodes) + 1)
                pos[node] = (x, y)
        
        # Color nodes based on status
        node_colors = []
        for node in self.search_tree.nodes:
            if node == self.current_node:
                node_colors.append('#ffd700')  # Current node - gold
            elif self.search_tree.nodes[node].get('solution', False):
                node_colors.append('#90EE90')  # Solution path - light green
            elif self.search_tree.nodes[node].get('goal', False):
                node_colors.append('#32CD32')  # Goal node - green
            elif self.search_tree.nodes[node].get('visited', False):
                node_colors.append('#87CEEB')  # Visited - light blue
            else:
                node_colors.append('#ddd')  # Unvisited - light gray
        
        # Draw edges
        for edge in self.search_tree.edges:
            if edge[0] in pos and edge[1] in pos:
                # Check if edge is part of solution path
                is_solution = (self.search_tree.nodes[edge[0]].get('solution', False) and 
                             self.search_tree.nodes[edge[1]].get('solution', False))
                edge_color = '#006400' if is_solution else '#666'
                edge_width = 3 if is_solution else 1
                self.ax.plot([pos[edge[0]][0], pos[edge[1]][0]], 
                           [pos[edge[0]][1], pos[edge[1]][1]], 
                           color=edge_color, linewidth=edge_width, alpha=0.7)
        
        # Draw nodes
        for node, (x, y) in pos.items():
            color = node_colors[self.search_tree.nodes[node].get('index', 0)]
            circle = plt.Circle((x, y), 0.03, color=color, ec='black', linewidth=2)
            self.ax.add_patch(circle)
            
            # Add node label
            level = self.search_tree.nodes[node].get('level', 0)
            self.ax.text(x, y-0.04, f"L{level}", ha='center', va='top', fontsize=8)
        
        self.ax.set_xlim(-0.1, 1.1)
        self.ax.set_ylim(-0.1, 1.1)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.set_title(f"{self.algorithm_var.get()} Search Tree - Levels Visible")
        
        # Add level indicators
        for level in sorted(levels.keys()):
            y = 1 - (level / (max_level + 1))
            self.ax.text(-0.05, y, f"Level {level}", ha='right', va='center', 
                        fontsize=10, fontweight='bold')
        
        self.canvas.draw()
    
    def update_river_display(self, left_bank=None, right_bank=None, boat_side=None):
        """Update the river visualization"""
        self.river_canvas.delete("all")
        
        left = left_bank if left_bank else self.left_bank
        right = right_bank if right_bank else self.right_bank
        boat = boat_side if boat_side else self.boat_side
        
        # Draw river
        self.river_canvas.create_rectangle(200, 50, 800, 150, fill='#4A90E2', outline='')
        
        # Draw banks
        self.river_canvas.create_rectangle(100, 30, 200, 170, fill='#8B4513', outline='')
        self.river_canvas.create_rectangle(800, 30, 900, 170, fill='#5D3A1A', outline='')
        
        # Bank labels
        self.river_canvas.create_text(150, 15, text="LEFT BANK", fill='white', 
                                     font=('Arial', 12, 'bold'))
        self.river_canvas.create_text(850, 15, text="RIGHT BANK", fill='white', 
                                     font=('Arial', 12, 'bold'))
        
        # Items on left bank
        for i, item in enumerate(left):
            x = 130 + (i % 2) * 30
            y = 60 + (i // 2) * 30
            self.river_canvas.create_text(x, y, text=item, font=('Arial', 16))
        
        # Items on right bank
        for i, item in enumerate(right):
            x = 830 + (i % 2) * 30
            y = 60 + (i // 2) * 30
            self.river_canvas.create_text(x, y, text=item, font=('Arial', 16))
        
        # Draw boat
        boat_x = 500 if boat == 'right' else 300
        self.river_canvas.create_polygon(boat_x, 120, boat_x+60, 120, 
                                        boat_x+50, 140, boat_x+10, 140, 
                                        fill='#8B4513', outline='')
        self.river_canvas.create_text(boat_x+30, 130, text='⛵', font=('Arial', 20))
        
        # Add water waves
        for i in range(3):
            x = 300 + i * 150
            self.river_canvas.create_text(x, 100, text='~~~', font=('Arial', 20), fill='white')
    
    def start_search(self):
        """Start the search algorithm"""
        start_time = time.time()
        
        if self.algorithm_var.get() == "BFS":
            found, path, nodes, branching = self.bfs_search()
        else:
            found, path, nodes, branching = self.dfs_search()
        
        elapsed_time = time.time() - start_time
        
        self.states_explored = path if found else []
        
        # Update statistics
        self.stats_vars['States Explored:'].set(str(nodes))
        self.stats_vars['Solution Depth:'].set(str(len(path)-1 if found else 0))
        self.stats_vars['Nodes in Memory:'].set(str(len(self.search_tree.nodes)))
        self.stats_vars['Time (s):'].set(f"{elapsed_time:.2f}")
        self.stats_vars['Branching Factor:'].set(f"{branching:.1f}")
        
        self.draw_search_tree()
        
        # Switch to tree tab to show visualization
        self.notebook.select(self.tree_tab)
        
        # Animate solution path
        if found:
            self.animate_solution()
    
    def animate_solution(self):
        """Animate the solution path step by step"""
        if not self.states_explored:
            return
        
        def step_animation(index=0):
            if index < len(self.states_explored):
                state = self.states_explored[index]
                left, right, boat = state
                
                # Update river display
                self.update_river_display(left, right, boat)
                
                # Update current node in tree
                self.current_node = self.state_to_string(state)
                
                # Mark node as visited in tree
                if self.current_node in self.search_tree.nodes:
                    self.search_tree.nodes[self.current_node]['visited'] = True
                
                # Redraw tree
                self.draw_search_tree()
                
                # Schedule next step
                speed = int(self.speed_var.get())
                self.root.after(speed, lambda: step_animation(index + 1))
            else:
                self.current_node = None
                self.draw_search_tree()
        
        step_animation()
    
    def step_search(self):
        """Step through search manually"""
        if not hasattr(self, 'search_generator') or self.search_generator is None:
            self.status_label.config(text="Search is complete! Please reset or start a new search.")
            return
        try:
            result = next(self.search_generator)
            if result:
                state, current_str, visited_count, level = result
                left, right, boat = state
                # Update displays
                self.update_river_display(left, right, boat)
                self.current_node = current_str
                # Mark node as visited
                if current_str in self.search_tree.nodes:
                    self.search_tree.nodes[current_str]['visited'] = True
                self.draw_search_tree()
                # Update statistics
                self.stats_vars['States Explored:'].set(str(visited_count))
                self.stats_vars['Nodes in Memory:'].set(str(len(self.search_tree.nodes)))
                # Show current level
                self.stats_vars['Solution Depth:'].set(str(level))
        except StopIteration:
            self.search_generator = None
            self.status_label.config(text="Search complete!")
    
    def bfs_step_generator(self):
        """Generator for step-by-step BFS"""
        start_state = (sorted(self.left_bank.copy()), sorted(self.right_bank.copy()), self.boat_side)
        goal_state = (sorted([]), sorted(['👨 Man', '🐐 Goat', '🐆 Leopard', '🌾 Grass']), 'right')
        
        queue = deque([(start_state, [start_state], 0)])
        visited = {self.state_to_string(start_state): 0}
        
        self.search_tree = nx.DiGraph()
        self.search_tree.add_node(self.state_to_string(start_state), state=start_state, level=0)
        
        visited_count = 0
        
        while queue:
            visited_count += 1
            current_state, path, level = queue.popleft()
            current_str = self.state_to_string(current_state)
            
            yield current_state, current_str, visited_count, level
            
            if current_state == goal_state:
                self.solution_path = path
                return
            
            for next_state in self.get_possible_moves(current_state):
                next_str = self.state_to_string(next_state)
                
                if next_str not in visited:
                    visited[next_str] = level + 1
                    self.search_tree.add_node(next_str, state=next_state, level=level + 1)
                    self.search_tree.add_edge(current_str, next_str)
                    queue.append((next_state, path + [next_state], level + 1))
    
    def dfs_step_generator(self):
        """Generator for step-by-step DFS"""
        start_state = (sorted(self.left_bank.copy()), sorted(self.right_bank.copy()), self.boat_side)
        goal_state = (sorted([]), sorted(['👨 Man', '🐐 Goat', '🐆 Leopard', '🌾 Grass']), 'right')
        
        stack = [(start_state, [start_state], 0)]
        visited = {self.state_to_string(start_state): 0}
        
        self.search_tree = nx.DiGraph()
        self.search_tree.add_node(self.state_to_string(start_state), state=start_state, level=0)
        
        visited_count = 0
        
        while stack:
            visited_count += 1
            current_state, path, level = stack.pop()
            current_str = self.state_to_string(current_state)
            
            yield current_state, current_str, visited_count, level
            
            if current_state == goal_state:
                self.solution_path = path
                return
            
            for next_state in self.get_possible_moves(current_state):
                next_str = self.state_to_string(next_state)
                
                if next_str not in visited:
                    visited[next_str] = level + 1
                    self.search_tree.add_node(next_str, state=next_state, level=level + 1)
                    self.search_tree.add_edge(current_str, next_str)
                    stack.append((next_state, path + [next_state], level + 1))
    
    def reset(self):
        """Reset the game and search"""
        self.left_bank = ['👨 Man', '🐐 Goat', '🐆 Leopard', '🌾 Grass']
        self.right_bank = []
        self.boat_side = 'left'
        self.search_tree = None
        self.current_node = None
        self.solution_path = []
        self.states_explored = []
        self.search_generator = None
        self.node_levels = {}
        
        self.update_river_display()
        self.ax.clear()
        self.canvas.draw()
        
        for key in self.stats_vars:
            self.stats_vars[key].set("0")
        
        # Switch back to river tab
        self.notebook.select(self.river_tab)
    
    def update_display(self):
        """Update the display periodically"""
        self.update_river_display()
        self.root.after(100, self.update_display)

if __name__ == "__main__":
    root = tk.Tk()
    app = RiverCrossingGUI(root)
    root.mainloop()