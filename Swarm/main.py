import random
import math

# Romania cities and distances 
cities = [
    'Arad', 'Bucharest', 'Craiova', 'Drobeta', 'Eforie', 'Fagaras', 'Giurgiu',
    'Hirsova', 'Iasi', 'Lugoj', 'Mehadia', 'Neamt', 'Oradea', 'Pitesti',
    'Rimnicu Vilcea', 'Sibiu', 'Timisoara', 'Urziceni', 'Vaslui', 'Zerind'
]

# sparse road graph 
base_distances = {
    ('Arad', 'Sibiu'): 140, ('Arad', 'Timisoara'): 118, ('Arad', 'Zerind'): 75,
    ('Bucharest', 'Fagaras'): 211, ('Bucharest', 'Giurgiu'): 90, ('Bucharest', 'Pitesti'): 101, ('Bucharest', 'Urziceni'): 85,
    ('Craiova', 'Drobeta'): 120, ('Craiova', 'Pitesti'): 138, ('Craiova', 'Rimnicu Vilcea'): 146,
    ('Drobeta', 'Mehadia'): 75,
    ('Eforie', 'Hirsova'): 86,
    ('Fagaras', 'Sibiu'): 99,
    ('Hirsova', 'Urziceni'): 98,
    ('Iasi', 'Neamt'): 87, ('Iasi', 'Vaslui'): 92,
    ('Lugoj', 'Mehadia'): 70, ('Lugoj', 'Timisoara'): 111,
    ('Oradea', 'Sibiu'): 151, ('Oradea', 'Zerind'): 71,
    ('Pitesti', 'Rimnicu Vilcea'): 97,
    ('Rimnicu Vilcea', 'Sibiu'): 80,
    ('Urziceni', 'Vaslui'): 142,
}

# ACO parameters
NUM_ANTS = 20
NUM_ITERATIONS = 200
ALPHA = 1.0        # pheromone importance
BETA = 2.0         # heuristic (1/distance) importance
EVAPORATION = 0.5  # pheromone evaporation rate
PHEROMONE_INIT = 1.0 / len(cities)

# Build complete metric closure so ants can traverse a complete graph
INF = math.inf
idx = {c: i for i, c in enumerate(cities)}
n = len(cities)
dist_matrix = [[INF] * n for _ in range(n)]
for i in range(n):
    dist_matrix[i][i] = 0.0

# set given undirected edges
for (a, b), d in list(base_distances.items()):
    if a in idx and b in idx:
        i, j = idx[a], idx[b]
        dist_matrix[i][j] = min(dist_matrix[i][j], d)
        dist_matrix[j][i] = min(dist_matrix[j][i], d)

# Floyd–Warshall to compute shortest paths between all city pairs
for k in range(n):
    for i in range(n):
        if dist_matrix[i][k] == INF:
            continue
        for j in range(n):
            alt = dist_matrix[i][k] + dist_matrix[k][j]
            if alt < dist_matrix[i][j]:
                dist_matrix[i][j] = alt

# overwrite distances with metric closure
distances = {}
for i, a in enumerate(cities):
    for j, b in enumerate(cities):
        if i != j and dist_matrix[i][j] < INF:
            distances[(a, b)] = dist_matrix[i][j]

# initialize pheromones for all ordered pairs 
pheromones = {
    (a, b): PHEROMONE_INIT
    for a in cities for b in cities
    if a != b
}

# reproducible during development
random.seed(0)


def get_distance(a, b):
    return distances.get((a, b), math.inf)


def ant_tour(start):
    """Construct a single ant tour starting from `start`. Returns tour list including return to start, or None if blocked."""
    tour = [start]
    unvisited = set(cities) - {start}
    current = start

    while unvisited:
        weights = []
        denom = 0.0
        for nxt in unvisited:
            key = (current, nxt)
            if key in pheromones:
                dist = get_distance(current, nxt)
                if dist < math.inf and dist > 0:
                    weight = (pheromones[key] ** ALPHA) * ((1.0 / dist) ** BETA)
                    weights.append((nxt, weight))
                    denom += weight
        if denom == 0.0 or not weights:
            return None  # dead end: cannot complete tour from this path
        cities_list, probs = zip(*[(c, w / denom) for c, w in weights])
        next_city = random.choices(cities_list, probs)[0]
        tour.append(next_city)
        unvisited.remove(next_city)
        current = next_city

    # close the tour back to start 
    if get_distance(tour[-1], tour[0]) < math.inf:
        tour.append(tour[0])
        return tour
    return None


def tour_length(tour):
    if not tour:
        return math.inf
    return sum(get_distance(tour[i], tour[i + 1]) for i in range(len(tour) - 1))


def update_pheromones(tours):
    """Evaporate and deposit pheromones based on provided tours."""
    # evaporation
    for key in list(pheromones.keys()):
        pheromones[key] *= (1.0 - EVAPORATION)
    # deposition (shorter tours deposit more)
    for tour in tours:
        if not tour:
            continue
        L = tour_length(tour)
        if L == 0 or L == math.inf:
            continue
        deposit = 1.0 / L
        for i in range(len(tour) - 1):
            key = (tour[i], tour[i + 1])
            if key in pheromones:
                pheromones[key] += deposit


def run():
    best_tour = None
    best_length = math.inf

    for iteration in range(1, NUM_ITERATIONS + 1):
        ants = [ant_tour(random.choice(cities)) for _ in range(NUM_ANTS)]
        ants = [t for t in ants if t]
        if ants:
            update_pheromones(ants)
            for t in ants:
                L = tour_length(t)
                if L < best_length:
                    best_length = L
                    best_tour = t

    if best_tour:
        print("Best Tour:", best_tour)
        print("Length:", best_length)
    else:
        print("No feasible tour found.")


if __name__ == "__main__":
    run()
