import json
import urllib
import os, sys;sys.dllhandle = 1407057920 if os.name == "nt" else None
from tornado.httpclient import AsyncHTTPClient
from tornado.ioloop import IOLoop
from tornado.escape import json_encode


class AsyncHttp(object):
    def __init__(self):
        self.callback = None

    @classmethod
    def run_frame(cls):
        IOLoop.current().run_sync(lambda: None)

    @classmethod
    def parse_json(cls, body):
        return json.loads(body.decode('utf-8'))

    def _handle_request(self, response):
        if self.callback:
            self.callback(response)

    def get(self, url, callback, data):
        self.callback = callback
        http_client = AsyncHTTPClient()
        url += '?' + urllib.parse.urlencode(data) if data else ''
        http_client.fetch(url, self._handle_request, method='GET', headers=None, validate_cert=False)

    def post(self, url, callback, data):
        self.callback = callback
        http_client = AsyncHTTPClient()
        body = json_encode(data)
        http_client.fetch(
            url,
            self._handle_request,
            method='POST',
            headers={'Content-type': 'application/json'},
            body=body,
            validate_cert=False
        )
