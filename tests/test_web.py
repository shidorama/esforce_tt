from json import loads
from unittest import TestCase

from mock import Mock, patch
from voluptuous import Schema

from common import ChatCache
from user import User
from webChat import Register, ChatChat


class TestWeb(TestCase):
    def testRegistration(self):
        """Basic positive case for registration

        :return:
        """
        request_mock = Mock()
        content_mock = Mock()
        request_mock.configure_mock(content=content_mock)
        content_mock.configure_mock(read=lambda: b'{"username":"user", "password":"pass"}')
        user_mock = Mock()
        user_mock.configure_mock(register=lambda: True)
        user_mock.return_value = user_mock
        test_schema = Schema({'token': str}, required=True)
        with patch('webChat.User', user_mock):
            reg_service = Register()
            result = reg_service.render_POST(request_mock)
            test_schema(loads(result))

    def testChat(self):
        """Testing basic case for chat over web
        """
        request_mock = Mock()
        content_mock = Mock()
        request_mock.configure_mock(content=content_mock, getHeader=lambda x: 'Bearer _token_')
        content_mock.configure_mock(read=lambda: b'{"message": "Hello"}')
        chat_cache = ChatCache()
        user = User('testUser', 'password')
        wubt = {"_token_": {'updated': 0, 'user': user, 'token': "_token_"}}
        expected_result = [[100, 'testUser', 'Hello'], ]
        with patch('webChat.web_users_by_token', wubt), \
                patch('webChat.chat_cache', chat_cache), \
                patch('webChat.time', lambda: 100):
            chat_service = ChatChat()
            result = chat_service.render_POST(request_mock)
            result_object = loads(result)
            self.assertEqual(result_object, expected_result)
