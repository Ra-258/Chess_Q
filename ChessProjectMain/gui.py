"""Main window and game controls for the Chess student project."""
import random
import threading
import time
import tkinter as tk
from copy import deepcopy
from pathlib import Path
from queue import Queue, Empty
from engine import ChessGame
from ai import ChessAI
from clock import ChessClock, PRESETS, display
from storage import StorageManager
from quests import QUESTS, QuestManager
BG = '#0D131D'
PANEL = '#172231'
LIGHT = '#F0EDE6'
DARK = '#292D34'
ACCENT = '#7892AE'
ACTIVE = '#304761'
TEXT = '#F0EDE6'
MUTED = '#99AABD'
LINE = '#304154'
ROOT = Path(__file__).resolve().parent

class ChessGUI:

    def __init__(self, root):
        self.root = root
        root.title('Chess')
        root.configure(bg=BG)
        root.minsize(760, 550)
        self.storage = StorageManager()
        self.settings_data = self.storage.settings()
        self.quests = QuestManager.from_data(self.storage.quest_progress())
        self.undo_used = False
        self._toast = None
        self._toast_after = None
        self.game = ChessGame()
        self.clock = ChessClock()
        self.mode = 'ai'
        self.human = 'w'
        self.difficulty = 'medium'
        self.game_id = None
        self.record = []
        self.clock_history = []
        self.flipped = False
        self.selected = None
        self.targets = set()
        self.premove = None
        self.busy = False
        self.token = 0
        self.ai_queue = Queue()
        self.modal = None
        self.sidebar_visible = True
        self.review_index = None
        self.result = '*'
        self._images = {}
        self.animating = False
        self._animation = None
        self._load_art()
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        for sequence, callback in [('<Control-z>', self.undo), ('<Control-s>', self.save_game), ('<Control-o>', self.continue_game), ('<Escape>', self.escape)]:
            self.root.bind(sequence, lambda e, fn=callback: fn())
        try:
            self.root.state('zoomed')
        except tk.TclError:
            self.root.geometry('1150x760')
        self.root.after(70, self._poll_ai)
        self.root.after(100, self._tick)
        self.show_menu()

    def _load_art(self):
        self.emblem = tk.PhotoImage(file=str(ROOT / 'assets' / 'knight_emblem.png')).subsample(2)
        for color in 'wb':
            for kind in 'KQRBNP':
                for size in (48, 64, 80, 96, 112, 128):
                    self._images[color, kind, size] = tk.PhotoImage(file=str(ROOT / 'assets' / 'pieces' / f'{color}{kind}_{size}.png'))

    def label(self, parent, text, size=11, color=TEXT, bold=False, bg=BG, **kwargs):
        return tk.Label(parent, text=text, bg=bg, fg=color, font=('Segoe UI', size, 'bold' if bold else 'normal'), **kwargs)

    def button(self, parent, text, command, primary=False, width=None):
        return tk.Button(parent, text=text, command=command, width=width, cursor='hand2', relief='flat', bd=0, font=('Segoe UI', 10, 'bold' if primary else 'normal'), padx=15, pady=10, bg=ACTIVE if primary else PANEL, fg=TEXT, activebackground=ACCENT, activeforeground=BG)

    def clear(self):
        self.modal = None
        self._toast = None
        for child in self.root.winfo_children():
            child.destroy()

    def card(self, parent):
        return tk.Frame(parent, bg=PANEL, padx=22, pady=18)

    def header(self, parent, title, back):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill='x', pady=(0, 20))
        self.button(row, '←  Back', back).pack(side='left')
        self.label(row, title, 20, bold=True).pack(side='left', padx=18)

    def dialog(self, title, description, actions):
        if self.modal and self.modal.winfo_exists():
            self.modal.destroy()
        shade = tk.Frame(self.root, bg='#0A0F17')
        shade.place(relx=0, rely=0, relwidth=1, relheight=1)
        pane = self.card(shade)
        pane.place(relx=0.5, rely=0.5, anchor='center', width=430)
        self.label(pane, title, 19, bold=True, bg=PANEL).pack(pady=(4, 10))
        if description:
            self.label(pane, description, 11, MUTED, bg=PANEL, wraplength=365, justify='center').pack(pady=(0, 18))
        bar = tk.Frame(pane, bg=PANEL)
        bar.pack(fill='x')
        for name, callback in actions:

            def fire(fn=callback):
                shade.destroy()
                self.modal = None
                if fn:
                    fn()
            self.button(bar, name, fire, primary=name in ('Start', 'Confirm', 'Save', 'Continue', 'Queen')).pack(side='left', expand=True, fill='x', padx=3)
        self.modal = shade

    def confirm(self, title, description, callback):
        if self.settings_data['confirm']:
            self.dialog(title, description, [('Cancel', None), ('Confirm', callback)])
        else:
            callback()

    def show_menu(self):
        self.token += 1
        self.busy = False
        self._animation = None
        self.animating = False
        self.clear()
        wrap = tk.Frame(self.root, bg=BG)
        wrap.pack(expand=True)
        tk.Label(wrap, image=self.emblem, bg=BG).pack(pady=(0, 5))
        self.label(wrap, 'Chess', 29, bold=True).pack(pady=(0, 32))
        self.button(wrap, 'New Game', self.new_game_screen, True, 29).pack(pady=5)
        self.button(wrap, 'Continue Game', self.continue_game, width=29).pack(pady=5)
        self.button(wrap, 'Quests', self.show_quests, width=29).pack(pady=5)
        self.button(wrap, 'Settings', lambda: self.settings_screen(self.show_menu), width=29).pack(pady=5)

    def new_game_screen(self):
        self.clear()
        outer = tk.Frame(self.root, bg=BG, padx=28, pady=20)
        outer.pack(fill='both', expand=True)
        self.header(outer, 'New Game', self.show_menu)
        pane = self.card(outer)
        pane.pack(expand=True)
        mode = tk.StringVar(value='ai')
        side = tk.StringVar(value='w')
        difficulty = tk.StringVar(value='medium')
        preset = tk.IntVar(value=3)

        def choices(title, options, var):
            self.label(pane, title, 11, MUTED, bg=PANEL).pack(anchor='w', pady=(12, 5))
            bar = tk.Frame(pane, bg=PANEL)
            bar.pack(fill='x')
            widgets = []
            for value, text in options:
                b = self.button(bar, text, lambda v=value: (var.set(v), refresh()))
                b.pack(side='left', fill='x', expand=True, padx=2)
                widgets.append((value, b))
            return widgets
        modes = choices('Mode', [('ai', 'Vs Computer'), ('local', 'Local Hotseat')], mode)
        sides = choices('Play as', [('w', 'White'), ('b', 'Black'), ('random', 'Random')], side)
        difficulty_title = self.label(pane, 'Computer difficulty', 11, MUTED, bg=PANEL)
        difficulty_title.pack(anchor='w', pady=(14, 5))
        diffbar = tk.Frame(pane, bg=PANEL)
        diffbar.pack(fill='x')
        diffs = []
        for val in ('easy', 'medium', 'hard'):
            b = self.button(diffbar, val.title(), lambda v=val: (difficulty.set(v), refresh()))
            b.pack(side='left', fill='x', expand=True, padx=2)
            diffs.append((val, b))
        self.label(pane, 'Time control', 11, MUTED, bg=PANEL).pack(anchor='w', pady=(18, 6))
        timegrid = tk.Frame(pane, bg=PANEL)
        timegrid.pack(fill='x')
        times = []
        for i, (name, seconds, increment) in enumerate(PRESETS):
            b = self.button(timegrid, name, lambda n=i: (preset.set(n), refresh()))
            b.grid(row=i // 3, column=i % 3, sticky='ew', padx=3, pady=3)
            times.append((i, b))
        for i in range(3):
            timegrid.columnconfigure(i, weight=1)

        def refresh():
            for options, var in ((modes, mode), (sides, side), (diffs, difficulty), (times, preset)):
                for val, b in options:
                    b.config(bg=ACTIVE if var.get() == val else BG)
            difficulty_title.config(fg=MUTED if mode.get() == 'ai' else '#536579')
            for _, b in diffs:
                b.config(state='normal' if mode.get() == 'ai' else 'disabled')
        refresh()

        def begin():
            self.mode = mode.get()
            self.human = random.choice('wb') if side.get() == 'random' else side.get()
            self.difficulty = difficulty.get()
            self.clock_preset = preset.get()
            sec, inc = PRESETS[preset.get()][1:]
            self.clock = ChessClock(sec, inc)
            self.game = ChessGame()
            self.record = []
            self.clock_history = []
            self.result = '*'
            self.game_id = None
            self.flipped = self.human == 'b'
            self.undo_used = False
            self.token += 1
            self.busy = False
            self.premove = None
            self.selected = None
            self.review_index = None
            self.build_game()
            self.clock.start('w')
            self.save_game()
            if self.mode == 'ai' and self.human == 'b':
                self.schedule_ai()
        self.button(pane, 'Start Game', begin, True, 28).pack(pady=(22, 3))

    def settings_screen(self, back):
        self.clear()
        outer = tk.Frame(self.root, bg=BG, padx=32, pady=24)
        outer.pack(fill='both', expand=True)
        self.header(outer, 'Settings', back)
        pane = self.card(outer)
        pane.pack(expand=True)
        options = [('coordinates', 'Board coordinates'), ('legal_moves', 'Legal move hints'), ('last_move', 'Last move highlight'), ('animations', 'Move animations'), ('auto_queen', 'Auto-queen'), ('autosave', 'Autosave'), ('confirm', 'Confirm important actions')]
        for key, name in options:
            row = tk.Frame(pane, bg=PANEL)
            row.pack(fill='x', pady=10)
            self.label(row, name, 11, bg=PANEL).pack(side='left', anchor='w')
            var = tk.BooleanVar(value=self.settings_data[key])

            def change(k=key, v=var):
                self.settings_data[k] = v.get()
                self.storage.save_settings(self.settings_data)
                if hasattr(self, 'canvas') and self.canvas.winfo_exists():
                    self.draw()
            tk.Checkbutton(row, variable=var, command=change, bg=PANEL, activebackground=PANEL, selectcolor=BG, fg=TEXT, activeforeground=TEXT, bd=0).pack(side='right', padx=10)

    def continue_game(self):
        data = self.storage.latest()
        if data:
            self._restore(data)
        else:
            self.dialog('No saved game', 'Start a new game first.', [('OK', None)])

    def load_game(self, id):
        data = self.storage.load_game(id)
        if data:
            self._restore(data)
        else:
            self.dialog('Could not load', 'The saved game is missing or damaged.', [('OK', None)])

    def _restore(self, data):
        try:
            game = ChessGame()
            for move in data['record']:
                if not game.move(*move[:4], promotion=move[4]):
                    raise ValueError('Invalid saved move')
            self.game = game
            self.record = [list(x) for x in data['record']]
            self.mode = data['mode']
            self.human = data['human']
            self.difficulty = data['difficulty']
            self.clock = ChessClock.restore(data['clock'])
            self.clock_history = data.get('clock_history', [])
            self.flipped = data.get('flipped', False)
            saved_preset = data.get('clock_preset', 5)
            self.clock_preset = min(max(0, saved_preset), len(PRESETS) - 1) if isinstance(saved_preset, int) else len(PRESETS) - 1
            self.result = data.get('result', '*')
            self.game_id = data['id']
            self.undo_used = data.get('undo_used', False)
            self.selected = None
            self.premove = None
            self.review_index = None
            self.token += 1
            self.busy = False
            self.build_game()
            if not game.finished and self.result == '*':
                self.clock.start(game.turn)
                if self.mode == 'ai' and game.turn != self.human:
                    self.schedule_ai()
        except (KeyError, ValueError, TypeError, IndexError) as exc:
            self.dialog('Could not load', f'This save could not be restored: {exc}', [('OK', None)])

    def save_game(self):
        if not hasattr(self, 'clock') or not hasattr(self, 'record'):
            return
        data = {'record': self.record, 'mode': self.mode, 'human': self.human, 'difficulty': self.difficulty, 'clock': self.clock.snapshot(), 'clock_history': self.clock_history, 'clock_preset': getattr(self, 'clock_preset', 5), 'time_name': PRESETS[getattr(self, 'clock_preset', 5)][0], 'flipped': self.flipped, 'result': self.result, 'undo_used': self.undo_used}
        self.game_id = self.storage.save_game(data, self.game_id)

    def build_game(self):
        self.clear()
        outer = tk.Frame(self.root, bg=BG, padx=18, pady=12)
        outer.pack(fill='both', expand=True)
        top = tk.Frame(outer, bg=BG)
        top.pack(fill='x', pady=(0, 8))
        self.button(top, '←  Menu', self.leave_game).pack(side='left')
        self.button(top, '⋯  Options', self.game_options).pack(side='right', padx=3)
        self.button(top, 'Quests', self.show_quests).pack(side='right', padx=3)
        self.button(top, 'Moves  ☷', self.toggle_sidebar).pack(side='right', padx=3)
        self.body = tk.Frame(outer, bg=BG)
        self.body.pack(fill='both', expand=True)
        self.boardarea = tk.Frame(self.body, bg=BG)
        self.boardarea.pack(side='left', fill='both', expand=True)
        self.topbar = tk.Frame(self.boardarea, bg=BG)
        self.topbar.pack(fill='x', padx=6, pady=(0, 4))
        self.top_player = self.label(self.topbar, '', 11)
        self.top_player.pack(side='left')
        self.top_clock = self.label(self.topbar, '', 14, bold=True)
        self.top_clock.pack(side='right')
        self.canvas = tk.Canvas(self.boardarea, bg=BG, highlightthickness=0, cursor='hand2')
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda e: self.draw())
        self.canvas.bind('<Button-1>', self.click)
        self.bottombar = tk.Frame(self.boardarea, bg=BG)
        self.bottombar.pack(fill='x', padx=6, pady=(4, 0))
        self.bottom_player = self.label(self.bottombar, '', 11, bold=True)
        self.bottom_player.pack(side='left')
        self.bottom_clock = self.label(self.bottombar, '', 14, bold=True)
        self.bottom_clock.pack(side='right')
        self.sidebar = tk.Frame(self.body, bg=PANEL, width=204, padx=9, pady=10)
        self.sidebar.pack_propagate(False)
        if self.sidebar_visible:
            self.sidebar.pack(side='right', fill='y', padx=(10, 0))
        self.move_canvas = tk.Canvas(self.sidebar, bg=PANEL, highlightthickness=0, width=185)
        self.move_canvas.pack(fill='both', expand=True)
        self.move_canvas.bind('<Configure>', lambda e: self.draw_history())
        self.move_canvas.bind('<MouseWheel>', lambda e: self.move_canvas.yview_scroll(-int(e.delta / 120), 'units'))
        bar = tk.Frame(self.sidebar, bg=PANEL)
        bar.pack(fill='x', pady=(8, 0))
        for i, (name, fn) in enumerate([('Undo', self.undo), ('Flip', self.flip), ('Save', self.save_game), ('More', self.game_options)]):
            self.button(bar, name, fn).grid(row=i // 2, column=i % 2, sticky='ew', padx=2, pady=2)
        bar.columnconfigure(0, weight=1)
        bar.columnconfigure(1, weight=1)
        self.update_view()

    def toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        if self.sidebar_visible:
            self.sidebar.pack(side='right', fill='y', padx=(10, 0))
        else:
            self.sidebar.pack_forget()
        self.draw()

    def update_view(self):
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            return
        top = 'w' if self.flipped else 'b'
        bottom = 'b' if self.flipped else 'w'
        for color, widget in ((top, self.top_player), (bottom, self.bottom_player)):
            name = 'White' if color == 'w' else 'Black'
            if self.mode == 'ai':
                name += ' · You' if color == self.human else ' · Computer'
            else:
                name += ' · Player 1' if color == self.human else ' · Player 2'
            widget.config(text=('●  ' if self.game.turn == color and self.result == '*' else '') + name)
        self.top_clock.config(text=display(self.clock.left(top)))
        self.bottom_clock.config(text=display(self.clock.left(bottom)))
        self.draw()
        self.draw_history()

    def _geometry(self):
        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        square = max(1, min(w, h) // 8)
        x = (w - 8 * square) // 2
        y = (h - 8 * square) // 2
        self.square = square
        self.origin = (x, y)
        return (square, x, y)

    def _screen(self, r, c):
        return (7 - r, 7 - c) if self.flipped else (r, c)

    def _board(self, r, c):
        return (7 - r, 7 - c) if self.flipped else (r, c)

    def draw(self):
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            return
        canvas = self.canvas
        canvas.delete('all')
        square, x, y = self._geometry()
        board = self.game.board
        if self.review_index is not None:
            board = self._review_board()
        for sr in range(8):
            for sc in range(8):
                r, c = self._board(sr, sc)
                color = LIGHT if (r + c) % 2 == 0 else DARK
                if self.settings_data['last_move'] and self.review_index is None and self.game.last_move and ((r, c) in self.game.last_move):
                    color = '#BBC9CF' if color == LIGHT else '#475968'
                if self.selected == (r, c):
                    color = '#91A8BA'
                if self.premove and (r, c) in self.premove:
                    color = '#7289A2'
                x1 = x + sc * square
                y1 = y + sr * square
                canvas.create_rectangle(x1, y1, x1 + square + 1, y1 + square + 1, fill=color, outline=color)
                p = board.cells[r][c]
                if p and (not (self._animation and (r, c) == self._animation['to'])):
                    size = min((48, 64, 80, 96, 112, 128), key=lambda s: abs(s - square * 0.86))
                    canvas.create_image(x1 + square / 2, y1 + square / 2, image=self._images[p.color, p.kind, size])
                if self.settings_data['legal_moves'] and self.selected and ((r, c) in self.targets):
                    if p:
                        canvas.create_oval(x1 + 5, y1 + 5, x1 + square - 5, y1 + square - 5, outline='#9BB7CF', width=3)
                    else:
                        radius = max(4, square * 0.115)
                        canvas.create_oval(x1 + square / 2 - radius, y1 + square / 2 - radius, x1 + square / 2 + radius, y1 + square / 2 + radius, fill='#8FA5B8', outline='')
                if self.settings_data['coordinates']:
                    if sr == 7:
                        canvas.create_text(x1 + square - 5, y1 + square - 4, text='abcdefgh'[c], fill='#9AA8B4' if color == DARK else '#596675', font=('Segoe UI', max(8, square // 8)), anchor='se')
                    if sc == 0:
                        canvas.create_text(x1 + 4, y1 + 3, text=str(8 - r), fill='#9AA8B4' if color == DARK else '#596675', font=('Segoe UI', max(8, square // 8)), anchor='nw')
        if self._animation:
            a = self._animation
            start = self._screen(*a['from'])
            end = self._screen(*a['to'])
            progress = a['step'] / 8
            px = x + (start[1] + (end[1] - start[1]) * progress + 0.5) * square
            py = y + (start[0] + (end[0] - start[0]) * progress + 0.5) * square
            size = min((48, 64, 80, 96, 112, 128), key=lambda s: abs(s - square * 0.86))
            canvas.create_image(px, py, image=self._images[a['color'], a['kind'], size])
        if self.review_index is None and board.check(self.game.turn):
            for r, row in enumerate(board.cells):
                for c, p in enumerate(row):
                    if p and p.kind == 'K' and (p.color == self.game.turn):
                        sr, sc = self._screen(r, c)
                        canvas.create_rectangle(x + sc * square + 2, y + sr * square + 2, x + (sc + 1) * square - 2, y + (sr + 1) * square - 2, outline='#A86A73', width=3)

    def _review_board(self):
        replay = ChessGame()
        for move in self.record[:self.review_index]:
            replay.move(*move[:4], promotion=move[4])
        return replay.board

    def draw_history(self):
        if not hasattr(self, 'move_canvas') or not self.move_canvas.winfo_exists():
            return
        c = self.move_canvas
        c.delete('all')
        width = max(c.winfo_width(), 170)
        for i in range(0, len(self.game.moves), 2):
            y = 12 + i // 2 * 33
            if i >= len(self.game.moves) - 2:
                c.create_rectangle(2, y - 8, width - 3, y + 23, fill='#253750', outline='')
            c.create_text(10, y, text=f'{i // 2 + 1}.', fill=MUTED, anchor='nw', font=('Segoe UI', 10))
            for j in range(2):
                if i + j >= len(self.game.moves):
                    continue
                move = self.game.moves[i + j]
                tag = f'move{i + j + 1}'
                c.create_text(48 + j * (width - 48) // 2, y, text=move, fill=LIGHT if j == 0 else '#A3BAD0', anchor='nw', font=('Segoe UI', 10), tags=(tag,))
                c.tag_bind(tag, '<Button-1>', lambda e, n=i + j + 1: self.review(n))
        c.configure(scrollregion=(0, 0, width, max(c.winfo_height(), 25 + (len(self.game.moves) + 1) // 2 * 33)))
        c.yview_moveto(1)

    def review(self, n):
        self.review_index = n
        self.selected = None
        self.targets = set()
        self.draw()
        self.dialog('Review position', f'{n} / {len(self.record)}', [('Previous', lambda: self.review(max(0, n - 1))), ('Next', lambda: self.review(min(len(self.record), n + 1))), ('Live board', self.live_board)])

    def live_board(self):
        self.review_index = None
        self.draw()

    def click(self, event):
        if self.modal or self.review_index is not None or self.result != '*' or self.animating:
            return
        square, x, y = self._geometry()
        sc = (event.x - x) // square
        sr = (event.y - y) // square
        if not (0 <= sr < 8 and 0 <= sc < 8):
            return
        r, c = self._board(sr, sc)
        premoving = self.mode == 'ai' and self.game.turn != self.human
        if premoving and (not self.busy):
            return
        if not premoving and self.busy:
            return
        player = self.human if premoving else self.game.turn
        piece = self.game.board.cells[r][c]
        if self.selected is not None and (r, c) in self.targets:
            fr, fc = self.selected
            self.selected = None
            self.targets = set()
            if premoving:
                self.premove = ((fr, fc), (r, c))
                self.draw()
            else:
                self.attempt_move(fr, fc, r, c)
            return
        if piece and piece.color == player:
            self.selected = (r, c)
            if premoving:
                self.targets = {(tr, tc) for tr in range(8) for tc in range(8) if self.game.pseudo(r, c, tr, tc)}
            else:
                self.targets = {(tr, tc) for tr in range(8) for tc in range(8) if self.game.legal(r, c, tr, tc)}
        else:
            self.selected = None
            self.targets = set()
            if premoving:
                self.premove = None
        self.draw()

    def attempt_move(self, r, c, tr, tc):
        piece = self.game.board.cells[r][c]
        if piece and piece.kind == 'P' and (tr in (0, 7)) and (not self.settings_data['auto_queen']):
            self.dialog('Promote pawn', 'Choose your new piece.', [('Queen', lambda: self.play_move(r, c, tr, tc, 'Q')), ('Rook', lambda: self.play_move(r, c, tr, tc, 'R')), ('Bishop', lambda: self.play_move(r, c, tr, tc, 'B')), ('Knight', lambda: self.play_move(r, c, tr, tc, 'N'))])
        else:
            self.play_move(r, c, tr, tc, 'Q')

    def play_move(self, r, c, tr, tc, promotion='Q'):
        if self.result != '*' or not self.game.legal(r, c, tr, tc):
            return False
        mover = self.game.turn
        moving_piece = self.game.board.cells[r][c]
        moving_kind = moving_piece.kind
        previous_clock = self.clock.snapshot()
        if not self.game.move(r, c, tr, tc, promotion):
            return False
        self.clock_history.append(previous_clock)
        self.record.append([r, c, tr, tc, promotion])
        self.selected = None
        self.targets = set()
        self.clock.switch(mover)
        status = self.game.status()
        if self.game.finished:
            self.clock.pause()
            self.result = ('1-0' if mover == 'w' else '0-1') if status == 'checkmate' else '1/2-1/2'
        self.update_view()
        if self.settings_data['animations']:
            self._animation = {'from': (r, c), 'to': (tr, tc), 'color': mover, 'kind': moving_kind, 'step': 0}
            self.animating = True
            self._animate_step()
        if self.settings_data['autosave'] or self.game.finished:
            self.save_game()
        self._evaluate_quests()
        if self.game.finished:
            self.root.after(260, lambda: self.game_over(status))
        elif self.mode == 'ai' and self.game.turn != self.human:
            self.schedule_ai()
        return True

    def _animate_step(self):
        if not self._animation:
            return
        self._animation['step'] += 1
        if self._animation['step'] > 8:
            self._animation = None
            self.animating = False
            self.draw()
            return
        self.draw()
        self.root.after(18, self._animate_step)

    def schedule_ai(self):
        if self.busy or self.game.finished or self.result != '*':
            return
        self.busy = True
        token = self.token
        position = deepcopy(self.game)
        started = time.monotonic()
        difficulty = self.difficulty

        def worker():
            try:
                move = ChessAI(difficulty).choose(position)
            except Exception:
                move = None
            self.ai_queue.put((token, move, started))
        threading.Thread(target=worker, daemon=True).start()

    def _poll_ai(self):
        try:
            while True:
                token, move, started = self.ai_queue.get_nowait()
                if token != self.token or not self.busy:
                    continue
                wait = max(0, 0.5 - (time.monotonic() - started))
                self.root.after(int(wait * 1000), lambda t=token, m=move: self._apply_ai(t, m))
        except Empty:
            pass
        self.root.after(70, self._poll_ai)

    def _apply_ai(self, token, move):
        if token != self.token or not self.busy or self.mode != 'ai' or (self.game.turn == self.human):
            return
        self.busy = False
        if move:
            self.play_move(*move)
        if self.premove and self.result == '*' and (self.game.turn == self.human):
            (r, c), (tr, tc) = self.premove
            self.premove = None
            if self.game.legal(r, c, tr, tc):
                self.root.after(210, lambda: self.attempt_move(r, c, tr, tc))
            else:
                self.draw()

    def _tick(self):
        try:
            if self.result == '*' and hasattr(self, 'canvas') and self.canvas.winfo_exists():
                flag = self.clock.flag()
                if flag:
                    self.clock.pause()
                    self.result = '0-1' if flag == 'w' else '1-0'
                    self.token += 1
                    self.busy = False
                    self.save_game()
                    self._evaluate_quests()
                    self.update_view()
                    self.game_over('time forfeit')
                else:
                    top = 'w' if self.flipped else 'b'
                    bottom = 'b' if self.flipped else 'w'
                    self.top_clock.config(text=display(self.clock.left(top)))
                    self.bottom_clock.config(text=display(self.clock.left(bottom)))
        except tk.TclError:
            pass
        self.root.after(100, self._tick)

    def game_over(self, status):
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
            return
        text = {'checkmate': 'Checkmate', 'stalemate': 'Stalemate', 'time forfeit': 'Time is up', 'insufficient material': 'Draw · insufficient material', 'threefold repetition': 'Draw · repetition', 'fifty-move draw': 'Draw · fifty-move rule'}.get(status, 'Game over')
        self.dialog(text, f'Result: {self.result}', [('Menu', self.show_menu), ('Review', lambda: self.review(len(self.record))), ('Rematch', self.restart_direct)])

    def undo(self):
        if not hasattr(self, 'canvas') or not self.canvas.winfo_exists() or (not self.record):
            return
        self.token += 1
        self.busy = False
        self.premove = None
        self.review_index = None
        self._animation = None
        self.animating = False
        steps = 2 if self.mode == 'ai' and self.game.turn == self.human and (len(self.record) >= 2) else 1
        for _ in range(steps):
            if not self.game.undo():
                break
            self.record.pop()
            snapshot = self.clock_history.pop()
            self.clock = ChessClock.restore(snapshot)
        self.result = '*'
        self.undo_used = True
        self.clock.start(self.game.turn)
        self.update_view()
        self.save_game()
        if self.mode == 'ai' and self.game.turn != self.human:
            self.schedule_ai()

    def flip(self):
        self.flipped = not self.flipped
        self.update_view()
        self.save_game()

    def leave_game(self):
        self.clock.pause()
        self.save_game()
        self.show_menu()

    def restart_direct(self):
        sec, inc = PRESETS[getattr(self, 'clock_preset', 5)][1:]
        self.token += 1
        self.busy = False
        self._animation = None
        self.animating = False
        self.game = ChessGame()
        self.clock = ChessClock(sec, inc)
        self.record = []
        self.clock_history = []
        self.result = '*'
        self.game_id = None
        self.premove = None
        self.selected = None
        self.review_index = None
        self.undo_used = False
        self.build_game()
        self.clock.start('w')
        self.save_game()
        if self.mode == 'ai' and self.human == 'b':
            self.schedule_ai()

    def restart(self):
        self.confirm('Restart game?', 'Your current game will remain saved.', self.restart_direct)

    def resign(self):

        def do():
            self.result = '0-1' if self.game.turn == 'w' else '1-0'
            self.clock.pause()
            self.token += 1
            self.busy = False
            self.save_game()
            self._evaluate_quests()
            self.game_over('resignation')
        self.confirm('Resign game?', 'This will end the current match.', do)

    def offer_draw(self):
        if self.mode == 'ai':
            self.dialog('Draw offer', 'The computer declines the draw. Keep playing!', [('OK', None)])
        else:
            self.confirm('Agree to a draw?', 'Both local players agree to finish the game.', self._agree_draw)

    def _agree_draw(self):
        self.result = '1/2-1/2'
        self.clock.pause()
        self.token += 1
        self.busy = False
        self.save_game()
        self._evaluate_quests()
        self.game_over('draw')

    def game_options(self):
        """The small set of actions needed during a match."""
        self.dialog('Game options', '', [('Restart', self.restart), ('Resign', self.resign), ('Draw', self.offer_draw), ('Close', None)])

    def _back_to_game(self):
        self.build_game()

    def _quest_colors(self):
        return (self.human,) if self.mode == 'ai' else ('w', 'b')

    def _evaluate_quests(self):
        """Check the eight optional quests after each move or result."""
        awarded, changed = self.quests.evaluate(self.game, self._quest_colors(), self.mode, self.difficulty, self.undo_used, self.result, self.game_id)
        if changed:
            self.storage.save_quest_progress(self.quests.to_data())
        if awarded:
            if len(awarded) == 1:
                message = 'Quest completed  ·  ' + awarded[0].name
            else:
                message = f'{len(awarded)} quests completed  ·  ' + awarded[0].name
            self._show_quest_toast(message)

    def _show_quest_toast(self, message):
        """Small, non-modal, silent notification inside the existing window."""
        if self._toast_after is not None:
            try:
                self.root.after_cancel(self._toast_after)
            except (tk.TclError, ValueError):
                pass
        if self._toast is not None:
            try:
                if self._toast.winfo_exists():
                    self._toast.destroy()
            except tk.TclError:
                pass
        toast = tk.Frame(self.root, bg=ACTIVE, padx=17, pady=11, highlightbackground=ACCENT, highlightthickness=1)
        toast.place(relx=0.98, y=22, anchor='ne')
        self.label(toast, message, 10, bg=ACTIVE, bold=True).pack()
        toast.lift()
        self._toast = toast

        def dismiss():
            try:
                if toast.winfo_exists():
                    toast.destroy()
            except tk.TclError:
                pass
            if self._toast is toast:
                self._toast = None
            self._toast_after = None
        self._toast_after = self.root.after(3200, dismiss)

    def show_quests(self):
        """Scrollable in-app quest journal, reachable from menu or active match."""
        if self.modal is not None:
            try:
                if self.modal.winfo_exists():
                    return
            except tk.TclError:
                pass
        shade = tk.Frame(self.root, bg='#0A0F17')
        shade.place(relx=0, rely=0, relwidth=1, relheight=1)
        shade.lift()
        screen_width = max(760, self.root.winfo_width())
        screen_height = max(550, self.root.winfo_height())
        width = min(660, screen_width - 60)
        height = min(690, screen_height - 50)
        pane = tk.Frame(shade, bg=PANEL, padx=22, pady=17)
        pane.place(relx=0.5, rely=0.5, anchor='center', width=width, height=height)
        head = tk.Frame(pane, bg=PANEL)
        head.pack(fill='x', pady=(0, 12))
        self.label(head, 'Quests', 21, bg=PANEL, bold=True).pack(side='left')
        self.button(head, 'Close', lambda: (shade.destroy(), setattr(self, 'modal', None))).pack(side='right')
        count = len(self.quests.completed)
        self.label(pane, f'{count} / {len(QUESTS)} completed', 10, MUTED, bg=PANEL).pack(anchor='w', pady=(0, 12))
        border = tk.Frame(pane, bg=LINE, height=1)
        border.pack(fill='x', pady=(0, 4))
        area = tk.Frame(pane, bg=PANEL)
        area.pack(fill='both', expand=True)
        scroll = tk.Scrollbar(area, orient='vertical')
        scroll.pack(side='right', fill='y')
        canvas = tk.Canvas(area, bg=PANEL, highlightthickness=0, yscrollcommand=scroll.set)
        canvas.pack(side='left', fill='both', expand=True)
        scroll.config(command=canvas.yview)
        content = tk.Frame(canvas, bg=PANEL)
        window = canvas.create_window((0, 0), window=content, anchor='nw')
        content.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: canvas.itemconfigure(window, width=e.width))

        def on_wheel(event):
            canvas.yview_scroll(-int(event.delta / 120) if event.delta else 0, 'units')
        canvas.bind('<MouseWheel>', on_wheel)
        content.bind('<MouseWheel>', on_wheel)
        for quest in QUESTS:
            completed = quest.key in self.quests.completed
            row = tk.Frame(content, bg=PANEL)
            row.pack(fill='x', padx=12, pady=9)
            self.label(row, '✓' if completed else '·', 16, '#AFD0BB' if completed else MUTED, bg=PANEL).pack(side='left', padx=(2, 12))
            labels = tk.Frame(row, bg=PANEL)
            labels.pack(side='left', fill='x', expand=True)
            self.label(labels, quest.name, 11, TEXT if completed else '#CED7E2', bold=completed, bg=PANEL).pack(anchor='w')
            self.label(labels, quest.description, 9, MUTED, bg=PANEL).pack(anchor='w', pady=(2, 0))
            if not completed and quest.target > 1:
                progress = max((self.quests.progress(self.game, color, quest.key, self.mode, self.difficulty, self.undo_used, self.result) for color in self._quest_colors()))
                self.label(row, f'{progress}/{quest.target}', 9, MUTED, bg=PANEL).pack(side='right')
        self.modal = shade

    def escape(self):
        if self.modal and self.modal.winfo_exists():
            self.modal.destroy()
            self.modal = None
        else:
            self.selected = None
            self.targets = set()
            self.premove = None
            self.draw()

    def close(self):
        try:
            if hasattr(self, 'canvas') and self.canvas.winfo_exists():
                self.clock.pause()
                self.save_game()
        except (tk.TclError, OSError):
            pass
        self.root.destroy()
