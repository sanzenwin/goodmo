import settings
from abc import ABCMeta, abstractmethod
from weakref import proxy


class UploadManager:
    file_types = dict()

    @classmethod
    def register(cls, file_type):
        def wrapper(c):
            cls.file_types[file_type] = c
            return c
        return wrapper

    def __init__(self, entity):
        self.entity = proxy(entity)
        self.index = 0
        self.key_map = dict()
        self.file_map = dict()

    def get_file(self, file_type, key, size):
        file_class = self.file_types.get(file_type)
        if file_class is None:
            return None
        if size > file_class.upload_size_upLimit or size <= 0:
            return None
        file = self.key_map.get(key)
        if file is None:
            self.index += 1
            file = file_class(self, key, self.index, size)
            self.key_map[key] = file
            self.file_map[file.fileno] = file
            return file
        elif not isinstance(file, file_class):
            return None
        return file

    def check_completed(self, file):
        if file.is_completed:
            del self.key_map[file.key]
            del self.file_map[file.fileno]

    def receive(self, fileno, data):
        file = self.file_map.get(fileno)
        if file is None or len(data) > file.upload_size_chunk:
            return None
        file.receive(data)
        self.check_completed(file)
        return file


class UploadFile(metaclass=ABCMeta):
    upload_size_upLimit = settings.Avatar.uploadSizeUpLimit
    upload_size_chunk = settings.Avatar.uploadSizeChunk

    def __init__(self, manager, key, fileno, size):
        self.__manager = proxy(manager)
        self.key = key
        self.fileno = fileno
        self.size = size
        self.data = bytes()

    @property
    def entity(self):
        return self.__manager.entity

    def begin(self):
        return (self.key,) + self.process()

    def process(self):
        return self.fileno, len(self.data), min(self.upload_size_chunk, self.size - len(self.data))

    @property
    def is_completed(self):
        return len(self.data) == self.size

    @abstractmethod
    def on_completed(self):
        pass

    def receive(self, data):
        left = max(self.size - len(self.data), 0)
        self.data += data[:left]
        if self.is_completed:
            self.on_completed()
