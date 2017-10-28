from random import randint

from twisted.internet import reactor
from twisted.web.http import HTTPFactory
from twisted.internet.protocol import ServerFactory, Factory
from twisted.protocols.basic import LineReceiver
from json import load, dump
from datetime import datetime
# from typing import

protocols = set()

class Chat(LineReceiver):
    def __init__(self):
        super(Chat, self).__init__()
        # self.authorized = False
        self.authorized = True
        self.name = 'User-%s' % randint(1, 1000)

    def connectionMade(self):
        super(Chat, self).connectionMade()
        protocols.add(self)

    def lineReceived(self, line):
        if self.authorized:
            self.broadcast(line)

    def broadcast(self, line):
        time = datetime.strftime(datetime.now(), '%H:%M')
        for client in protocols:
            if client.authorized and client is not self:
                client.sendMessage(self.name, time, line)

    def sendMessage(self, name, time, line):
        chatLine = "%s - %s: %s\r\n" % (time, name, line.decode('utf-8', 'ignore'))
        self.transport.write(chatLine.encode())





class TNChatFactory(Factory):
    def buildProtocol(self, addr):
        return Chat()

if __name__ == '__main__':
    with open('users.json', 'w+') as fp:
        try:
            users = load(fp)
        except ValueError:
            users = {}
        except IOError as e:
            raise

    httpFactory  = HTTPFactory()
    chatFactory = TNChatFactory()
    reactor.listenTCP(8080, httpFactory)
    reactor.listenTCP(8050, chatFactory)
    reactor.run()