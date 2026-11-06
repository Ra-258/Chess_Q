"""Self-contained chess rules. Board coordinates: row 0 is rank 8."""
from copy import deepcopy
from dataclasses import dataclass
VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

@dataclass
class Piece:
    color: str
    kind: str
    moved: bool = False

class Board:
    """The 8 × 8 squares and piece attack patterns."""

    def __init__(self):
        self.cells = [[None] * 8 for _ in range(8)]
        for c, k in enumerate('RNBQKBNR'):
            self.cells[0][c] = Piece('b', k)
            self.cells[7][c] = Piece('w', k)
            self.cells[1][c] = Piece('b', 'P')
            self.cells[6][c] = Piece('w', 'P')

    @staticmethod
    def inside(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def attacks(self, r, c, tr, tc):
        p = self.cells[r][c]
        if p is None or (r, c) == (tr, tc):
            return False
        dr, dc = (tr - r, tc - c)
        if p.kind == 'P':
            return dr == (-1 if p.color == 'w' else 1) and abs(dc) == 1
        if p.kind == 'N':
            return (abs(dr), abs(dc)) in ((1, 2), (2, 1))
        if p.kind == 'K':
            return max(abs(dr), abs(dc)) == 1
        straight = dr == 0 or dc == 0
        diagonal = abs(dr) == abs(dc)
        if not (p.kind == 'R' and straight or (p.kind == 'B' and diagonal) or (p.kind == 'Q' and (straight or diagonal))):
            return False
        sr = (dr > 0) - (dr < 0)
        sc = (dc > 0) - (dc < 0)
        rr, cc = (r + sr, c + sc)
        while (rr, cc) != (tr, tc):
            if self.cells[rr][cc]:
                return False
            rr += sr
            cc += sc
        return True

    def threatened(self, r, c, by):
        return any((p and p.color == by and self.attacks(i, j, r, c) for i, row in enumerate(self.cells) for j, p in enumerate(row)))

    def check(self, color):
        for r, row in enumerate(self.cells):
            for c, p in enumerate(row):
                if p and p.kind == 'K' and (p.color == color):
                    return self.threatened(r, c, 'b' if color == 'w' else 'w')
        return True

class ChessGame:
    """Keep track of legal moves, turns, checks and game results."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.board = Board()
        self.turn = 'w'
        self.en_passant = None
        self.history = []
        self.moves = []
        self.events = []
        self.finished = False
        self.halfmove = 0
        self.fullmove = 1
        self.last_move = None
        self.position_counts = {}
        self._record_position()

    def key(self):
        board = tuple((tuple(((p.color, p.kind) if p else None for p in row)) for row in self.board.cells))
        rights = []
        for color, row in (('w', 7), ('b', 0)):
            king = self.board.cells[row][4]
            if king and king.kind == 'K' and (king.color == color) and (not king.moved):
                for c in (0, 7):
                    rook = self.board.cells[row][c]
                    if rook and rook.kind == 'R' and (rook.color == color) and (not rook.moved):
                        rights.append((color, c))
        ep = None
        if self.en_passant:
            er, ec = self.en_passant
            pr = er + (1 if self.turn == 'w' else -1)
            if any((0 <= cc < 8 and 0 <= pr < 8 and (p := self.board.cells[pr][cc]) and (p.color == self.turn) and (p.kind == 'P') for cc in (ec - 1, ec + 1))):
                ep = self.en_passant
        return (board, self.turn, tuple(rights), ep)

    def _record_position(self):
        k = self.key()
        self.position_counts[k] = self.position_counts.get(k, 0) + 1

    def pseudo(self, r, c, tr, tc):
        b = self.board
        if not b.inside(r, c) or not b.inside(tr, tc) or (r, c) == (tr, tc):
            return False
        p = b.cells[r][c]
        if not p:
            return False
        target = b.cells[tr][tc]
        if target and (target.color == p.color or target.kind == 'K'):
            return False
        dr, dc = (tr - r, tc - c)
        if p.kind == 'P':
            d = -1 if p.color == 'w' else 1
            if dc == 0 and (not target):
                return dr == d or (dr == 2 * d and r == (6 if p.color == 'w' else 1) and (not b.cells[r + d][c]))
            if abs(dc) == 1 and dr == d:
                other = b.cells[r][tc]
                return bool(target) or (self.en_passant == (tr, tc) and other is not None and (other.kind == 'P') and (other.color != p.color))
            return False
        if p.kind == 'K' and dr == 0 and (abs(dc) == 2):
            rook_c = 7 if dc > 0 else 0
            rook = b.cells[r][rook_c]
            enemy = 'b' if p.color == 'w' else 'w'
            if c != 4 or r != (7 if p.color == 'w' else 0) or p.moved or (not rook) or (rook.kind != 'R') or (rook.color != p.color) or rook.moved or b.check(p.color):
                return False
            step = 1 if dc > 0 else -1
            return not any((b.cells[r][j] for j in range(c + step, rook_c, step))) and (not b.threatened(r, c + step, enemy)) and (not b.threatened(tr, tc, enemy))
        return b.attacks(r, c, tr, tc)

    def apply(self, r, c, tr, tc, promotion='Q'):
        b = self.board
        p = b.cells[r][c]
        old_ep = self.en_passant
        self.en_passant = None
        captured = b.cells[tr][tc]
        if p.kind == 'P' and tc != c and (captured is None) and (old_ep == (tr, tc)):
            captured = b.cells[r][tc]
            b.cells[r][tc] = None
        if p.kind == 'K' and abs(tc - c) == 2:
            rc = 7 if tc > c else 0
            to = tc - 1 if tc > c else tc + 1
            b.cells[r][to] = b.cells[r][rc]
            b.cells[r][rc] = None
            b.cells[r][to].moved = True
        b.cells[tr][tc] = p
        b.cells[r][c] = None
        p.moved = True
        if p.kind == 'P':
            if abs(tr - r) == 2:
                self.en_passant = ((r + tr) // 2, c)
            if tr in (0, 7):
                p.kind = promotion
        return captured

    def legal(self, r, c, tr, tc):
        """Test a move without leaving our own king in check."""
        p = self.board.cells[r][c] if self.board.inside(r, c) else None
        if not p or p.color != self.turn or (not self.pseudo(r, c, tr, tc)):
            return False
        saved = (self.board, self.en_passant)
        self.board = deepcopy(self.board)
        try:
            self.apply(r, c, tr, tc)
            return not self.board.check(self.turn)
        finally:
            self.board, self.en_passant = saved

    def possible_moves(self):
        """Yield every legal move for the player whose turn it is."""
        for r, row in enumerate(self.board.cells):
            for c, p in enumerate(row):
                if p and p.color == self.turn:
                    for tr in range(8):
                        for tc in range(8):
                            if self.legal(r, c, tr, tc):
                                yield (r, c, tr, tc)

    def status(self):
        if not any(self.possible_moves()):
            return 'checkmate' if self.board.check(self.turn) else 'stalemate'
        if self.halfmove >= 100:
            return 'fifty-move draw'
        if self.position_counts.get(self.key(), 0) >= 3:
            return 'threefold repetition'
        nonk = [(p.kind, p.color, (r + c) % 2) for r, row in enumerate(self.board.cells) for c, p in enumerate(row) if p and p.kind != 'K']
        if not nonk:
            return 'insufficient material'
        if len(nonk) == 1 and nonk[0][0] in ('B', 'N'):
            return 'insufficient material'
        if len(nonk) == 2 and all((x[0] == 'B' for x in nonk)) and (nonk[0][2] == nonk[1][2]):
            return 'insufficient material'
        return 'check' if self.board.check(self.turn) else 'playing'

    def move(self, r, c, tr, tc, promotion='Q'):
        """Apply a legal move and record it in standard chess notation."""
        if self.finished or promotion not in 'QRBN' or (not self.legal(r, c, tr, tc)):
            return False
        p = self.board.cells[r][c]
        kind = p.kind
        color = p.color
        capture = self.board.cells[tr][tc]
        if kind == 'P' and c != tc and (not capture):
            capture = self.board.cells[r][tc]
        ambiguous = []
        if kind != 'P' and kind != 'K':
            for rr, row in enumerate(self.board.cells):
                for cc, other in enumerate(row):
                    if (rr, cc) != (r, c) and other and (other.color == color) and (other.kind == kind) and self.legal(rr, cc, tr, tc):
                        ambiguous.append((rr, cc))
        if kind == 'K' and abs(tc - c) == 2:
            notation = 'O-O' if tc > c else 'O-O-O'
        else:
            prefix = '' if kind == 'P' else kind
            if ambiguous:
                prefix += chr(97 + c) if all((cc != c for _, cc in ambiguous)) else str(8 - r) if all((rr != r for rr, _ in ambiguous)) else chr(97 + c) + str(8 - r)
            if kind == 'P' and capture:
                prefix = chr(97 + c)
            notation = prefix + ('x' if capture else '') + chr(97 + tc) + str(8 - tr)
            if kind == 'P' and tr in (0, 7):
                notation += '=' + promotion
        snapshot = (deepcopy(self.board), self.turn, self.en_passant, list(self.moves), list(self.events), self.halfmove, self.fullmove, self.last_move, dict(self.position_counts), self.finished)
        self.history.append(snapshot)
        self.apply(r, c, tr, tc, promotion)
        self.halfmove = 0 if kind == 'P' or capture else self.halfmove + 1
        if color == 'b':
            self.fullmove += 1
        self.turn = 'b' if color == 'w' else 'w'
        self.last_move = ((r, c), (tr, tc))
        self._record_position()
        state = self.status()
        self.finished = state not in ('playing', 'check')
        if state == 'check':
            notation += '+'
        if state == 'checkmate':
            notation += '#'
        self.moves.append(notation)
        self.events.append({'color': color, 'kind': kind, 'capture': capture.kind if capture else None, 'castle': kind == 'K' and abs(tc - c) == 2, 'promotion': kind == 'P' and tr in (0, 7), 'checkmate': state == 'checkmate', 'gave_check': state in ('check', 'checkmate'), 'queen_sacrifice': False, 'status': state, 'move': (r, c, tr, tc)})
        if capture and capture.kind == 'Q' and (len(self.events) >= 2):
            previous = self.events[-2]
            if previous['color'] != color and previous['kind'] == 'Q' and (previous['move'][2:] == (r, c)):
                if not previous['capture']:
                    previous['queen_sacrifice'] = True
        return True

    def undo(self):
        """Go back to the previous position."""
        if not self.history:
            return False
        self.board, self.turn, self.en_passant, self.moves, self.events, self.halfmove, self.fullmove, self.last_move, self.position_counts, self.finished = self.history.pop()
        return True
