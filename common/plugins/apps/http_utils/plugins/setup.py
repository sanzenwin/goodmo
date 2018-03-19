import KBEngine
import plugins
from common.dispatcher import receiver
from kbe.signals import baseapp_ready
from kbe.core import Equalization
from http_utils.signals import http_setup
from http_utils_common.server import HTTPServerAsync, Response
from kbe.xml import settings_kbengine
from kbe.utils import internal_ip_address


@receiver(baseapp_ready)
def setup(signal, sender):
    indexes, conf = Equalization.getBaseIndexInfo("http_utils")
    if sender.groupIndex in indexes:
        KBEngine.setAppFlags(KBEngine.APP_FLAGS_NOT_PARTCIPATING_LOAD_BALANCING)
        server = HTTPServerAsync()
        index = indexes.index(sender.groupIndex)
        info = conf[index]
        ip = ""
        if info["externalIP"]:
            ip = settings_kbengine.baseapp.externalAddress.value
        if not ip:
            ip = internal_ip_address()
        port = info["port"]
        xml_conf = settings_kbengine.apps.http_utils
        ip = xml_conf.ip.value or ip
        port = xml_conf.port.value or port
        server.listen(ip, port)
        plugins.plugins.load_all_module("http_servers")
        http_setup.send(server, conf=dict(ip=ip, port=port))
        print("Starting development server at http://%s:%s" % (ip, port))
