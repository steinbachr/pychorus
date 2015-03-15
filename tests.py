import unittest
from pychorus import PyChorus


class TestPyChorus(unittest.TestCase):
    def setUp(self):
        self.bob = PyChorus('tests/bob.wav')
        self.arctic = PyChorus('tests/arctic_monkeys.wav')

    def test_find_bridge_end(self):
        song_obj = self.bob.song
        # give ourself a margin of error of a few seconds (occurs somewhere between 3:24 - 3:28) (4:35 length)
        self.assertTrue(204 <= song_obj._find_bridge_end() <= 208)

        # 2:11 - 2:14 (3:03 length)
        song_obj = self.arctic.song
        self.assertTrue(131 <= song_obj._find_bridge_end() <= 134)

    def test_find_chorus(self):
        pass