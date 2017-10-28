"""
Common variables and methods
"""
import string
from pickle import dump
from time import time
from typing import Union

WEB_TIMEOUT = 60
CACHE_SIZE = 100

users = {}
onlineUsers = set()
protocols = set()
web_users_by_username = {}
web_users_by_token = {}


class ChatCache(object):
    """
    Chat cache. Usually used by web clients or when telnet client is just connected
    """

    def __init__(self):
        self.cache = []

    def push_line(self, timestamp, user, line):
        """Push line to cache, while also expunging old lines if they are over the limit

        :param timestamp:
        :param user:
        :param line:
        :return:
        """
        self.cache.append((timestamp, user, line))
        while len(self.cache) > CACHE_SIZE:
            self.cache.pop(0)

    def getCache(self):
        return self.cache


chatCache = ChatCache()


def save_users():
    """As we're using pickle instead of full-fledged DB - this mean to dump users on disk after each modification
    """
    with open('users.pickle', 'wb') as fp:
        try:
            dump(users, fp)
        except IOError as e:
            raise


def clean_web_clients():
    """Removes seb clients that are stall i.e. those who hadn't communicated in some time (defined by WEB_TIMEOUT)
    """
    now = time()
    usernames = list(web_users_by_username.keys())
    for client_name in usernames:
        client = web_users_by_username[client_name]
        if now - client['updated'] > WEB_TIMEOUT:
            web_users_by_username.pop(client['user'].name)
            web_users_by_token.pop(client['token'])
            onlineUsers.remove(client['user'].name)
            print('Deleted %s' % client)

def filter_string(line: Union[bytes, str]) -> str:
    """Cleans bytestring of all that's not in 'printable' and returns it as string

    :param line: bytes received
    :return: result string
    """
    raw_str = line
    if isinstance(line, bytes):
        raw_str = line.decode('utf-8', 'ignore')
    return ''.join(filter(lambda x: x in string.printable, raw_str))
