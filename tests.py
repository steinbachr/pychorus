import unittest
from pychorus import PyChorus


class TestPyChorus(unittest.TestCase):
    def setUp(self):
        self.bob = PyChorus('tests/bob.mp3')
        self.arctic = PyChorus('tests/arctic_monkeys.mp3')

    def test_find_chorus(self):
        pass