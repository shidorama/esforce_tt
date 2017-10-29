import json
from hashlib import md5
from time import time
from typing import Dict, List, Union
from uuid import uuid1

from twisted.web import resource
from twisted.web.http import Request
from voluptuous import Schema, error

from common import users, chat_cache, online_users, protocols, web_users_by_token, web_users_by_username, filter_string
from user import User


class ChatResource(resource.Resource):
    def __init__(self):
        super(ChatResource, self).__init__()
        self.data = None

    def render_OPTIONS(self, request: Request) -> bytes:
        """basic options request. No body.

        :param request:
        :return:
        """
        # request.setHeader('allow', 'OPTIONS, GET, HEAD, POST')
        return b''

    def getChild(self, path: str, request: Request) -> resource.Resource:
        """gets child resource from root to get answer

        :return: target resource
        """
        str_path = path.decode()
        child = self.children.get(str_path)
        if not child:
            super(ChatResource, self).getChild(path, request)
        return child

    def render(self, request: Request) -> bytes:
        """We're adding some CORS headers for future use, also we're sending content-type

        """
        request.setHeader('content-type', 'application/json')
        acrm = request.getHeader('access-control-request-method')
        if acrm:
            request.setHeader('Access-Control-Allow-Methods', acrm)
        acrh = request.getHeader('access-control-request-headers')
        if acrh:
            request.setHeader('Access-Control-Allow-Headers', acrh)
        origin = request.getHeader('origin')
        if origin:
            request.setHeader('Access-Control-Allow-Origin', origin)
        return super(ChatResource, self).render(request)

    def get_json_content(self, requset: Request) -> Union[List, Dict, bool]:
        """loads raw data from request and tries to parse it as JSON

        :param requset:
        :return:
        """
        content = requset.content.read()
        try:
            data = json.loads(content)
        except ValueError:
            return False
        return data

    def abort(self, request: Request, code: int, message: str):
        request.setResponseCode(code)
        error = {
            "code": code,
            "message": message
        }
        return json.dumps(error).encode()

    def is_parseable_and_valid(self, request: Request, schema: Schema) -> Union[bool, bytes]:
        data = self.get_json_content(request)
        if not data:
            return self.abort(request, 422, 'Cannot parse JSON')
        try:
            schema(data)
        except error.MultipleInvalid as e:
            return self.abort(request, 422, 'Data schema does not match')
        self.data = data
        return True


class UserResource(ChatResource):
    """
    All the resources that can generate access tokens
    """

    def activate_user(self, username: str, user: User) -> str:
        """generates bearer token for user, adds user to online users and adds special object to web users pools

        generated token remains active as long as user is active in web pools
        :param username:
        :param user:
        :return:
        """
        online_users.add(username)
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

    def render_POST(self, request: Request) -> bytes:
        """tries to register new user

        :param request:
        :return:
        """
        schema = Schema({"username": str, "password": str}, required=True)
        check_result = self.is_parseable_and_valid(request, schema)
        if check_result is not True:
            return check_result
        username = self.data.get('username')
        password = self.data.get('password')
        if username not in users:
            user = User(username, password)
            if user.register():
                token = self.activate_user(username, user)
                return json.dumps({'token': token}).encode()
        return self.abort(request, 400, 'Cannnot register user. Username already exists or not allowed.')


class Auth(UserResource):
    isLeaf = True

    def render_POST(self, request: Request) -> bytes:
        """Authorize user and generates access token for him to use.

        Token is valid while user is submitting timely requests
        :param request:
        :return:
        """
        schema = Schema({"username": str, "password": str}, required=True)
        check_result = self.is_parseable_and_valid(request, schema)
        if check_result is not True:
            return check_result
        username = self.data.get('username')
        password = self.data.get('password')
        if username in users:
            user = users.get(username)
            if username not in online_users or username in web_users_by_username:
                if username in web_users_by_username:
                    client = web_users_by_username[username]
                    web_users_by_username.pop(client['user'].name)
                    web_users_by_token.pop(client['token'])
                if user.auth(password):
                    token = self.activate_user(username, user)
                    return json.dumps({'token': token}).encode()
        return self.abort(request, 400, 'Cannot authorize user. Username/password pair invalid.')


class AuthorizedResources(ChatResource):
    def check_auth(self, request: Request) -> Union[bytes, User]:
        """Checks is user submitted access token and this token is valid

        """
        raw_auth = request.getHeader('authorization')
        auth = raw_auth.split()
        if len(auth) == 2:
            if auth[1] in web_users_by_token:
                web_users_by_token[auth[1]]['updated'] = time()
                return web_users_by_token[auth[1]]['user']
        return self.abort(request, 401, "You're not authorized")


class ActiveUsers(AuthorizedResources):
    isLeaf = True

    def render_GET(self, request: Request) -> bytes:
        """Returns list of online users

        """
        user = self.check_auth(request)
        if isinstance(user, User):
            return json.dumps(list(online_users)).encode()
        return user


class ChatChat(AuthorizedResources):
    isLeaf = True

    def render_GET(self, request: Request) -> bytes:
        """Returns all of the chat cache

        :param request:
        :return:
        """
        user = self.check_auth(request)
        if isinstance(user, User):
            return json.dumps(chat_cache.getCache()).encode()
        return user

    def render_POST(self, request: Request) -> bytes:
        """Submits message from user to chat and returns chat cache

        :param request:
        :return:
        """
        user = self.check_auth(request)
        if isinstance(user, User):
            schema = Schema({'message': str}, required=True)
            check_result = self.is_parseable_and_valid(request, schema)
            if check_result is not True:
                return check_result
            message = filter_string(self.data.get('message'))
            timestamp = time()
            chat_cache.push_line(timestamp, user.name, message)
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
