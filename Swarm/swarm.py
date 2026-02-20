# swarm.py (fixed version)
import random
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import networkx as nx

# Romania cities and their approximate coordinates for visualization
cities_coords = {
    'Arad': (91, 492),
    'Bucharest': (400, 327),
    'Craiova': (253, 288),
    'Drobeta': (165, 299),
    'Eforie': (562, 293),
    'Fagaras': (305, 449),
    'Giurgiu': (375, 270),
    'Hirsova': (534, 318),
    'Iasi': (473, 506),
    'Lugoj': (165, 379),
    'Mehadia': (168, 339),
    'Neamt': (406, 537),
    'Oradea': (131, 571),
    'Pitesti': (320, 368),
    'Rimnicu Vilcea': (233, 410),
    'Sibiu': (207, 457),
    'Timisoara': (94, 410),
    'Urziceni': (456, 350),
    'Vaslui': (509, 445),
    'Zerind': (108, 531)
}

cities = list(cities_coords.keys())

# Road connections (undirected)
roads = [
    ('Arad', 'Sibiu', 140), ('Arad', 'Timisoara', 118), ('Arad', 'Zerind', 75),
    ('Bucharest', 'Fagaras', 211), ('Bucharest', 'Giurgiu', 90), 
    ('Bucharest', 'Pitesti', 101), ('Bucharest', 'Urziceni', 85),
    ('Craiova', 'Drobeta', 120), ('Craiova', 'Pitesti', 138), 
    ('Craiova', 'Rimnicu Vilcea', 146),
    ('Drobeta', 'Mehadia', 75),
    ('Eforie', 'Hirsova', 86),
    ('Fagaras', 'Sibiu', 99),
    ('Hirsova', 'Urziceni', 98),
    ('Iasi', 'Neamt', 87), ('Iasi', 'Vaslui', 92),
    ('Lugoj', 'Mehadia', 70), ('Lugoj', 'Timisoara', 111),
    ('Oradea', 'Sibiu', 151), ('Oradea', 'Zerind', 71),
    ('Pitesti', 'Rimnicu Vilcea', 97),
    ('Rimnicu Vilcea', 'Sibiu', 80),
    ('Urziceni', 'Vaslui', 142),
]

# Build distance dictionary
distances = {}
for a, b, d in roads:
    distances[(a, b)] = d
    distances[(b, a)] = d

# ACO Parameters
class ACOParams:
    def __init__(self):
        self.num_ants = 30
        self.num_iterations = 100
        self.alpha = 1.0      # pheromone importance
        self.beta = 3.0       # heuristic importance
        self.evaporation = 0.3
        self.q = 100          # pheromone deposit factor
        self.init_pheromone = 1.0


