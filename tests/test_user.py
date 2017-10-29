from unittest import TestCase

from mock import patch

from user import User


class TestUser(TestCase):
    def testAuth(self):
        """Testing both basic positive and negative cases for user auth method
        """
        test_user = User('test', 'password')
        self.assertTrue(test_user.auth('password'))
        self.assertFalse(test_user.auth('password1'))

    def testRegistration(self):
        """Test user registration, positive and negative
        """
        test_user = User('testUser', 'password')
        users = {'testUser': object()}
        save_calls = []

        def save_users_mock():
            save_calls.append('1')

        with patch('user.users', users), patch('user.save_users', save_users_mock):
            self.assertFalse(test_user.register())
            self.assertEqual(len(save_calls), 0)

        with patch('user.users', {}), patch('user.save_users', save_users_mock):
            self.assertTrue(test_user.register())
            self.assertEqual(len(save_calls), 1)
            self.assertTrue('testUser' in users)
