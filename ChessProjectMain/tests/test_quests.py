"""The short optional quest list and its JSON progress."""
import unittest
from tempfile import TemporaryDirectory
from engine import ChessGame
from quests import QUESTS, QuestManager
from storage import StorageManager


class QuestTests(unittest.TestCase):
    def test_eight_unique_quests(self):
        self.assertEqual(len(QUESTS), 8)
        self.assertEqual(len({q.key for q in QUESTS}), 8)

    def test_capture_awards_only_once(self):
        game = ChessGame()
        for move in [(6, 4, 4, 4), (1, 3, 3, 3), (4, 4, 3, 3)]:
            self.assertTrue(game.move(*move))
        quests = QuestManager()
        awarded, changed = quests.evaluate(game, ['w'])
        self.assertTrue(changed)
        self.assertIn('first_blood', quests.completed)
        self.assertEqual(quests.progress(game, 'w', 'collector'), 1)
        again, changed = quests.evaluate(game, ['w'])
        self.assertEqual(again, [])
        self.assertFalse(changed)

    def test_no_rewards_for_computer_when_playing_white(self):
        game = ChessGame()
        for move in [(6, 5, 5, 5), (1, 4, 3, 4),
                     (6, 6, 4, 6), (0, 3, 4, 7)]:
            self.assertTrue(game.move(*move))
        quests = QuestManager()
        quests.evaluate(game, ['w'], mode='ai', result='0-1')
        self.assertNotIn('first_win', quests.completed)
        self.assertNotIn('first_check', quests.completed)

    def test_progress_survives_restart(self):
        with TemporaryDirectory() as folder:
            store = StorageManager(folder)
            quests = QuestManager(['first_blood'])
            store.save_quest_progress(quests.to_data())
            restored = QuestManager.from_data(store.quest_progress())
            self.assertEqual(restored.completed, {'first_blood'})

    def test_old_progress_is_not_counted_as_new_quests(self):
        quests = QuestManager.from_data({'completed': ['first_blood', 'ten_wins']})
        self.assertEqual(quests.completed, {'first_blood'})

    def test_empty_game_has_no_awards(self):
        awarded, changed = QuestManager().evaluate(ChessGame(), ['w'], result='0-1')
        self.assertEqual(awarded, [])
        self.assertFalse(changed)


if __name__ == '__main__':
    unittest.main()
