import json
from hashlib import md5
from time import time
from uuid import uuid1

from twisted.web import resource
from twisted.web.resource import ErrorPage
from voluptuous import Schema

from common import users, chatCache, onlineUsers, protocols, web_users_by_token, web_users_by_username
from user import User



class ChatResource(resource.Resource):
    def render_OPTIONS(self, request):
        request.setHeader('allow', 'OPTIONS, GET, HEAD, POST')
        request.setHeader('Access-Control-Allow-Methods', request.getHeader('access-control-request-method'))
        request.setHeader('Access-Control-Allow-Headers', request.getHeader('access-control-request-headers'))
        request.setHeader('Access-Control-Allow-Origin', request.getHeader('origin'))
        return b''


    def getChild(self, path, request):
        str_path = path.decode()
        child = self.children.get(str_path)
        if not child:
            super(ChatResource, self).getChild(path, request)
        return child

    def render(self, request):
        request.setHeader('content-type', 'application/json')
        request.setHeader('Access-Control-Allow-Methods', request.getHeader('access-control-request-method'))
        request.setHeader('Access-Control-Allow-Headers', request.getHeader('access-control-request-headers'))
        request.setHeader('Access-Control-Allow-Origin', request.getHeader('origin'))
        return super(ChatResource, self).render(request)

    def getJsonContent(self, requset):
        content = requset.content.read()
        try:
            data = json.loads(content)
        except ValueError:
            return False
        return data


class UserResource(ChatResource):
    def activate_user(self, username, user):
        onlineUsers.add(username)
        token = md5(uuid1().bytes).hexdigest()
        data = {
            'token': token,
            'updated': time(),
            'user': user
        }
        web_users_by_token[token] = data
        web_users_by_username[username] = data
        return token


class Register(UserResource):
    isLeaf = True

    def render_POST(self, request):
        schema = Schema({"username": str, "password": str}, required=True)
        data = self.getJsonContent(request)
        schema(data)
        username = data.get('username')
        password = data.get('password')
        if username not in users:
            user = User(username, password)
            if user.register():
                token = self.activate_user(username, user)
                return json.dumps({'token': token}).encode()


class Auth(UserResource):
    isLeaf = True

    def render_POST(self, request):
        schema = Schema({"username": str, "password": str}, required=True)
        data = self.getJsonContent(request)
        schema(data)
        username = data.get('username')
        password = data.get('password')
        if username in users:
            user = users.get(username)
            if username not in onlineUsers or username in web_users_by_username:
                if username in web_users_by_username:
                    client = web_users_by_username[username]
                    web_users_by_username.pop(client['user'].name)
                    web_users_by_token.pop(client['token'])
                if user.auth(password):
                    token = self.activate_user(username, user)
                    return json.dumps({'token': token}).encode()
        return ErrorPage(400, b'Shit!', b'Shit2!').render(request)


class AuthorizedResources(ChatResource):
    def check_auth(self, request):
        raw_auth = request.requestHeaders.getRawHeaders('authorization')
        for auth_item in raw_auth:
            auth = auth_item.split()
            if len(auth) == 2:
                if auth[1] in web_users_by_token:
                    web_users_by_token[auth[1]]['updated'] = time()
                    return web_users_by_token[auth[1]]['user']
        return self.not_authorized(request)

    def not_authorized(self, request):
        request.setResponseCode(401)
        return b''


class ActiveUsers(AuthorizedResources):
    isLeaf = True

    def render_GET(self, request):
        user = self.check_auth(request)
        if user:
            return json.dumps(list(onlineUsers)).encode()
        return user


class ChatChat(AuthorizedResources):
    isLeaf = True

    def render_GET(self, request):
        user = self.check_auth(request)
        if user:
            return json.dumps(chatCache.getCache()).encode()
        return user

    def render_POST(self, request):
        user = self.check_auth(request)
        if user:
            data = self.getJsonContent(request)
            schema = Schema({'message': str}, required=True)
            schema(data)
            message = data.get('message')
            timestamp = time()
            chatCache.push_line(timestamp, user.name, message)
            for client in protocols:
                if client.authorized:
                    client.send_message(timestamp, user.name, message)
            return self.render_GET(request)
        return user


root = ChatResource()
root.putChild('auth', Auth())
root.putChild('register', Register())
root.putChild('users', ActiveUsers())
root.putChild('chat', ChatChat())
