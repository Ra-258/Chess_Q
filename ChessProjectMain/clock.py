"""Two-player chess clock. Uses monotonic time while the program is open."""
import time
PRESETS = [('1 min', 60, 0), ('3 min', 180, 0), ('5 min', 300, 0), ('10 min', 600, 0), ('15 + 10', 900, 10), ('Unlimited', None, 0)]

class ChessClock:
    """Count down both players using the computer’s monotonic clock."""

    def __init__(self, seconds=600, increment=0):
        self.remaining = {'w': float(seconds) if seconds is not None else None, 'b': float(seconds) if seconds is not None else None}
        self.increment = increment
        self.active = None
        self.started_at = None

    def pause(self):
        if self.active is not None and self.remaining[self.active] is not None:
            self.remaining[self.active] = max(0, self.remaining[self.active] - (time.monotonic() - self.started_at))
        self.active = None
        self.started_at = None

    def start(self, color):
        self.pause()
        self.active = color
        self.started_at = time.monotonic()

    def switch(self, previous):
        self.pause()
        if self.remaining[previous] is not None:
            self.remaining[previous] += self.increment
        self.start('b' if previous == 'w' else 'w')

    def left(self, color):
        v = self.remaining[color]
        if v is None:
            return None
        if color == self.active:
            return max(0, v - (time.monotonic() - self.started_at))
        return max(0, v)

    def flag(self):
        return self.active if self.active and self.left(self.active) <= 0 else None

    def snapshot(self):
        return {'remaining': {c: self.left(c) for c in 'wb'}, 'increment': self.increment, 'active': self.active}

    @classmethod
    def restore(cls, data):
        clock = cls(None, data.get('increment', 0))
        clock.remaining = data['remaining'].copy()
        return clock

def display(seconds):
    if seconds is None:
        return '∞'
    seconds = max(0, int(seconds + 0.999))
    return f'{seconds // 60:02d}:{seconds % 60:02d}'
