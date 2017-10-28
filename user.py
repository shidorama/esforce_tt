from common import users, save_users

class User(object):
    def __init__(self, name, password):
        self.name = name
        self.password = password

    def auth(self, password):
        if self.password == password:
            return True
        return False

    def register(self):
        if self.name in users:
            return False
        users[self.user.name] = self.user
        save_users()
        return True