class AntColonyOptimization:
    def __init__(self, params):
        self.params = params
        self.cities = cities
        self.num_cities = len(cities)
        self.city_to_idx = {city: i for i, city in enumerate(cities)}
        self.idx_to_city = {i: city for i, city in enumerate(cities)}
        
        # Initialize pheromone matrix
        self.pheromones = np.ones((self.num_cities, self.num_cities)) * params.init_pheromone
        np.fill_diagonal(self.pheromones, 0)
        
        # Heuristic matrix (1/distance)
        self.heuristic = np.zeros((self.num_cities, self.num_cities))
        for i in range(self.num_cities):
            for j in range(self.num_cities):
                if i != j:
                    city_i = self.idx_to_city[i]
                    city_j = self.idx_to_city[j]
                    dist = distances.get((city_i, city_j), float('inf'))
                    if dist != float('inf'):
                        self.heuristic[i][j] = 1.0 / dist
        
        # Tracking best solution
        self.best_tour = None
        self.best_length = float('inf')
        self.best_history = []
        self.avg_history = []
        
        # Visualization setup
        self.fig = None
        self.ax_map = None
        self.ax_conv = None
        self.graph = None
        self.pos = None
        
    def calculate_tour_length(self, tour):
        """Calculate total length of a tour"""
        length = 0
        for i in range(len(tour) - 1):
            city1 = tour[i]
            city2 = tour[i + 1]
            length += distances.get((city1, city2), float('inf'))
        return length
    
    def select_next_city(self, current_city, unvisited):
        """Select next city using probability based on pheromone and heuristic"""
        current_idx = self.city_to_idx[current_city]
        
        # Calculate probabilities
        probs = []
        cities_list = []
        
        for city in unvisited:
            city_idx = self.city_to_idx[city]
            if self.heuristic[current_idx][city_idx] > 0:
                pheromone = self.pheromones[current_idx][city_idx] ** self.params.alpha
                heuristic = self.heuristic[current_idx][city_idx] ** self.params.beta
                prob = pheromone * heuristic
                probs.append(prob)
                cities_list.append(city)
        
        if not probs or sum(probs) == 0:
            return random.choice(list(unvisited))
        
        # Normalize probabilities
        probs = np.array(probs) / sum(probs)
        
        # Select city
        return np.random.choice(cities_list, p=probs)
    
    def construct_solution(self, start_city=None):
        """Construct a tour for one ant"""
        if start_city is None:
            start_city = random.choice(self.cities)
        
        tour = [start_city]
        unvisited = set(self.cities) - {start_city}
        current_city = start_city
        
        while unvisited:
            next_city = self.select_next_city(current_city, unvisited)
            tour.append(next_city)
            unvisited.remove(next_city)
            current_city = next_city
        
        # Return to start to complete tour
        tour.append(start_city)
        return tour
    
    def update_pheromones(self, tours, lengths):
        """Update pheromone levels"""
        # Evaporation
        self.pheromones *= (1 - self.params.evaporation)
        
        # Deposit pheromones
        for tour, length in zip(tours, lengths):
            if length == float('inf'):
                continue
            
            deposit = self.params.q / length
            
            for i in range(len(tour) - 1):
                city1_idx = self.city_to_idx[tour[i]]
                city2_idx = self.city_to_idx[tour[i + 1]]
                self.pheromones[city1_idx][city2_idx] += deposit
                self.pheromones[city2_idx][city1_idx] += deposit
    
    def run(self, visualize=True):
        """Run the ACO algorithm"""
        print("Starting Ant Colony Optimization for Romania TSP...")
        print(f"Number of cities: {self.num_cities}")
        print(f"Number of ants: {self.params.num_ants}")
        print(f"Number of iterations: {self.params.num_iterations}")
        print("-" * 50)
        
        if visualize:
            self.setup_visualization()
        
        for iteration in range(self.params.num_iterations):
            # Construct tours for all ants
            tours = []
            lengths = []
            
            for _ in range(self.params.num_ants):
                tour = self.construct_solution()
                length = self.calculate_tour_length(tour)
                tours.append(tour)
                lengths.append(length)
                
                # Update best solution
                if length < self.best_length:
                    self.best_length = length
                    self.best_tour = tour
                    print(f"Iteration {iteration + 1}: New best length = {length:.2f}")
            
            # Update pheromones
            self.update_pheromones(tours, lengths)
            
            # Track history
            self.best_history.append(self.best_length)
            self.avg_history.append(np.mean(lengths))
            
            # Update visualization
            if visualize and (iteration + 1) % 5 == 0:
                self.update_visualization(iteration)
        
        print("-" * 50)
        print("Optimization Complete!")
        print(f"Best tour length: {self.best_length:.2f}")
        print(f"Best tour: {' -> '.join(self.best_tour)}")
        
        if visualize:
            self.show_final_result()
        
        return self.best_tour, self.best_length
    
    def setup_visualization(self):
        """Setup the visualization"""
        self.fig = plt.figure(figsize=(15, 6))
        
        # Left subplot - Map
        self.ax_map = self.fig.add_subplot(121)
        
        # Create graph
        self.graph = nx.Graph()
        for city in cities:
            self.graph.add_node(city, pos=cities_coords[city])
        
        # Add edges
        for a, b, d in roads:
            self.graph.add_edge(a, b, weight=d)
        
        # Get positions
        self.pos = nx.get_node_attributes(self.graph, 'pos')
        
        # Right subplot - Convergence
        self.ax_conv = self.fig.add_subplot(122)
        
        plt.ion()
        plt.show()
    
    def update_visualization(self, iteration):
        """Update the visualization"""
        if not self.fig:
            return
        
        self.ax_map.clear()
        self.ax_conv.clear()
        
        # Draw the graph
        nx.draw_networkx_nodes(self.graph, self.pos, node_size=200, 
                              node_color='lightblue', ax=self.ax_map)
        nx.draw_networkx_labels(self.graph, self.pos, font_size=8, ax=self.ax_map)
        
        # Draw edges
        nx.draw_networkx_edges(self.graph, self.pos, edge_color='gray', 
                              width=1, alpha=0.5, ax=self.ax_map)
        
        # Draw best tour if exists
        if self.best_tour:
            tour_edges = [(self.best_tour[i], self.best_tour[i + 1]) 
                         for i in range(len(self.best_tour) - 1)]
            nx.draw_networkx_edges(self.graph, self.pos, edgelist=tour_edges,
                                  edge_color='red', width=2, ax=self.ax_map)
        
        self.ax_map.set_title(f"Romania Map - Best Tour (Length: {self.best_length:.1f})")
        self.ax_map.axis('off')
        
        # Plot convergence
        iterations = range(1, len(self.best_history) + 1)
        self.ax_conv.plot(iterations, self.best_history, 'b-', label='Best Length')
        self.ax_conv.plot(iterations, self.avg_history, 'g--', label='Average Length')
        self.ax_conv.set_xlabel('Iteration')
        self.ax_conv.set_ylabel('Tour Length')
        self.ax_conv.set_title('Convergence Plot')
        self.ax_conv.legend()
        self.ax_conv.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.pause(0.1)
    
    def show_final_result(self):
        """Show final result"""
        plt.ioff()
        
        # Create final figure
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        
        # 1. Best tour on map
        nx.draw_networkx_nodes(self.graph, self.pos, node_size=300, 
                              node_color='lightblue', ax=ax1)
        nx.draw_networkx_labels(self.graph, self.pos, font_size=9, ax=ax1)
        nx.draw_networkx_edges(self.graph, self.pos, edge_color='gray', 
                              width=1, alpha=0.5, ax=ax1)
        
        # Draw best tour
        if self.best_tour:
            tour_edges = [(self.best_tour[i], self.best_tour[i + 1]) 
                         for i in range(len(self.best_tour) - 1)]
            nx.draw_networkx_edges(self.graph, self.pos, edgelist=tour_edges,
                                  edge_color='red', width=3, ax=ax1)
        
        ax1.set_title(f"Best ACO Tour\nLength: {self.best_length:.1f}")
        ax1.axis('off')
        
        # 2. Convergence plot
        iterations = range(1, len(self.best_history) + 1)
        ax2.plot(iterations, self.best_history, 'b-', linewidth=2, label='Best')
        ax2.plot(iterations, self.avg_history, 'g--', linewidth=2, label='Average')
        ax2.set_xlabel('Iteration')
        ax2.set_ylabel('Tour Length')
        ax2.set_title('Convergence History')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Pheromone heatmap
        pheromone_avg = np.mean(self.pheromones, axis=1)
        city_names = [city[:10] for city in cities]  # Truncate names
        
        ax3.bar(range(len(city_names)), pheromone_avg)
        ax3.set_xticks(range(len(city_names)))
        ax3.set_xticklabels(city_names, rotation=45, ha='right')
        ax3.set_xlabel('Cities')
        ax3.set_ylabel('Average Pheromone Level')
        ax3.set_title('Pheromone Distribution')
        ax3.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.show()


