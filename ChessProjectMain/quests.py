"""Eight optional chess quests. Each is unlocked by playing real moves.

The rules are intentionally simple enough to explain during a school presentation.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Quest:
    key: str
    name: str
    description: str
    target: int = 1


QUESTS = [
    Quest('first_blood', 'First Blood', 'Capture an enemy piece'),
    Quest('first_check', 'First Check', 'Put your opponent in check'),
    Quest('knight', 'Knight’s Honor', 'Capture a piece with a knight'),
    Quest('castle', 'Royal Guard', 'Castle with your king'),
    Quest('collector', 'The Collector', 'Capture five pieces in one game', 5),
    Quest('promotion', 'The Long March', 'Promote a pawn'),
    Quest('first_game', 'First Steps', 'Finish your first game'),
    Quest('first_win', 'A Worthy Victory', 'Win a game'),
]


class QuestManager:
    """Remember completed quests; look for achievements in the move history."""

    def __init__(self, completed=None):
        valid = {quest.key for quest in QUESTS}
        self.completed = set(completed or []) & valid

    @classmethod
    def from_data(cls, data):
        if not isinstance(data, dict):
            return cls()
        return cls(data.get('completed', []))

    def to_data(self):
        return {'completed': sorted(self.completed)}

    def progress(self, game, color, key, mode='local', difficulty='medium',
                 undo_used=False, result='*'):
        own_moves = [event for event in game.events if event['color'] == color]
        captures = sum(bool(event['capture']) for event in own_moves)
        if key == 'first_blood':
            return min(captures, 1)
        if key == 'collector':
            return min(captures, 5)
        if key == 'first_check':
            return int(any(event['gave_check'] for event in own_moves))
        if key == 'knight':
            return int(any(event['kind'] == 'N' and event['capture'] for event in own_moves))
        if key == 'castle':
            return int(any(event['castle'] for event in own_moves))
        if key == 'promotion':
            return int(any(event['promotion'] for event in own_moves))
        if key == 'first_game':
            return int(bool(game.events) and (result != '*' or game.finished))
        if key == 'first_win':
            winner = {'1-0': 'w', '0-1': 'b'}.get(result)
            # Ignore a resignation before any meaningful play.
            return int(winner == color and len(game.events) >= 4)
        return 0

    def evaluate(self, game, colors, mode='local', difficulty='medium',
                 undo_used=False, result='*', game_id=None):
        """Return newly earned quests and whether saved progress changed."""
        newly_earned = []
        for quest in QUESTS:
            if quest.key in self.completed:
                continue
            if any(self.progress(game, color, quest.key, mode, difficulty,
                                 undo_used, result) >= quest.target for color in colors):
                self.completed.add(quest.key)
                newly_earned.append(quest)
        return newly_earned, bool(newly_earned)
