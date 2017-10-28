from pickle import dump
users = {}
onlineUsers = set()
CACHE_SIZE = 100

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
    with open('users.json', 'wb') as fp:
        try:
            dump(users, fp)
        except IOError as e:
            raise

