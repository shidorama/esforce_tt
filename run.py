import os
from pickle import load

from twisted.internet import reactor, task
from twisted.web import server

from chat import TNChatFactory
from common import users, clean_web_clients
from webChat import root

if __name__ == '__main__':
    if os.path.getsize('users.pickle') > 0:
        with open('users.pickle', 'rb') as fp:
            try:
                users.update(**load(fp))
            except ValueError:
                pass
            except IOError as e:
                raise

    http_server = server.Site(root)
    chatFactory = TNChatFactory()
    cleaner = task.LoopingCall(clean_web_clients)
    cleaner.start(10.0, False)
    reactor.listenTCP(8050, chatFactory)
    reactor.listenTCP(8080, http_server)
    reactor.run()
