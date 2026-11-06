"""Three explainable, offline chess AI levels."""
import random
from engine import VALUES

class ChessAI:
    """A small offline opponent: random, greedy, or short search."""

    def __init__(self, difficulty='medium'):
        self.difficulty = difficulty

    def evaluate(self, game, color):
        score = 0
        for row in game.board.cells:
            for p in row:
                if p:
                    score += (1 if p.color == color else -1) * VALUES[p.kind]
        state = game.status()
        if state == 'checkmate':
            return -10000 if game.turn == color else 10000
        if state not in ('playing', 'check'):
            return 0
        return score

    def choose(self, game):
        """Choose one legal move from the current position."""
        moves = list(game.possible_moves())
        if not moves:
            return None
        color = game.turn
        if self.difficulty == 'easy':
            return random.choice(moves)
        if self.difficulty == 'medium':
            return max(moves, key=lambda m: self._one(game, m, color) + random.random() * 0.16)
        best = None
        bestscore = -float('inf')
        alpha = -float('inf')
        ordered = sorted(moves, key=lambda m: self._one(game, m, color), reverse=True)
        for move in ordered:
            game.move(*move)
            score = -self._negamax(game, 1, -float('inf'), -alpha, color)
            game.undo()
            if score > bestscore:
                bestscore = score
                best = move
            alpha = max(alpha, score)
        return best

    def _one(self, game, move, color):
        r, c, tr, tc = move
        victim = game.board.cells[tr][tc]
        score = VALUES[victim.kind] if victim else 0
        if game.board.cells[r][c].kind == 'P' and tr in (0, 7):
            score += 8
        game.move(*move)
        score += self.evaluate(game, color) * 0.7
        game.undo()
        return score

    def _negamax(self, game, depth, alpha, beta, root):
        if depth == 0 or game.finished:
            return self.evaluate(game, root) * (1 if game.turn == root else -1)
        best = -float('inf')
        for move in game.possible_moves():
            game.move(*move)
            score = -self._negamax(game, depth - 1, -beta, -alpha, root)
            game.undo()
            best = max(best, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return best if best != -float('inf') else self.evaluate(game, root)
