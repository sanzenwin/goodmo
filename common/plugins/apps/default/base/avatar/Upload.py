# -*- coding: utf-8 -*-
from kbe.protocol import Base, BaseMethodExposed, Property, Client, ClientMethod, Type
from upload_default import UploadManager


class Upload:
    base = Base(
        reqUpload=BaseMethodExposed(Type.UNICODE, Type.UNICODE, Type.UINT32),
        reqUploadProcess=BaseMethodExposed(Type.UINT32, Type.BLOB)
    )

    client = Client(
        onUpload=ClientMethod(Type.UNICODE, Type.UINT32, Type.UINT32, Type.UINT32),
        onUploadProcess=ClientMethod(Type.UINT32, Type.UINT32, Type.UINT32)
    )

    def __init__(self):
        super().__init__()
        self.uploadManager = UploadManager(self)

    def reqUpload(self, fileType, key, size):
        file = self.uploadManager.get_file(fileType, key, size)
        if file is not None:
            self.client.onUpload(*file.begin())

    def reqUploadProcess(self, fileno, data):
        file = self.uploadManager.receive(fileno, data)
        if file is not None:
            self.client.onUploadProcess(*file.process())
