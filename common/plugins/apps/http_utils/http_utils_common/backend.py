from common.dispatcher import receiver
from http_utils.signals import http_setup
from http_utils_common.server import Response

handler_map = {}


def handler(name):
    def wrapper(func):
        handler_map[name] = func
        return func

    return wrapper


@receiver(http_setup)
def url(signal, server, conf):
    server.route("/command/", command)


def command(promise):
    data = promise.req.data_copy()
    operation = data.pop("operation", "")
    func = handler_map.get(operation, None)
    if func:
        func(promise, data)
    else:
        promise.done(Response(data="unknown operation.", content_type='application/text'))
    print(promise.req.method.upper(), promise.req.url, operation)
