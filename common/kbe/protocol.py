class X:
    @classmethod
    def add_type(cls, c):
        for k, v in c.__dict__.items():
            if isinstance(v, cls):
                v.type = k
        return c

    def __init__(self, t=None):
        self.type = t
        self.origin = None
        self.client_flag = False

    def __call__(self, t):
        if self.origin is not None and self.origin is not t:
            assert False, "You can only give it a alias just once or same one! %s, %s" % (t, self.origin)
        self.origin = t
        return self

    def __str__(self):
        return self.str()

    @property
    def array(self):
        return self.__class__(self)

    @property
    def client(self):
        c = self.clone()
        c.client_flag = True
        return c

    def clone(self):
        c = self.__class__()
        c.type = self.type.clone() if self.is_array_type() else self.type
        c.origin = self.origin.clone() if isinstance(self.origin, self.__class__) else self.origin
        c.client_flag = self.client_flag
        return c

    def final_x(self):
        t = self
        while t.is_array_type():
            t = t.type
        return t

    def depth(self):
        depth = 0
        t = self
        while t.is_array_type():
            t = t.type
            depth += 1
        return depth

    def is_array_type(self):
        return isinstance(self.type, self.__class__)

    def is_client_type(self):
        return self.client_flag

    def has_alias(self):
        return isinstance(self.origin, self.__class__)

    def str(self):
        def travel(o):
            if o.is_array_type():
                return r'ARRAY<of>%s</of>' % travel(o.type)
            else:
                return str(o.type)

        return travel(self)

    def alias_str(self):
        assert self.has_alias(), "This one is not a alias! %s, %s" % (self, self.origin)
        return r"    <%(alias)s>%(origin)s</%(alias)s>" % dict(
            alias=self,
            origin=self.origin
        )


class MetaOfType(type):
    def __getattr__(cls, item):
        dict_type = cls.dicts.get(item)
        return dict_type or cls.alias.setdefault(item, X(item))

    def __getitem__(cls, item):
        item = item.protocol_name()
        return cls.dicts.setdefault(item, X(item))


@X.add_type
class Type(object, metaclass=MetaOfType):
    template_str = """<root>
    %(alias)s
    %(dict_types)s
</root>"""
    alias = dict()
    dicts = dict()
    dict_types = []

    UINT8 = X()
    UINT16 = X()
    UINT32 = X()
    UINT64 = X()
    INT8 = X()
    INT16 = X()
    INT32 = X()
    INT64 = X()
    FLOAT = X()
    DOUBLE = X()
    VECTOR2 = X()
    VECTOR3 = X()
    VECTOR4 = X()
    STRING = X()
    UNICODE = X()
    PYTHON = X()
    PY_DICT = X()
    PY_TUPLE = X()
    PY_LIST = X()
    MAILBOX = X()
    BLOB = X()

    @classmethod
    def add_dict_type(cls, dict_type):
        cls.dict_types.append(dict_type)

    @classmethod
    def finish_dict_type(cls):
        for dict_type_cls in cls.dict_types:
            dict_type_cls.apply_by_properties_type()

    @classmethod
    def init_dict_types(cls):
        for dict_type_cls in cls.dict_types:
            init = getattr(dict_type_cls, "init_type", None)
            if init:
                init()
        cls.finish_dict_type()

    @classmethod
    def alias_str(cls):
        s = ""
        for name in sorted(cls.alias):
            if cls.alias[name].has_alias():
                s += '\n' + cls.alias[name].alias_str()
        return s

    @classmethod
    def dict_types_str(cls):
        s = ""
        for dict_type in cls.dict_types:
            if dict_type.check_t_type(dict_type):
                s += '\n' + dict_type.protocol_str()
        return s

    @classmethod
    def str(cls):
        return cls.template_str % dict(
            alias=cls.alias_str(),
            dict_types=cls.dict_types_str()
        )


class AnyProperty(dict):
    pass


class Property(dict):
    @X.add_type
    class Flags:
        BASE = X()
        BASE_AND_CLIENT = X()
        CELL_PRIVATE = X()
        CELL_PUBLIC = X()
        CELL_PUBLIC_AND_OWN = X()
        ALL_CLIENTS = X()
        OWN_CLIENT = X()
        OTHER_CLIENTS = X()

    @X.add_type
    class Index:
        DEFAULT = X()
        INDEX = X()
        UNIQUE = X()

    @X.add_type
    class Persistent:
        true = X()
        false = X()

    empty = object()
    standard_list = ("Utype", "Type", "Flags", "Default", "Index", "DatabaseLength", "Persistent")
    template_kv_str = """            <%(key)s>%(value)s</%(key)s>"""

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls, *args, **kwargs)
        if set(kwargs) & set(cls.standard_list):
            return obj
        return AnyProperty(**kwargs)

    def is_client(self):
        return self["Flags"] in (
            self.Flags.BASE_AND_CLIENT,
            self.Flags.CELL_PUBLIC_AND_OWN,
            self.Flags.ALL_CLIENTS,
            self.Flags.OWN_CLIENT,
            self.Flags.OTHER_CLIENTS)

    def check_k_v(self, k, v):
        if k == "Index" and v == self.Index.DEFAULT:
            return False
        return True

    def str(self):
        s = ""
        for key in self.standard_list:
            value = self.get(key, self.empty)
            if value is not self.empty and self.check_k_v(key, value):
                s += '\n' + self.template_kv_str % dict(
                    key=key,
                    value=value
                )
        return s


