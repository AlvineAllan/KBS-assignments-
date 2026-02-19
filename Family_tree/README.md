# KBS_assignment_5_Family_Trees
The program stores basic family facts in simple data structures: sets for genders and spouses, and a dictionary mapping each parent to their list of children.
Basic relations like father, mother, son, daughter, husband, and wife are checked directly by combining gender information with parent-child or spouse facts.
The ancestor relation is computed recursively: it checks if there is a chain of parent links from the potential ancestor down to the descendant, using a visited set to avoid loops.
The relative predicate returns true if two people are the same (false), married (true), or share at least one common ancestor (determined by comparing their ancestor sets).
