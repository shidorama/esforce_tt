from common import users, save_users, filter_string

reservedNames = {'e', 'l', 'r', }


class User(object):
    def __init__(self, name, password):
        self.name = filter_string(name)
        self.password = password

    def auth(self, password):
        if self.password == password:
            return True
        return False

    def register(self):
        if self.name in users or self.name in reservedNames:
            return False
        users[self.name] = self
        save_users()
        return True
