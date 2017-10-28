from pickle import dump
from time import time
from copy import copy

users = {}
onlineUsers = set()
CACHE_SIZE = 100
protocols = set()
web_users_by_username = {}
web_users_by_token = {}
WEB_TIMEOUT = 60


class ChatCache(object):
    def __init__(self):
        self.cache = []

    def push_line(self, timestamp, user, line):
        self.cache.append((timestamp, user, line))
        while len(self.cache) > CACHE_SIZE:
            self.cache.pop(-1)

    def getCache(self):
        return self.cache

chatCache = ChatCache()

def save_users():
    with open('users.pickle', 'wb') as fp:
        try:
            dump(users, fp)
        except IOError as e:
            raise
        print('Dumped %s' % users)

def clean_web_clients():
    print('Cleansing!')
    now = time()
    usernames = list(web_users_by_username.keys())
    for client_name in usernames:
        client = web_users_by_username[client_name]
        if now - client['updated'] > WEB_TIMEOUT:
            web_users_by_username.pop(client['user'].name)
            web_users_by_token.pop(client['token'])
            onlineUsers.remove(client['user'].name)
            print('Deleted %s' % client)

