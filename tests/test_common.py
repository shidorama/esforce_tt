from unittest import TestCase

from mock import mock

from common import ChatCache, CACHE_SIZE, clean_web_clients, WEB_TIMEOUT, filter_string


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
        """
        cache = ChatCache()
        indexes = list(range(CACHE_SIZE * 2))
        lines = [(i, 'username', 'test') for i in indexes]
        for line in lines:
            cache.push_line(*line)
            self.assertLessEqual(len(cache.getCache()), CACHE_SIZE)
        self.assertEqual(cache.getCache(), lines[CACHE_SIZE:])


class TestGenericCommonMethods(TestCase):
    def testWebClientsCleaning(self):
        userMock = mock.Mock()
        userMock.name = 'user'
        user = {
            'token': 'test',
            'updated': 1,
            'user': userMock
        }
        wubu = {'user': user}
        wubt = {'test': user}
        ou = {'user'}

        def time_mock():
            return 1 + WEB_TIMEOUT

        with mock.patch('common.web_users_by_username', wubu), \
                mock.patch('common.web_users_by_token', wubt), \
                mock.patch('common.online_users', ou), \
                mock.patch('common.time', time_mock):
            clean_web_clients()
            self.assertEqual(len(wubu), 0)
            self.assertEqual(len(wubt), 0)
            self.assertEqual(len(ou), 0)

    def testFilterString(self):
        """Testing if string filtering is working OK and leaving only allowed chars from full range of UTF chars
        """
        test_string = ''.join([chr(i) for i in range(1114111)])
        new_string = filter_string(test_string)
        self.assertEqual(len(new_string), 95)
