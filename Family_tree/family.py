"""
Simple Family Tree Knowledge Base
A small genealogy example with basic facts and recursive relations.
"""

# ────────────────────────────────────────────────
# FACTS
# ────────────────────────────────────────────────

males = {"Jack", "John", "Joe", "Mark", "Fred"}
females = {"Nancy", "Mary", "Linda", "Liz"}

all_people = males | females

# Spouses (both directions for simplicity)
spouses = {
    ("Joe", "Mary"), ("Mary", "Joe"),
    ("John", "Nancy"), ("Nancy", "John")
}

# Parent → list of children (dictionary)
parent_of = {
    "Jack":  ["Nancy", "Linda"],
    "John":  ["Mark"],
    "Nancy": ["Mark"],
    "Joe":   ["Fred"],
    "Linda": ["Liz"]
}

# ────────────────────────────────────────────────
# BASIC PREDICATES
# ────────────────────────────────────────────────

def male(p):
    return p in males

def female(p):
    return p in females

def spouse(a, b):
    return (a, b) in spouses

def husband(h, w):
    return spouse(h, w) and male(h)

def wife(w, h):
    return spouse(w, h) and female(w)

def parent(p, c):
    return c in parent_of.get(p, [])

def child(c, p):
    return parent(p, c)

def father(f, c):
    return parent(f, c) and male(f)

def mother(m, c):
    return parent(m, c) and female(m)

def son(s, p):
    return child(s, p) and male(s)

def daughter(d, p):
    return child(d, p) and female(d)

# ────────────────────────────────────────────────
# RECURSIVE RELATIONS
# ────────────────────────────────────────────────

def ancestor(anc, desc, visited=None):
    """
    Returns True if 'anc' is an ancestor of 'desc' (anc → ... → desc)
    """
    if visited is None:
        visited = set()

    if anc == desc or anc in visited:
        return False

    visited.add(anc)

    children = parent_of.get(anc, [])
    if desc in children:
        return True

    for child in children:
        if ancestor(child, desc, visited):
            return True

    return False


def descendant(desc, anc):
    """Returns True if 'desc' is a descendant of 'anc'"""
    return ancestor(anc, desc)


def relative(a, b):
    """
    Returns True if a and b are relatives:
    - they are the same person               → False
    - they are married                       → True
    - they share at least one common ancestor → True
    """
    if a == b:
        return False

    if spouse(a, b):
        return True

    anc_a = {p for p in all_people if ancestor(p, a)}
    anc_b = {p for p in all_people if ancestor(p, b)}

    return bool(anc_a & anc_b)


# ────────────────────────────────────────────────
# QUERY DISPLAY HELPER
# ────────────────────────────────────────────────

def show(query_str, result):
    print(f"{query_str:<45} -> {result}")


# ────────────────────────────────────────────────
# EXAMPLE QUERIES
# ────────────────────────────────────────────────

if __name__ == "__main__":
    print("Family Tree Queries")
    print("--------------------------------------------------")          # <-- safe ASCII only

    show("ancestor(Jack, Fred)",      ancestor("Jack", "Fred"))
    show("ancestor(Jack, Liz)",       ancestor("Jack", "Liz"))
    show("ancestor(Jack, Mark)",      ancestor("Jack", "Mark"))
    show("ancestor(Joe, Fred)",       ancestor("Joe", "Fred"))
    show("ancestor(Linda, Liz)",      ancestor("Linda", "Liz"))
    show("ancestor(Nancy, Fred)",     ancestor("Nancy", "Fred"))

    print()
    show("relative(Liz, Joe)",        relative("Liz", "Joe"))
    show("relative(Nancy, Fred)",     relative("Nancy", "Fred"))
    show("relative(Mark, Liz)",       relative("Mark", "Liz"))
    show("relative(John, Nancy)",     relative("John", "Nancy"))
    show("relative(Joe, Mary)",       relative("Joe", "Mary"))

    print()
    show("father(Jack, Nancy)",       father("Jack", "Nancy"))
    show("mother(Nancy, Mark)",       mother("Nancy", "Mark"))
    show("daughter(Liz, Linda)",      daughter("Liz", "Linda"))
    show("son(Fred, Joe)",            son("Fred", "Joe"))
    show("husband(John, Nancy)",      husband("John", "Nancy"))