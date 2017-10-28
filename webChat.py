import json
from voluptuous import Schema
from twisted.web import server, resource
from twisted.web.resource import ErrorPage
from common import users, chatCache, onlineUsers
from time import time
from user import User

web_users = {}

WEB_TIMEOUT = 60

class ChatResource(resource.Resource):
    def getChild(self, path, request):
        str_path = path.decode()
        child =  self.children.get(str_path)
        if not child:
            super(ChatResource, self).getChild(path, request)
        return child

    def getJsonContent(self, requset):
        content = requset.content.read()
        try:
            data = json.loads(content)
        except ValueError:
            return False
        return data


class Register(ChatResource):
    isLeaf = True
    def render_GET(self, request):
        pass

    def render_POST(self, request):
        print(request)
        pass

class Auth(ChatResource):

    def render_POST(self, request):
        schema = Schema({"username": str, "password": str}, required=True)
        data = self.getJsonContent(request)
        schema(data)
        username = data.get('username')
        password = data.get('password')
        if username in users:
            user = users.get(username)
            user.auth(password)

        return ErrorPage(400,b'Shit!', b'Shit2!').render(request)

    def render_GET(self, request):
        return b'asda'


class WebChat(ChatResource):
    isLeaf = True
    def render_GET(self, request):
        return b'{}a'




root = ChatResource()
root.putChild('auth', Auth())