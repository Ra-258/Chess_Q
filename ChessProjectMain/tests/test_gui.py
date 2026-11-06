import unittest
import tkinter as tk
from gui import ChessGUI

class GUISmoke(unittest.TestCase):
    def test_navigation(self):
        root=tk.Tk();root.withdraw()
        try:
            app=ChessGUI(root)
            root.update();app.new_game_screen();root.update()
            app.settings_screen(app.show_menu);root.update()
            app.game=__import__('engine').ChessGame();app.build_game();root.update()
            self.assertTrue(app.canvas.winfo_exists())
            app.toggle_sidebar();app.toggle_sidebar();root.update()
            app.close()
        finally:
            try:root.destroy()
            except tk.TclError:pass


class CleanInterface(unittest.TestCase):
    def test_menus_have_no_decorative_subtitles(self):
        root=tk.Tk();root.withdraw()
        try:
            app=ChessGUI(root)
            def labels(widget):
                values=[]
                for child in widget.winfo_children():
                    if isinstance(child,tk.Label):values.append(child.cget('text'))
                    values.extend(labels(child))
                return values
            menu_labels=labels(root)
            self.assertEqual([s for s in menu_labels if s], ['Chess'])
            app.settings_screen(app.show_menu)
            settings_labels=labels(root)
            self.assertNotIn('No sounds. No accounts. Everything stays on your computer.',settings_labels)
            self.assertNotIn('Show ranks and files',settings_labels)
            self.assertIn('Settings',settings_labels)
            app.new_game_screen()
            new_game_labels=labels(root)
            self.assertNotIn('Player 2 / Computer automatically plays the opposite color.',new_game_labels)
        finally:
            try:root.destroy()
            except tk.TclError:pass