class ParticleSwarmOptimization:
    """Alternative swarm algorithm - Particle Swarm Optimization"""
    
    def __init__(self, num_particles=50, num_iterations=100):
        self.num_particles = num_particles
        self.num_iterations = num_iterations
        self.cities = cities
        self.num_cities = len(cities)
        
        # PSO parameters
        self.w = 0.5  # inertia weight
        self.c1 = 1.5  # cognitive parameter
        self.c2 = 1.5  # social parameter
        
        # Tracking
        self.best_position = None
        self.best_cost = float('inf')
        self.best_history = []
        
    def initialize_particles(self):
        """Initialize particles with random permutations"""
        particles = []
        velocities = []
        
        for _ in range(self.num_particles):
            # Random permutation of cities
            particle = random.sample(self.cities, self.num_cities)
            particles.append(particle)
            
            # Random velocity (swap probability)
            velocity = np.random.rand(self.num_cities, self.num_cities)
            velocities.append(velocity)
        
        return particles, velocities
    
    def calculate_cost(self, tour):
        """Calculate tour length"""
        length = 0
        for i in range(len(tour) - 1):
            length += distances.get((tour[i], tour[i + 1]), float('inf'))
        # Add return to start
        length += distances.get((tour[-1], tour[0]), float('inf'))
        return length
    
    def apply_velocity(self, particle, velocity):
        """Apply velocity (swap operations) to particle"""
        new_particle = particle.copy()
        
        # Convert velocity to swap operations
        for i in range(self.num_cities):
            for j in range(i + 1, self.num_cities):
                if velocity[i][j] > 0.5:  # Threshold for swapping
                    # Swap cities
                    new_particle[i], new_particle[j] = new_particle[j], new_particle[i]
        
        return new_particle
    
    def run(self):
        """Run PSO algorithm"""
        print("\n" + "="*50)
        print("Particle Swarm Optimization for Romania TSP")
        print("="*50)
        
        # Initialize
        particles, velocities = self.initialize_particles()
        
        # Personal best positions
        pbest_positions = particles.copy()
        pbest_costs = [self.calculate_cost(p) for p in particles]
        
        # Global best
        gbest_idx = np.argmin(pbest_costs)
        gbest_position = pbest_positions[gbest_idx].copy()
        gbest_cost = pbest_costs[gbest_idx]
        
        for iteration in range(self.num_iterations):
            for i in range(self.num_particles):
                # Update velocity
                r1, r2 = np.random.rand(), np.random.rand()
                
                # Cognitive component (attraction to personal best)
                cognitive = np.zeros((self.num_cities, self.num_cities))
                if particles[i] != pbest_positions[i]:
                    # Find positions to swap to get to pbest
                    for idx, city in enumerate(particles[i]):
                        target_idx = pbest_positions[i].index(city)
                        if idx != target_idx:
                            cognitive[idx][target_idx] += self.c1 * r1
                
                # Social component (attraction to global best)
                social = np.zeros((self.num_cities, self.num_cities))
                for idx, city in enumerate(particles[i]):
                    target_idx = gbest_position.index(city)
                    if idx != target_idx:
                        social[idx][target_idx] += self.c2 * r2
                
                # Update velocity
                velocities[i] = self.w * velocities[i] + cognitive + social
                
                # Apply velocity to get new position
                new_particle = self.apply_velocity(particles[i], velocities[i])
                new_cost = self.calculate_cost(new_particle)
                
                # Update personal best
                if new_cost < pbest_costs[i]:
                    pbest_positions[i] = new_particle.copy()
                    pbest_costs[i] = new_cost
                
                # Update particle
                particles[i] = new_particle
            
            # Update global best
            current_best_idx = np.argmin(pbest_costs)
            if pbest_costs[current_best_idx] < gbest_cost:
                gbest_cost = pbest_costs[current_best_idx]
                gbest_position = pbest_positions[current_best_idx].copy()
                print(f"Iteration {iteration + 1}: New best = {gbest_cost:.2f}")
            
            self.best_history.append(gbest_cost)
        
        self.best_position = gbest_position
        self.best_cost = gbest_cost
        
        print("-"*50)
        print(f"PSO Best tour length: {self.best_cost:.2f}")
        print(f"PSO Best tour: {' -> '.join(self.best_position + [self.best_position[0]])}")
        
        return self.best_position, self.best_cost


