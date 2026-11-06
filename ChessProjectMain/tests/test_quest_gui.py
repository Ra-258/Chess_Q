"""Verify the quest menu, in-game journal and non-modal toast."""
import tkinter as tk
import unittest
from tempfile import TemporaryDirectory
from gui import ChessGUI
from storage import StorageManager
from clock import ChessClock
from engine import ChessGame


class QuestGuiTests(unittest.TestCase):
    def test_journal_from_main_menu_and_match(self):
        root=tk.Tk()
        root.withdraw()
        try:
            with TemporaryDirectory() as folder:
                app=ChessGUI(root)
                app.storage=StorageManager(folder)
                app.quests=__import__('quests').QuestManager()
                root.update()
                menu_buttons=[w.cget('text') for w in root.winfo_children()[0].winfo_children()
                              if isinstance(w, tk.Button)]
                self.assertIn('Quests', menu_buttons)
                app.show_quests()
                root.update()
                self.assertIsNotNone(app.modal)
                self.assertTrue(app.modal.winfo_exists())
                app.escape()
                app.mode='local';app.game=ChessGame();app.clock=ChessClock(None)
                app.record=[];app.clock_history=[];app.game_id=None
                app.build_game();root.update()
                app.show_quests();root.update()
                self.assertTrue(app.modal.winfo_exists())
                app.escape()
                self.assertTrue(app.canvas.winfo_exists())
                self.assertEqual(root.title(), 'Chess')
                app.close()
        finally:
            try:root.destroy()
            except tk.TclError:pass

    def test_real_capture_awards_saves_and_notifies(self):
        root=tk.Tk()
        root.withdraw()
        try:
            with TemporaryDirectory() as folder:
                app=ChessGUI(root)
                app.storage=StorageManager(folder)
                app.quests=__import__('quests').QuestManager()
                app.mode='local';app.human='w';app.difficulty='medium'
                app.game=ChessGame();app.clock=ChessClock(None)
                app.record=[];app.clock_history=[];app.game_id=None;app.result='*'
                app.build_game()
                root.update()
                self.assertTrue(app.play_move(6,4,4,4))
                self.assertTrue(app.play_move(1,3,3,3))
                self.assertTrue(app.play_move(4,4,3,3))
                self.assertIn('first_blood', app.quests.completed)
                saved=app.storage.quest_progress()
                self.assertIn('first_blood', saved['completed'])
                self.assertIsNotNone(app._toast)
                self.assertTrue(app._toast.winfo_exists())
                self.assertIsNone(app.modal)
                app.close()
        finally:
            try:root.destroy()
            except tk.TclError:pass

    def test_toast_is_not_a_separate_window(self):
        root=tk.Tk()
        root.withdraw()
        try:
            app=ChessGUI(root)
            app._show_quest_toast('Quest completed  ·  First Blood')
            root.update()
            self.assertIsInstance(app._toast, tk.Frame)
            self.assertEqual(len(root.winfo_children()), 2)
            app.show_menu()
            root.update()
            self.assertIsNone(app._toast)
            app.close()
        finally:
            try:root.destroy()
            except tk.TclError:pass
