import unittest
from tempfile import TemporaryDirectory
from clock import ChessClock,display,PRESETS
from storage import StorageManager,DEFAULTS

class ClockStorage(unittest.TestCase):
    def test_clock(self):
        clock=ChessClock(60,2);clock.start('w');clock.switch('w')
        self.assertGreater(clock.left('w'),61.5)
        self.assertEqual(clock.active,'b');clock.pause()
    def test_unlimited(self):self.assertEqual(display(None),'∞')
    def test_presets(self):self.assertEqual(len(PRESETS),6)
    def test_settings(self):
        with TemporaryDirectory() as tmp:
            s=StorageManager(tmp);self.assertEqual(s.settings(),DEFAULTS)
            settings=s.settings();settings['coordinates']=False;s.save_settings(settings)
            self.assertFalse(s.settings()['coordinates'])
    def test_save_game(self):
        with TemporaryDirectory() as tmp:
            s=StorageManager(tmp);id=s.save_game({'record':[],'mode':'local'})
            self.assertEqual(s.latest()['id'],id)
            self.assertTrue((s.game_path).exists())
            s.save_game({'record':[1], 'mode':'local'}, id)
            self.assertEqual(s.latest()['record'],[1])
