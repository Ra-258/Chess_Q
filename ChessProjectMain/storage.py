"""Save one active chess game, simple settings and optional quests to JSON."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path


DEFAULTS = {
    'coordinates': True,
    'legal_moves': True,
    'last_move': True,
    'animations': True,
    'auto_queen': True,
    'autosave': True,
    'confirm': True,
}


class StorageManager:
    def __init__(self, folder=None):
        self.folder = Path(folder) if folder else Path.home() / '.chessprojectmain'
        self.folder.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.folder / 'settings.json'
        self.game_path = self.folder / 'game.json'
        self.quests_path = self.folder / 'quests.json'

    def _read(self, path, default=None):
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError, TypeError):
            return default

    def _write(self, path, data):
        # Write into a temporary file first to avoid half-written saves.
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        os.replace(temporary, path)

    def settings(self):
        return {**DEFAULTS, **(self._read(self.settings_path, {}) or {})}

    def save_settings(self, data):
        self._write(self.settings_path, data)

    def quest_progress(self):
        return self._read(self.quests_path, {})

    def save_quest_progress(self, data):
        self._write(self.quests_path, data)

    def save_game(self, data, game_id=None):
        """Save the current match. A new match replaces the last match."""
        game_id = game_id or uuid.uuid4().hex[:12]
        data = {**data, 'id': game_id,
                'updated': datetime.now().isoformat(timespec='minutes')}
        self._write(self.game_path, data)
        return game_id

    def latest(self):
        """Load the latest save, including a save from an older Chess version."""
        current = self._read(self.game_path)
        if isinstance(current, dict):
            return current

        # Earlier versions placed each game in games/<id>.json.
        last = self._read(self.folder / 'recent.json', {}) or {}
        old_id = last.get('id')
        if isinstance(old_id, str) and old_id.isalnum():
            return self._read(self.folder / 'games' / f'{old_id}.json')
        return None
