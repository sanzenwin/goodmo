# -*- coding: utf-8 -*-
import KBEngine
import settings
from common.utils import server_time, Event, Bytes
from kbe.protocol import Base, BaseMethodExposed, Property, Client, ClientMethod, Type


class Upload:
    base = Base(
        reqUpload=BaseMethodExposed(Type.UNICODE),
    )

    client = Client(
        onUpload=ClientMethod(Type.UNICODE, Type.UNICODE)
    )

    uploadMap = Property(
        Type=Type.PYTHON,
        Flags=Property.Flags.BASE
    )

    def reqUpload(self, key, size):
        if size > settings.Avatar.uploadSizeUpLimit:
            return
        self.uploadMap[key]


class UploadFile:
    def __init__(self, key, size):
        self.key = key
        self.size = size

    def receive(self, d):
        pass
