"""A complete local move can be saved and continued in the app."""
import tkinter as tk
import unittest
from tempfile import TemporaryDirectory

from gui import ChessGUI
from storage import StorageManager
from engine import ChessGame
from clock import ChessClock


class StudentFlow(unittest.TestCase):
    def test_save_and_continue(self):
        root = tk.Tk()
        root.withdraw()
        try:
            with TemporaryDirectory() as folder:
                app = ChessGUI(root)
                app.storage = StorageManager(folder)
                app.mode = 'local'
                app.human = 'w'
                app.game = ChessGame()
                app.clock = ChessClock(600)
                app.clock_preset = 3
                app.record = []
                app.clock_history = []
                app.game_id = None
                app.result = '*'
                app.build_game()
                self.assertTrue(app.play_move(6, 4, 4, 4))
                self.assertEqual(app.game.moves, ['e4'])
                app.leave_game()
                app.continue_game()
                self.assertEqual(app.game.moves, ['e4'])
                self.assertEqual(app.game.turn, 'b')
                app.close()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass

    def test_restore_previous_save_format(self):
        import json
        with TemporaryDirectory() as folder:
            store = StorageManager(folder)
            old_id = 'old123'
            old_games = store.folder / 'games'
            old_games.mkdir()
            (old_games / f'{old_id}.json').write_text(
                json.dumps({'id': old_id, 'record': [1]}), encoding='utf-8')
            (store.folder / 'recent.json').write_text(
                json.dumps({'id': old_id}), encoding='utf-8')
            self.assertEqual(store.latest()['id'], old_id)