class Union(dict):
    def __add__(self, other):
        result = dict()
        result.update(other)
        result.update(self)
        return self.__class__(**result)


class Properties(Union):
    template_detail_str = """        <%(name)s>%(detail)s
        </%(name)s>"""
    template_whole_str = """    <Properties>%s
    </Properties>\n\n"""

    def str(self):
        s = ""
        for k in sorted(self):
            detail = self[k].str()
            if detail:
                s += '\n' + self.template_detail_str % dict(
                    name=k,
                    detail=detail
                )
        return self.template_whole_str % s if self else ""


class MailBox(Union):
    template_method_str = """        <%(name)s>%(args)s
        </%(name)s>"""
    template_whole_str = ""

    def str(self):
        s = ""
        for k in sorted(self):
            if not isinstance(self[k], Method):
                continue
            s += '\n' + self.template_method_str % dict(
                name=k,
                args=self[k].str()
            )
        return self.template_whole_str % s if self else ""


class Parent(str):
    template_whole_str = """    <Parent>%s</Parent>\n\n"""

    def str(self):
        return self.template_whole_str % self if self else self


class Interfaces(list):
    template_detail_str = """        <Interface>%(detail)s</Interface>"""
    template_whole_str = """    <Interfaces>%s
    </Interfaces>\n\n"""

    def str(self):
        s = ""
        for x in self:
            s += '\n' + self.template_detail_str % dict(detail=x)
        return self.template_whole_str % s if self else ""


class Volatile(dict):
    always = None
    never = 0

    template_kv_str = """        <%(key)s>%(value)s
        </%(key)s>"""
    template_whole_str = """    <Volatile>%s
    </Volatile>"""

    @classmethod
    def never_sync(cls):
        return cls(
            position=cls.never,
            yaw=cls.never,
            pitch=cls.never,
            roll=cls.never
        )

    @classmethod
    def always_sync(cls):
        return cls(
            position=cls.always,
            yaw=cls.always,
            pitch=cls.always,
            roll=cls.always
        )

    def str(self):
        s = ""
        for k in ("position", "yaw", "pitch", "roll"):
            v = self.get(k)
            if v is not None:
                s += '\n' + self.template_kv_str % dict(
                    key=k,
                    value=v
                )
        return self.template_whole_str % s if self else ""


class Base(MailBox):
    template_whole_str = """    <BaseMethods>%s
    </BaseMethods>\n\n"""


class Cell(MailBox):
    template_whole_str = """    <CellMethods>%s
    </CellMethods>\n\n"""


class Client(MailBox):
    UNKNOWN_CLIENT_COMPONENT_TYPE = 0
    CLIENT_TYPE_MOBILE = 1  # 手机类
    CLIENT_TYPE_WIN = 2  # pc， 一般都是exe客户端
    CLIENT_TYPE_LINUX = 3  # Linux Application program
    CLIENT_TYPE_MAC = 4  # Mac Application program
    CLIENT_TYPE_BROWSER = 5  # web应用， html5，flash
    CLIENT_TYPE_BOTS = 6  # bots
    CLIENT_TYPE_MINI = 7  # 微型客户端

    template_whole_str = """    <ClientMethods>%s
    </ClientMethods>"""

    @staticmethod
    def proxy(*args, **kwargs):
        pass

    def __getattr__(self, item):
        return self.proxy


class Entity(dict):
    template_whole_str = """<root>
%s
</root>"""
    template_detail_str = """%(parent)s%(volatile)s%(implements)s%(properties)s%(base)s%(cell)s%(client)s"""

    def str(self):
        return self.template_whole_str % ((self.template_detail_str % self).rstrip())


class Entities(list):
    template_whole_str = """<root>
%s
</root>"""
    template_detail_str = """    <%(name)s%(detail)s></%(name)s>\n"""

    def _sort(self):
        self.sort(key=lambda x: x["key"])

    def append(self, p_object):
        if p_object["name"] not in [info["name"] for info in self]:
            super().append(p_object)

    def str(self):
        self._sort()
        s = ""
        for info in self:
            detail = ""
            if info["hasCell"]:
                detail += ' hasCell = "true"'
            # if info["hasBase"]:
            #     detail += ' hasBase = "true"'
            if info["hasClient"]:
                detail += ' hasClient = "true"'
            s += self.template_detail_str % dict(
                name=info["name"],
                detail=detail
            )
        return self.template_whole_str % s.rstrip()


class Method(list):
    prefix_str = ""
    template_str = """            <Arg>%s</Arg>"""

    def __init__(self, *args):
        super().__init__(args)

    def __call__(self, *args, **kwargs):
        pass

    def str(self):
        s = self.prefix_str
        for x in self:
            s += '\n' + self.template_str % x.str()
        return s


class BaseMethod(Method):
    pass


class BaseMethodExposed(BaseMethod):
    prefix_str = """\n            <Exposed/>"""


class CellMethod(Method):
    pass


class CellMethodExposed(CellMethod):
    prefix_str = """\n            <Exposed/>"""


class ClientMethod(Method):
    pass
