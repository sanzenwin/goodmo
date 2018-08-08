import settings
from common.dispatcher import receiver
from http_utils.signals import http_setup
from http_utils_common.server import Response
from . import status

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
    white = set(settings.Backend.whiteList)
    if "*" not in white and promise.req.ip not in white:
        promise.done(
            Response(data="permissions denied!", status=status.HTTP_403_FORBIDDEN, content_type='application/text'))
        return
    data = promise.req.data_copy()
    operation = data.pop("operation", "")
    func = handler_map.get(operation, None)
    if func:
        func(promise, data)
    else:
        promise.done(Response(data="unknown operation.", content_type='application/text'))
    print(promise.req.method.upper(), promise.req.url, operation)
