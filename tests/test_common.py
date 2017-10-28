from unittest import TestCase
from mock import mock

from common import ChatCache, CACHE_SIZE, clean_web_clients

class TestChatCache(TestCase):
    def testAdditon(self):
        """Test if data we're pushing into cache gets there in correct order

        :return:
        """
        cache = ChatCache()
        indexes = list(range(10))
        lines = [(i, 'test', 'test') for i in indexes]
        for line in lines:
            cache.push_line(*line)
        self.assertEqual(cache.getCache(), lines)

    def testOverflow(self):
        """Tests if overflow is working correctly and cache size is always below limit

        :return:
        """
        cache = ChatCache()
        indexes = list(range(CACHE_SIZE*2))
        lines = [(i, 'username', 'test') for i in indexes]
        for line in lines:
            cache.push_line(*line)
            self.assertLessEqual(len(cache.getCache()), CACHE_SIZE)
        self.assertEqual(cache.getCache(), lines[CACHE_SIZE:])

class TestGenericCommonMethods(TestCase):
    def testWebClientsCleaning(self):
        user = {
            'token': 'test',
            'updated': 1,
            'user': mock.MagicMock(name='user')
        }
        wubu = {'user': user}
        wubt = {'test': user}
        ou = {'user'}
        def time_mock():
            return 10
        with mock.patch('common.web_users_by_username', wubu), \
            mock.patch('common.web_users_by_token', wubt), \
            mock.patch('common.online_users', ou), \
            mock.patch('common.time', time_mock):
            clean_web_clients()
