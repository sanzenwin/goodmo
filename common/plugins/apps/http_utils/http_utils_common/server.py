# -*- coding: utf-8 -*-
import json
import KBEngine
import socket
import urllib.parse
from io import StringIO
from functools import partial
from copy import copy, deepcopy
from . import status


class HTTPResponseException(Exception):
    pass


class HTTPResponse:
    DEFAULT_ERROR_CONTENT_TYPE = "text/html;charset=utf-8"

    def __init__(self, sock):
        self._sock = sock
        self.version = 'HTTP/1.1'
        self.status = 200
        self.body = b''
        self._headers = []

    def send_error(self, code):
        self.status = code
        self.add_header("Content-Type", self.DEFAULT_ERROR_CONTENT_TYPE)
        self.flush()

    def add_header(self, key, value):
        self._headers.append("%s: %s\r\n" % (key, value))

    def flush(self):
        self.add_header('Connection', 'close')
        self.add_header('Content-Length', len(self.body))
        cnt = '%s %d ok\r\n%s\r\n' % (self.version, self.status, ''.join(self._headers))
        self._sock.send(cnt.encode('latin-1', 'strict'))
        self._sock.send(self.body)
        self._sock.send(b'\r\n')


class Response:
    def __init__(self, data=None, status=status.HTTP_200_OK, headers=None, content_type='application/json'):
        self.data = data
        self.status = status
        self.headers = headers
        self.content_type = content_type

    def adapt(self, resp):
        if self.headers:
            for k, v in self.headers.items():
                resp.add_header(k, v)
        resp.add_header('Content-Type', self.content_type)
        resp.status = self.status
        if self.content_type == 'application/json':
            resp.body = bytes(json.dumps(self.data), "utf-8")
        else:
            resp.body = bytes(str(self.data), "utf-8")


def handler_404(request):
    return Response(data='404 Not Found.', status=status.HTTP_404_NOT_FOUND, content_type='text/html')


class HTTPRequest:
    MAX_LINE = 65536

    def __init__(self, sock, address):
        self._r_file = None
        self.method = None
        self.url = ''
        self.path = ''
        self.version = None
        self.error_code = None
        self.address = address
        self.ip = address[0]
        self.port = address[1]
        self.headers = {}
        self.params = {}
        self.data = {}

        if self.receive_bytes(sock):
            self.parse_request()

    def receive_bytes(self, sock):
        try:
            s = b''
            while True:
                data = sock.recv(self.MAX_LINE + 1)
                s += data
                if len(data) <= self.MAX_LINE + 1:
                    break
            self._r_file = StringIO(str(s, 'iso-8859-1'))
        except ConnectionResetError:
            return False
        return True

    @property
    def is_bad(self):
        return not self.url

    def mark_error(self, code):
        self.error_code = code

    @property
    def has_error(self):
        return self.error_code is not None

    def parse_request(self):
        line = self._r_file.readline(self.MAX_LINE + 1)
        if len(line) > self.MAX_LINE:
            self.mark_error(414)
            return
        words = line.rstrip('\r\n').split()
        if len(words) != 3:
            self.mark_error(400)
            return
        self.method, self.url, self.version = words
        code = self.parse_headers()
        if code:
            self.mark_error(code)
            return
        self.parse_params()
        if self.method == 'POST':
            self.parse_data()

    def parse_data(self):
        if self.headers.get("Content-Type") == "application/x-www-form-urlencoded":
            self.parse_form()
        elif self.headers.get("Content-Type") == "application/json":
            self.parse_json()

    def parse_form(self):
        while True:
            line = self._r_file.readline()
            if line in ('\r\n', '\n', ''):
                break
            for i in line.rstrip('\r\n').split('&'):
                words = i.split('=')
                self.data[words[0]] = words[1]

    def parse_json(self):
        data = ""
        while True:
            line = self._r_file.readline()
            if line in ('\r\n', '\n', ''):
                break
            data += line
        try:
            self.data = json.loads(data)
        except ValueError:
            pass

    def parse_params(self):
        pos = self.url.find('?')
        if pos != -1:
            for i in self.url[pos + 1:].split('&'):
                words = i.split('=')
                self.params[words[0]] = words[1]
            self.path = self.url[:pos]
        else:
            self.path = self.url

    def parse_headers(self):
        while True:
            line = self._r_file.readline(self.MAX_LINE + 1)
            if len(line) > self.MAX_LINE:
                return 414
            if line in ('\r\n', '\n', ''):
                break
            words = line.split(':', 1)
            self.headers[words[0].strip(' \r\n')] = words[-1].strip(' \r\n')
        return None

    def parse_param(self, key, value=None):
        return urllib.parse.unquote(self.params.get(key, value)) if key in self.params else value

    def param_copy(self):
        return copy(self.params)

    def data_copy(self):
        return deepcopy(self.data)


class HTTPServer:
    def __init__(self):
        self._sock = None
        self._handlers = {}

    def listen(self, address='127.0.0.1', port=80):
        assert not self._sock and port > 0
        self._sock = socket.socket()
        self._sock.bind((address, port))
        self._sock.listen(10)
        KBEngine.registerReadFileDescriptor(self._sock.fileno(), self.on_accept)

    def route(self, url, func):
        assert url and func and url not in self._handlers
        self._handlers[url] = func

    def on_accept(self, fileno):
        if self._sock.fileno() == fileno:
            sock, address = self._sock.accept()
            KBEngine.registerReadFileDescriptor(sock.fileno(), partial(self.on_receive, sock, address))

    def on_receive(self, sock, address, fileno):
        KBEngine.deregisterReadFileDescriptor(fileno)
        try:
            req = HTTPRequest(sock, address)
            if req.is_bad:
                return
            resp = HTTPResponse(sock)
            if req.has_error:
                resp.send_error(req.error_code)
            else:
                handler = self._handlers.get(req.path)
                if not handler:
                    handler = handler_404
                response = handler(req)
                response.adapt(resp)
                resp.flush()
        finally:
            sock.close()


def async_handler_404(promise):
    promise.done(Response(data='404 Not Found.', status=status.HTTP_404_NOT_FOUND, content_type='text/html'))


class Promise:
    def __init__(self, sock, req, resp):
        self.sock = sock
        self.req = req
        self.resp = resp

    def done(self, response):
        try:
            response.adapt(self.resp)
            self.resp.flush()
        finally:
            self.sock.close()


class HTTPServerAsync(HTTPServer):
    def on_receive(self, sock, address, fileno):
        KBEngine.deregisterReadFileDescriptor(fileno)
        need_close = True
        try:
            req = HTTPRequest(sock, address)
            if req.is_bad:
                return
            resp = HTTPResponse(sock)
            if req.has_error:
                resp.send_error(req.error_code)
            else:
                need_close = False
                handler = self._handlers.get(req.path)
                if not handler:
                    handler = async_handler_404
                handler(Promise(sock, req, resp))
        finally:
            if need_close:
                sock.close()
