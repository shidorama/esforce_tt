from unittest import TestCase
from common import ChatCache

class TestChatCache(TestCase):
    def testAdditon(self):
        cache = ChatCache()
        indexes = list(range(10))
        lines = [(i, 'test', 'test') for i in indexes]
        for line in lines:
            cache.push_line(*line)
        self.assertEqual(cache.getCache(), lines)