class BeeColonyOptimization:
    """Artificial Bee Colony algorithm"""
    
    def __init__(self, num_bees=50, num_iterations=100):
        self.num_bees = num_bees
        self.num_iterations = num_iterations
        self.num_cities = len(cities)
        self.limit = 20  # abandonment limit
        
    def calculate_cost(self, tour):
        """Calculate tour length"""
        length = 0
        for i in range(len(tour) - 1):
            length += distances.get((tour[i], tour[i + 1]), float('inf'))
        length += distances.get((tour[-1], tour[0]), float('inf'))
        return length
    
    def generate_neighbor(self, solution):
        """Generate neighbor solution using 2-opt swap"""
        neighbor = solution.copy()
        i, j = sorted(random.sample(range(len(solution)), 2))
        neighbor[i:j+1] = reversed(neighbor[i:j+1])
        return neighbor
    
    def run(self):
        """Run ABC algorithm"""
        print("\n" + "="*50)
        print("Artificial Bee Colony for Romania TSP")
        print("="*50)
        
        # Initialize food sources
        foods = [random.sample(self.cities, self.num_cities) for _ in range(self.num_bees)]
        costs = [self.calculate_cost(f) for f in foods]
        trials = [0] * self.num_bees
        
        best_idx = np.argmin(costs)
        best_food = foods[best_idx].copy()
        best_cost = costs[best_idx]
        
        for iteration in range(self.num_iterations):
            # Employed bees phase
            for i in range(self.num_bees):
                # Generate neighbor
                neighbor = self.generate_neighbor(foods[i])
                neighbor_cost = self.calculate_cost(neighbor)
                
                # Greedy selection
                if neighbor_cost < costs[i]:
                    foods[i] = neighbor
                    costs[i] = neighbor_cost
                    trials[i] = 0
                else:
                    trials[i] += 1
            
            # Onlooker bees phase
            # Calculate probabilities based on fitness
            min_cost = min(costs)
            if min_cost > 0:
                fitness = [1.0 / (c - min_cost + 1) for c in costs]
                probs = fitness / np.sum(fitness)
                
                for _ in range(self.num_bees):
                    # Select food source based on probability
                    selected = np.random.choice(range(self.num_bees), p=probs)
                    
                    # Generate neighbor
                    neighbor = self.generate_neighbor(foods[selected])
                    neighbor_cost = self.calculate_cost(neighbor)
                    
                    # Greedy selection
                    if neighbor_cost < costs[selected]:
                        foods[selected] = neighbor
                        costs[selected] = neighbor_cost
                        trials[selected] = 0
                    else:
                        trials[selected] += 1
            
            # Scout bees phase
            for i in range(self.num_bees):
                if trials[i] > self.limit:
                    # Abandon food source and find new random one
                    foods[i] = random.sample(self.cities, self.num_cities)
                    costs[i] = self.calculate_cost(foods[i])
                    trials[i] = 0
                    print(f"  Scout bee found new food source at iteration {iteration + 1}")
            
            # Update best solution
            current_best_idx = np.argmin(costs)
            if costs[current_best_idx] < best_cost:
                best_cost = costs[current_best_idx]
                best_food = foods[current_best_idx].copy()
                print(f"Iteration {iteration + 1}: New best = {best_cost:.2f}")
        
        print("-"*50)
        print(f"ABC Best tour length: {best_cost:.2f}")
        print(f"ABC Best tour: {' -> '.join(best_food + [best_food[0]])}")
        
        return best_food, best_cost


