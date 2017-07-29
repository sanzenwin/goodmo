import json
import importlib
import Math
from kbe.protocol import Type


class PythonType:
    @classmethod
    def dump(cls, v, client_flag):
        return json.dumps(v) if client_flag else v

    @classmethod
    def load(cls, v, client_flag):
        return json.loads(v) if client_flag else v


class ArrayType:
    def __init__(self, element_type):
        self.element_type = element_type

    def __str__(self):
        result = []
        element_type = self.element_type
        while isinstance(element_type, self.__class__):
            result.append(element_type)
            element_type = element_type.element_type
        result.append(element_type)
        return str(result)

    def dump(self, v, client_flag):
        return [self.element_type.dump(d, client_flag) for d in v]

    def load(self, v, client_flag):
        return [self.element_type.load(d, client_flag) for d in v]


def python_client(obj):
    return PythonType.dump(obj, True)


def python_client_list(lst):
    return ArrayType(PythonType).dump(lst, True)


def python_server(obj, real_type=None):
    if not isinstance(obj, str):
        return obj
    v = PythonType.load(obj, True)
    if real_type is not None and not isinstance(v, real_type):
        return real_type()
    return v


class MetaOfDictType(type):
    protocol_template_str = """
    <%(protocol_name)s>FIXED_DICT
        <implementedBy>%(module_name)s.%(pickler_name)s</implementedBy>
        <Properties>%(properties_str)s
        </Properties>
    </%(protocol_name)s>"""

    properties_template_str = """
            <%(name)s>
                <Type>%(type)s</Type>
            </%(name)s>"""

    default_value_empty = object()
    default_value_map = dict(
        UINT8=0,
        UINT16=0,
        UINT32=0,
        UINT64=0,
        INT8=0,
        INT16=0,
        INT32=0,
        INT64=0,
        FLOAT=0.0,
        DOUBLE=0.0,
        VECTOR2=Math.Vector2(),
        VECTOR3=Math.Vector3(),
        VECTOR4=Math.Vector4(),
        STRING="",
        UNICODE="",
        PYTHON=dict(),
        PY_DICT=dict(),
        PY_TUPLE=tuple(),
        PY_LIST=list(),
        MAILBOX=None,
        BLOB=""
    )

    client_map = dict(
        PYTHON=PythonType
    )

    base_list = []

    class DictTypePickler:
        user_type_class = None

        def createObjFromDict(self, dct):
            cls = self.user_type_class.real_type(dct)
            return cls().createFromDict(dct)

        def getDictFromObj(self, obj):
            return obj.asDict()

        def isSameType(self, obj):
            return isinstance(obj, self.user_type_class)

    @classmethod
    def is_base(mcs, cls):
        for base in mcs.base_list:
            if issubclass(cls, base):
                return False
        return True

    @classmethod
    def get_t_value(mcs, t):
        if t.is_array_type():
            return list()
        type_name = t.str()
        v = mcs.default_value_map.get(type_name, mcs.default_value_empty)
        if v is not mcs.default_value_empty:
            return v
        x = Type.alias.get(type_name, mcs.default_value_empty)
        if x is not mcs.default_value_empty:
            assert x.origin, "%s should have alias!" % x
            return mcs.default_value_map[x.origin.str()]
        for cls in Type.dict_types:
            if cls.check_t_type(cls) and type_name == cls.protocol_name():
                return cls().client if t.is_client_type() else cls()
        assert False, "MetaOfDictType::get_t_value: type error %s" % type_name

    @classmethod
    def get_r_value(mcs, t):
        type_name = t.final_x().str()
        c = None
        for cls in Type.dict_types:
            if cls.check_t_type(cls) and type_name == cls.protocol_name():
                c = cls
                break
        assert c, "MetaOfDictType::get_r_value: type error %s" % type_name
        depth = t.depth()
        while depth > 0:
            c = ArrayType(c)
            depth -= 1
        return c

    @classmethod
    def check_t_type(mcs, cls):
        return cls.__name__[0] == 'T' and "A" <= cls.__name__[1] <= "Z"

    def __new__(mcs, name, bases, kwargs):
        dict_type_cls = super().__new__(mcs, name, bases, kwargs)
        if mcs.is_base(dict_type_cls):
            mcs.base_list.append(dict_type_cls)
        elif "generic_key" not in dict_type_cls.__dict__ and hasattr(dict_type_cls, "generic_key"):
            dict_type_cls.generic_init()
        elif mcs.check_t_type(dict_type_cls):
            pickler_cls = type(name[1:] + 'Pickler', (mcs.DictTypePickler,), dict(user_type_class=dict_type_cls))
            module = importlib.import_module(dict_type_cls.__module__)
            setattr(module, dict_type_cls.pickler_name(), pickler_cls())
        Type.add_dict_type(dict_type_cls)
        return dict_type_cls

    def apply_by_properties_type(cls):
        cls.properties = {k: (getattr(cls, k, None) or cls.get_t_value(v)) for k, v in cls.properties_type.items()}
        cls.client_fields = {k: cls.client_map[v.str()] for k, v in cls.properties_type.items() if
                             v.client_flag and v.str() not in Type.dicts}
        cls.recursion_fields = {k: cls.get_r_value(v) for k, v in cls.properties_type.items() if
                                v.final_x().str() in Type.dicts}
        # cls.recursion_fields.update(cls.client_fields)

        cls.dict_properties = dict()
        for c in reversed(cls.mro()):
            properties = getattr(c, 'properties', dict())
            cls.dict_properties.update(properties)

    def pickler_name(cls):
        return "instance_%s" % cls.protocol_name().lower()

    def protocol_name(cls):
        assert cls.check_t_type(cls) or cls.is_base(cls), \
            "(%s)DictType's subclass name should started by 'T'!" % cls.__name__
        s = ""
        for c in cls.__name__[1:]:
            if 'A' <= c <= 'Z' and s:
                s += '_'
            s += c
        return s.upper()

    def properties_str(cls):
        s = ""
        for name in sorted(cls.properties_type):
            s += cls.properties_template_str % dict(
                name=name,
                type=cls.properties_type[name].str()
            )
        return s

    def protocol_str(cls):
        return cls.protocol_template_str % dict(
            protocol_name=cls.protocol_name(),
            module_name=cls.__module__,
            pickler_name=cls.pickler_name(),
            properties_str=cls.properties_str()
        )


