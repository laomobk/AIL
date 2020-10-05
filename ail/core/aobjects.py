from . import error
from ..objects import types

import inspect

INVISIBLE_ATTRS = (
    '__value__',
    '__class__',
    '__init__',
    '__add__',
    '__div__',
    '__muit__',
    '__sub__',
    '__div__',
    '__getattr__',
    '__setattr__',
    '__getitem__',
    '__setitem__',
    '__name__'
)


class AILConstant:
    __slots__ = ['const', 'type_']

    def __init__(self, const, type_: int):
        self.const = const
        self.type_ = type_


class NullType:
    def __str__(self):
        return 'null'

    __repr__ = __str__


# null = NullType()

class AILCodeObject:
    __slots__ = ('consts', 'varnames', 'bytecodes', 'firstlineno', 'lineno_list',
                 'argcount', 'name', 'lnotab', 'closure', 'is_main',
                 '_closure_outer')

    def __init__(self, consts: list, varnames: list,
                 bytecodes: list, firstlineno: int,
                 argcount: int, name: str, lnotab: list, lineno_list: tuple,
                 closure: bool = False, is_main: bool = False):
        self.consts = consts
        self.varnames = varnames
        self.bytecodes = bytecodes
        self.firstlineno = firstlineno
        self.argcount = argcount  # if function or -1
        self.name = name
        self.lnotab = lnotab
        self.closure = closure
        self.is_main = is_main
        self.lineno_list = lineno_list

        self._closure_outer: list = list()  # empty if not closure

    def __str__(self):
        return '<AIL CodeObject \'%s\'>' % self.name

    __repr__ = __str__


class AILObject:
    """Base object, do noting..."""

    def __init__(self, **ps):
        self.properties = ps
        self.reference = 0

    def __getitem__(self, key: str):
        if key in self.properties:
            k = self.properties[key]
            if isinstance(k, AILObject):
                k.reference += 1
            return k
        return None

    def __setitem__(self, key: str, value):
        if isinstance(value, AILObject):
            value.reference += 1
        self.properties[key] = value

    def __getattr__(self, item: str):
        if item[:5] == 'aprop':
            return self.__getitem__(item[6:])
        return super().__getattribute__(item)

    def __setattr__(self, key: str, value):
        if key[:5] == 'aprop':
            self.__setitem__(key[6:])
        super().__setattr__(key, value)

    def __str__(self):
        try:
            return self['__str__'](self)
        except TypeError:
            return '<AIL %s object at %s>' % (self['__class__'].name, hex(id(self)))

    def __eq__(self, o):
        try:
            b = self['__eq__'](self, o)
            if isinstance(b, error.AILRuntimeError):
                return False
            if isinstance(b, AILObject):
                v = b['__value__']
                if v is None:
                    return True  # 若无value， 默认返回 True
                return v
            return bool(b)

        except TypeError:
            return super().__eq__(o)

    def __repr__(self):
        try:
            return self['__repr__'](self)
        except TypeError:
            return self.__str__()


class AILObjectType:
    """Object Type"""

    def __init__(self, tname: str, otype=None, methods: dict = None, **required):
        self.name = tname
        self.required = required
        self.otype = types.I_TYPE_TYPE if otype is None else otype
        self.methods = methods

    def __str__(self):
        return '<AIL Type \'%s\'>' % self.name

    __repr__ = __str__


class ObjectCreater:
    from ..objects import ailobject as __aobj
    from ..objects.function import \
        convert_to_func_wrapper as __to_wrapper

    __required_normal = {
        '__str__': __aobj.obj_func_str,
        '__init__': __aobj.obj_func_init,
        '__eq__': __aobj.obj_func_eq,
        '__getattr__': __aobj.obj_getattr,
        '__setattr__': __aobj.obj_setattr,
        '__equals__': __aobj.obj_equals
    }

    @staticmethod
    def new_object(obj_type: AILObjectType, *args) -> AILObject:
        """
        ATTENTION : 返回的对象的引用为0
        :return : obj_type 创建的对象，并将 *args 作为初始化参数
        """

        obj = AILObject()  # create an object
        obj.properties['__class__'] = obj_type

        for k, v in obj_type.required.items():
            obj.properties[k] = v

        if obj_type.methods is not None:
            for mn, mo in obj_type.methods.items():
                if inspect.isfunction(mo):
                    f = ObjectCreater.__to_wrapper(mo)

                    f.reference += 1
                    obj.reference += 1

                    f['__this__'] = obj  # bound self to __this__
                    obj.properties[mn] = f

        # check normal required

        missing_req = [x for x in ObjectCreater.__required_normal.keys() if x not in obj_type.required.keys()]

        for mis in missing_req:
            obj.properties[mis] = ObjectCreater.__required_normal[mis]

        # call init method
        init_mthd = obj['__init__']
        r = init_mthd(obj, *args)

        if isinstance(r, error.AILRuntimeError):
            return r

        return obj


def check_object(obj):
    if isinstance(obj, error.AILRuntimeError):
        error.print_global_error(obj)


def convert_to_ail_object(pyobj: object) -> AILObject:
    if isinstance(pyobj, AILObject):
        return pyobj

    from ..objects import string
    from ..objects import integer
    from ..objects import float
    from ..objects import bool
    from ..objects import array
    from ..objects import wrapper
    from ..objects import function

    from types import FunctionType

    target_t = {
        str: string.STRING_TYPE,
        int: integer.INTEGER_TYPE,
        float: float.FLOAT_TYPE,
        bool: bool.BOOL_TYPE,
        list: array.ARRAY_TYPE,
        FunctionType: function.PY_FUNCTION_TYPE,
    }.get(type(pyobj), wrapper.WRAPPER_TYPE)

    return ObjectCreater.new_object(target_t, pyobj)


def compare_type(o, *t):
    if isinstance(o, AILObject):
        if o['__class__'] in t:
            return True
    return False


def has_attr(aobj: AILObject, name: str):
    if isinstance(aobj, AILObject):
        return name in aobj.properties
    return False


def unpack_ailobj(ailobj: AILObject):
    if has_attr(ailobj, '__value__'):
        return ailobj['__value__']
    return ailobj