def compare_algorithms():
    """Compare different swarm algorithms"""
    
    print("\n" + "="*70)
    print("SWARM INTELLIGENCE ALGORITHMS COMPARISON")
    print("="*70)
    print("\nProblem: Traveling Salesman Problem (Romania Cities)")
    print(f"Number of cities: {len(cities)}")
    print("="*70)
    
    # Run ACO
    print("\n1. ANT COLONY OPTIMIZATION")
    print("-"*40)
    aco_params = ACOParams()
    aco_params.num_ants = 30
    aco_params.num_iterations = 50  # Reduced for faster comparison
    aco = AntColonyOptimization(aco_params)
    aco_tour, aco_length = aco.run(visualize=False)
    
    # Run PSO
    print("\n2. PARTICLE SWARM OPTIMIZATION")
    print("-"*40)
    pso = ParticleSwarmOptimization(num_particles=30, num_iterations=50)
    pso_tour, pso_length = pso.run()
    
    # Run ABC
    print("\n3. ARTIFICIAL BEE COLONY")
    print("-"*40)
    abc = BeeColonyOptimization(num_bees=30, num_iterations=50)
    abc_tour, abc_length = abc.run()
    
    # Comparison results
    print("\n" + "="*70)
    print("ALGORITHM COMPARISON RESULTS")
    print("="*70)
    print(f"{'Algorithm':<25} {'Best Length':<15} {'Improvement':<15}")
    print("-"*70)
    
    # Find best among all
    lengths = [aco_length, pso_length, abc_length]
    best_idx = np.argmin(lengths)
    best_length = min(lengths)
    
    algorithms = ['ACO', 'PSO', 'ABC']
    
    for i, (name, length) in enumerate(zip(algorithms, lengths)):
        improvement = ((length - best_length) / best_length) * 100 if best_length > 0 else 0
        if i == best_idx:
            # Fix: Don't use backslash in f-string
            print(f"{name:<25} {length:<15.2f} {improvement:<15.1f}% (BEST)")
        else:
            print(f"{name:<25} {length:<15.2f} {improvement:<15.1f}%")
    
    print("="*70)
    
    # Create comparison visualization
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    
    # Plot ACO convergence
    if hasattr(aco, 'best_history') and aco.best_history:
        ax1.plot(range(1, len(aco.best_history) + 1), aco.best_history, 'r-', linewidth=2, label='ACO')
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Tour Length')
    ax1.set_title(f'ACO Convergence\nBest: {aco_length:.1f}')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot PSO convergence
    if hasattr(pso, 'best_history') and pso.best_history:
        ax2.plot(range(1, len(pso.best_history) + 1), pso.best_history, 'g-', linewidth=2, label='PSO')
    ax2.set_xlabel('Iteration')
    ax2.set_title(f'PSO Convergence\nBest: {pso_length:.1f}')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Bar chart comparison
    algorithms_display = ['ACO', 'PSO', 'ABC']
    lengths_display = [aco_length, pso_length, abc_length]
    colors_display = ['red', 'green', 'blue']
    bars = ax3.bar(algorithms_display, lengths_display, color=colors_display, alpha=0.7)
    
    # Add value labels on bars
    for bar, length in zip(bars, lengths_display):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{length:.0f}', ha='center', va='bottom')
    
    ax3.set_ylabel('Tour Length')
    ax3.set_title('Algorithm Comparison')
    ax3.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('Swarm Intelligence Algorithms for TSP', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.show()
    
    return {
        'ACO': (aco_tour, aco_length),
        'PSO': (pso_tour, pso_length),
        'ABC': (abc_tour, abc_length)
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SWARM INTELLIGENCE FOR OPTIMIZATION")
    print("="*70)
    print("\nChoose an option:")
    print("1. Run Ant Colony Optimization (ACO) with visualization")
    print("2. Run Particle Swarm Optimization (PSO)")
    print("3. Run Artificial Bee Colony (ABC)")
    print("4. Compare all algorithms")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        params = ACOParams()
        params.num_ants = 30
        params.num_iterations = 100
        aco = AntColonyOptimization(params)
        aco.run(visualize=True)
        
    elif choice == '2':
        pso = ParticleSwarmOptimization(num_particles=30, num_iterations=100)
        pso.run()
        
    elif choice == '3':
        abc = BeeColonyOptimization(num_bees=30, num_iterations=100)
        abc.run()
        
    elif choice == '4':
        results = compare_algorithms()
        
    else:
        print("Invalid choice. Running ACO as default...")
        params = ACOParams()
        aco = AntColonyOptimization(params)
        aco.run(visualize=True)