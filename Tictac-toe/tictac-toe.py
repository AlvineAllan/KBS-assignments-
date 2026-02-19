# Import required modules
import math
import copy

class TicTacToe:
    """
    Class to represent the Tic-Tac-Toe game state and logic.
    """
    def __init__(self, board=None, player='X'):
        """
        Initialize the board and set the current player.
        """
        self.board = board or [['' for _ in range(3)] for _ in range(3)]
        self.player = player

    def get_moves(self):
        """
        Return a list of all possible moves (empty cells).
        """
        return [(i, j) for i in range(3) for j in range(3) if self.board[i][j] == '']

    def make_move(self, move):
        """
        Return a new TicTacToe object with the move applied.
        """
        new_board = copy.deepcopy(self.board)
        new_board[move[0]][move[1]] = self.player
        return TicTacToe(new_board, 'O' if self.player == 'X' else 'X')

    def winner(self):
        """
        Check if there is a winner. Returns 'X', 'O', or None.
        """
        lines = [self.board[i] for i in range(3)] + \
                [[self.board[j][i] for j in range(3)] for i in range(3)] + \
                [[self.board[i][i] for i in range(3)], [self.board[i][2 - i] for i in range(3)]]
        for line in lines:
            if line[0] == line[1] == line[2] != '':
                return line[0]
        return None

    def is_terminal(self):
        """
        Check if the game is over (win or draw).
        """
        return self.winner() is not None or not self.get_moves()

    def utility(self):
        """
        Return the utility value: 1 for X win, -1 for O win, 0 otherwise.
        """
        win = self.winner()
        if win == 'X': return 1
        if win == 'O': return -1
        return 0

def minimax(game):
    """
    Minimax algorithm to choose the best move for the current player.
    Returns (best_value, best_move).
    """
    if game.is_terminal():
        return game.utility(), None
    best_value = -math.inf if game.player == 'X' else math.inf
    best_move = None
    for move in game.get_moves():
        child = game.make_move(move)
        value, _ = minimax(child)
        if (game.player == 'X' and value > best_value) or (game.player == 'O' and value < best_value):
            best_value = value
            best_move = move
    return best_value, best_move

def alpha_beta(game, alpha=-math.inf, beta=math.inf):
    """
    Alpha-Beta pruning algorithm to choose the best move efficiently.
    Returns (best_value, best_move).
    """
    if game.is_terminal():
        return game.utility(), None
    best_value = -math.inf if game.player == 'X' else math.inf
    best_move = None
    for move in game.get_moves():
        child = game.make_move(move)
        value, _ = alpha_beta(child, alpha, beta)
        if game.player == 'X':
            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, best_value)
        else:
            if value < best_value:
                best_value = value
                best_move = move
            beta = min(beta, best_value)
        if alpha >= beta:
            break
    return best_value, best_move

# Test on empty board
# Create a new game and print the best moves for both algorithms
game = TicTacToe()
print("Minimax:", minimax(game)[1])  # e.g., (1,1)
print("Alpha-Beta:", alpha_beta(game)[1])