class DictType(object, metaclass=MetaOfDictType):
    client_flag = True
    properties = dict()
    properties_type = dict()
    client_fields = dict()
    recursion_fields = dict()
    dict_properties = dict()

    def __init__(self, **kwargs):
        for k, v in self.dict_properties.items():
            setattr(self, k, kwargs.get(k, v))

    def __str__(self):
        return json.dumps(self.asRecursionDict(), indent=1)

    def __deepcopy__(self, memo):
        return self.clone()

    def __eq__(self, other):
        for k, v in self.dict_properties.items():
            if getattr(self, k) != getattr(other, k):
                return False
        return True

    def clone(self):
        obj = self.__class__()
        obj.createFromRecursionDict(self.asRecursionDict())
        return obj

    @staticmethod
    def _setClient(obj, isClient):
        obj.client_flag = isClient
        for k, tv in obj.recursion_fields.items():
            v = getattr(obj, k)
            if isinstance(v, DictType):
                DictType._setClient(v, isClient)
            elif isinstance(tv, ArrayType):
                for v2 in v:
                    DictType._setClient(v2, isClient)

    @property
    def client(self):
        if not self.client_flag:
            DictType._setClient(self, True)
        return self

    @property
    def server(self):
        if self.client_flag:
            DictType._setClient(self, False)
        return self

    @classmethod
    def real_type(cls, dct):
        return cls

    def asDict(self):
        ret = dict()
        for k in self.dict_properties.keys():
            v = getattr(self, k)
            if self.client_flag:
                client_handle = self.client_fields.get(k, None)
                if client_handle:
                    v = client_handle.dump(v, self.client_flag)
            ret[k] = v
        return ret

    def createFromDict(self, dictData):
        for k, v in dictData.items():
            client_handle = self.client_fields.get(k, None)
            if client_handle:
                v = client_handle.load(v, self.client_flag)
            setter = getattr(self, "set__%s" % k, None)
            if setter is not None:
                v = setter(v)
            setattr(self, k, v)
        return self

    def asRecursionDict(self):
        ret = dict()
        for k in self.dict_properties.keys():
            v = getattr(self, k)
            if self.client_flag:
                client_handle = self.client_fields.get(k, None)
                if client_handle:
                    v = client_handle.dump(v, self.client_flag)
            else:
                recursion_handle = self.recursion_fields.get(k, None)
                if recursion_handle:
                    v = recursion_handle.dump(v, self.client_flag)
            ret[k] = v
        return ret

    def createFromRecursionDict(self, dictData):
        for k, v in dictData.items():
            client_handle = self.client_fields.get(k, None)
            if client_handle:
                v = client_handle.load(v, self.client_flag)
            recursion_handle = self.recursion_fields.get(k, None)
            if recursion_handle:
                v = recursion_handle.load(v, self.client_flag)
            setter = getattr(self, "set__%s" % k, None)
            if setter is not None:
                v = setter(v)
            setattr(self, k, v)
        return self

    @classmethod
    def dump(cls, v, client_flag):
        v = v.client if client_flag else v.server
        return v.asRecursionDict()

    @classmethod
    def load(cls, v, client_flag):
        o = cls().client if client_flag else cls().server
        return o.createFromRecursionDict(v)


class GenericDictType(DictType):
    generic_key = None
    generic_map = None

    @classmethod
    def generic_init(cls):
        cls.generic_map[getattr(cls, cls.generic_key)] = cls

    @classmethod
    def real_type(cls, dct):
        return cls.generic_map[dct[cls.generic_key]]

    def __init__(self, **kwargs):
        kwargs[self.generic_key] = getattr(self, self.generic_key)
        super().__init__(**kwargs)
