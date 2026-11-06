import unittest
from engine import ChessGame
from ai import ChessAI

class ChessRules(unittest.TestCase):
    def test_opening_moves(self):self.assertEqual(len(list(ChessGame().possible_moves())),20)
    def test_undo(self):
        g=ChessGame();self.assertTrue(g.move(6,4,4,4));self.assertTrue(g.undo());self.assertEqual(g.moves,[])
    def test_checkmate(self):
        g=ChessGame()
        for m in [(6,5,5,5),(1,4,3,4),(6,6,4,6),(0,3,4,7)]:self.assertTrue(g.move(*m))
        self.assertEqual(g.status(),'checkmate')
    def test_castle(self):
        g=ChessGame()
        for m in [(7,6,5,5),(1,0,2,0),(6,4,4,4),(2,0,3,0),(7,5,6,4),(1,1,2,1),(7,4,7,6)]:self.assertTrue(g.move(*m))
        self.assertEqual(g.moves[-1],'O-O')
    def test_en_passant(self):
        g=ChessGame()
        for m in [(6,4,4,4),(1,0,2,0),(4,4,3,4),(1,3,3,3)]:self.assertTrue(g.move(*m))
        self.assertTrue(g.move(3,4,2,3));self.assertIsNone(g.board.cells[3][3])
    def test_promotion(self):
        g=ChessGame();g.board.cells=[[None]*8 for _ in range(8)]
        from engine import Piece
        g.board.cells[7][4]=Piece('w','K');g.board.cells[0][4]=Piece('b','K');g.board.cells[1][0]=Piece('w','P')
        self.assertTrue(g.move(1,0,0,0,'N'));self.assertEqual(g.board.cells[0][0].kind,'N')
    def test_ai(self):
        for level in ('easy','medium','hard'):
            g=ChessGame();self.assertIn(ChessAI(level).choose(g),list(g.possible_moves()))
    def test_turn_changes(self):
        game = ChessGame()
        self.assertTrue(game.move(6, 4, 4, 4))
        self.assertEqual(game.turn, 'b')
