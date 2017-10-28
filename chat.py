from twisted.internet import reactor
from twisted.web.http import HTTPFactory
from twisted.internet.protocol import ServerFactory, Factory
from twisted.protocols.basic import LineReceiver

class Chat(LineReceiver):
    pass


class TNChatFactory(Factory):
    def buildProtocol(self, addr):
        return Chat()


httpFactory  = HTTPFactory()
chatFactory = ''


reactor.listenTCP(8080, httpFactory)
reactor.listenTCP(8050, )