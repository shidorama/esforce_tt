import string
from random import randint
from collections import OrderedDict
from twisted.internet import reactor
from twisted.web import server, resource
from twisted.internet.protocol import ServerFactory, Factory
from twisted.protocols.basic import LineReceiver
from datetime import datetime
from pickle import dump, load
from time import time
# from typing import

protocols = set()
users = {}
onlineUsers = set()
reservedNames = {'e', 'l', 'r',}
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

class User(object):
    def __init__(self, name, password):
        self.name = name
        self.password = password

    def auth(self, password):
        if self.password == password:
            return True
        return False


class ChatClient(object):
    def __init__(self):
        self.user = None
        self.authorized = False

    def exit(self):
        if self.authorized:
            onlineUsers.remove(self.user.name)

    def authorize(self):
        self.authorized = True
        onlineUsers.add(self.user.name)

    def send_message(self, timestamp, name, line):
        raise NotImplementedError()

    def register_user(self, login, password):
        if login in users or login in reservedNames:
            return False
        self.user = User(login, password)
        self.authorized = True
        users[self.user.name] = self.user
        save_users()
        return True

    def broadcast(self, line):
        timestamp = time()
        chatCache.push_line(timestamp, self.user.name, line)
        for client in protocols:
            if client.authorized and client is not self:
                client.send_message(timestamp, self.user.name, line)



class ChatClientTelnet(LineReceiver, ChatClient):
    MENU_MAIN = 0
    MENU_REGISTER = 1
    MENU_AUTH = 2
    MENU_REGISTER_LOGIN = 3
    MENU_REGISTER_PASSWORD = 4
    MENU_AUTH_LOGIN = 5
    MENU_AUTH_PASSWORD = 6

    CONNECTION_BANNER = b'Welcome to chat\r\nPlease login(l) or register(r)\r\n(e) is for exit\r\n'

    def __init__(self):
        super(ChatClientTelnet, self).__init__()
        self.menu_data = {}
        self.menu_position = self.MENU_MAIN

    def connectionMade(self):
        super(ChatClientTelnet, self).connectionMade()
        protocols.add(self)
        self.transport.write(self.CONNECTION_BANNER)

    def connectionLost(self, reason):
        self.exit()

    @staticmethod
    def filter_string(line):
        return ''.join(filter(lambda x: x in string.printable, line.decode('utf-8', 'ignore')))

    def lineReceived(self, line):
        line = self.filter_string(line)
        if line == 'e':
            # TODO: lose connection, drop user
            self.transport.loseConnection()
        if self.authorized:
            self.broadcast(line)
        else:
            self.menu(line)

    def menu(self, line):
        if self.menu_position == self.MENU_MAIN:
            if line == 'r':
                self.menu_position = self.MENU_REGISTER
            elif line == 'l':
                self.menu_position = self.MENU_AUTH
            else:
                self.transport.write(b'Wrong input!\r\nPlease login(l) or register(r)\r\n(e) is for exit\r\n')
        if self.menu_position == self.MENU_REGISTER:
            self.transport.write(b'Please enter your username:\r\n')
            self.menu_position = self.MENU_REGISTER_LOGIN
        elif self.menu_position == self.MENU_REGISTER_LOGIN:
            self.menu_data = {'name': line}
            self.menu_position = self.MENU_REGISTER_PASSWORD
            self.transport.write(b'Please enter password:\r\n')
        elif self.menu_position == self.MENU_REGISTER_PASSWORD:
            if not self.register_user(self.menu_data['name'], line):
                self.transport.write(b'Username is not available! Chose another:\r\n')
                self.menu_position = self.MENU_REGISTER_LOGIN
                return
            self.join()
        elif self.menu_position == self.MENU_AUTH:
            self.transport.write(b'Login:\r\n')
            self.menu_position = self.MENU_AUTH_LOGIN
        elif self.menu_position == self.MENU_AUTH_LOGIN:
            self.menu_data = {'name': line}
            self.transport.write(b'Enter password:\r\n')
            self.menu_position = self.MENU_AUTH_PASSWORD
        elif self.menu_position == self.MENU_AUTH_PASSWORD:
            login = self.menu_data['name']
            if users[login] in onlineUsers:
                self.transport.write(b'User is already online!\r\n')
                self.transport.loseConnection()
                return
            if login in users:
                if users[login].auth(line):
                    self.authorized = True
                    self.join()
                    return
            self.transport.write(b'Username or password does not match! Try again. Login:\r\n')
            self.menu_position = self.MENU_REGISTER_LOGIN

    def join(self):
        self.transport.write(b'Welcome to chat\r\n')
        for cc in chatCache.getCache():
            self.send_message(*cc)


    def send_message(self, timestamp, name, line):
        str_time = datetime.strftime(datetime.fromtimestamp(timestamp), '%H:%M')
        chat_line = "%s - %s: %s\r\n" % (str_time, name, line)
        self.transport.write(chat_line.encode())





class TNChatFactory(Factory):
    def buildProtocol(self, addr):
        return ChatClientTelnet()

def save_users():
    with open('users.json', 'wb') as fp:
        try:
            dump(users, fp)
        except IOError as e:
            raise

if __name__ == '__main__':
    save_users() # Remove this
    with open('users.json', 'rb') as fp:
        try:
            users = load(fp)
        except ValueError:
            pass
        except IOError as e:
            raise

    chatFactory = TNChatFactory()
    reactor.listenTCP(8050, chatFactory)
    reactor.run()