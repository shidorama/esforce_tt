import string
from datetime import datetime
from time import time

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

from common import onlineUsers, chatCache, users, protocols, filter_string
from user import User



class ChatClient(object):
    def __init__(self):
        self.user = None
        self.authorized = False

    def exit(self):
        """Removes user from online users if he authorized
        """
        if self.authorized:
            onlineUsers.remove(self.user.name)

    def authorize(self):
        """Set user state to authorized and add his login to online users list

        :return:
        """
        self.authorized = True
        onlineUsers.add(self.user.name)

    def send_message(self, timestamp: float, name: str, line: str):
        """Send message to current user

        :param timestamp: timestamp of message
        :param name: nick or login of sender
        :param line: message itself
        :return:
        """
        raise NotImplementedError()

    def register_user(self, login: str, password: str) -> bool:
        """Register user into database

        :param login: username
        :param password: password of the user
        :return: result of the registration
        """
        self.user = User(login, password)
        return self.user.register()

    def broadcast(self, line: str):
        """Send message to all telnet clients and add message to chat cache for web clients

        :param line: message to broadcast
        """
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


    def lineReceived(self, line: bytes):
        """Entry point for data received on socket

        data is cleaned and the then reacted upon
        :param line: line received from socket
        """
        line = filter_string(line)
        if line == 'e':
            self.transport.loseConnection()
        if self.authorized:
            self.broadcast(line)
        else:
            self.menu(line)

    def menu(self, line):
        """Big and ugly function which works with login and registration process

        Flow is as follows
        Start -> register -> enter login -> enter password -> if user can be registered -> exit to chat
        |                                           <--- goto register <---- else
        |
        -> login -> enter login -> enter password -> if auth OK -> exit to chat\
                            <----- goto login <------else

        :param line: line received
        """
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
            self.authorize()
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
            if login in onlineUsers:
                self.transport.write(b'User is already online!\r\n')
                self.transport.loseConnection()
                return
            if login in users:
                if users[login].auth(line):
                    self.user = users[login]
                    self.authorize()
                    self.join()
                    return
            self.transport.write(b'Username or password does not match! Try again. Login:\r\n')
            self.menu_position = self.MENU_REGISTER_LOGIN

    def join(self):
        """displays welcome banner and prints out chat cache

        """
        self.transport.write(b'Welcome to chat\r\n')
        for cc in chatCache.getCache():
            self.send_message(*cc)

    def send_message(self, timestamp: float, name: str, line: str):
        """Formats message and then writes it to client's socket
        """
        str_time = datetime.strftime(datetime.fromtimestamp(timestamp), '%H:%M:%S')
        chat_line = "%s - %s: %s\r\n" % (str_time, name, line)
        self.transport.write(chat_line.encode())


class TNChatFactory(Factory):
    def buildProtocol(self, addr):
        return ChatClientTelnet()



