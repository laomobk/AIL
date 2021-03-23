import inspect

from types import FunctionType
from typing import Union

from . import error
from ..objects import types

from .avmsig import VMInterrupt, MII_ERR_POP_TO_TRY, sig_check_continue

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
                 'argcount', 'name', 'lnotab', 'closure', 'is_main', 'filename',
                 '_closure_outer', 'global_names', 'nonlocal_names', 'var_arg',
                 'doc_string', '_function_signature')

    def __init__(self, consts: list, varnames: list,
                 bytecodes: list, firstlineno: int, filename: str,
                 argcount: int, name: str, lnotab: list, lineno_list: tuple,
                 closure: bool = False, is_main: bool = False,
                 global_names: list=None, nonlocal_names: list=None,):
        self.consts = consts
        self.varnames = varnames
        self.bytecodes = tuple(bytecodes)
        self.firstlineno = firstlineno
        self.argcount = argcount  # if function or -1
        self.name = name
        self.filename = filename
        self.lnotab = lnotab
        self.closure = closure
        self.is_main = is_main
        self.lineno_list = lineno_list
        self.global_names = global_names
        self.nonlocal_names = nonlocal_names

        self.var_arg: str = None
        self.doc_string: str = ''

        self._closure_outer: list = list()  # empty if not closure

        self._function_signature = ''

    def __str__(self):
        return '<AIL CodeObject \'%s\'>' % self.name

    __repr__ = __str__


class AILObject:
    """Base object, do noting..."""

    def __init__(self, **ps):
        self.__hash_target = object()  # hash

        self.hash_handler = None
        self.properties = ps
        self.reference = 0

    def __getitem__(self, key: str):
        return self.properties.get(key)

    def __setitem__(self, key: str, value):
        self.properties[key] = value

    def __str__(self):
        s = self['__str__'](self)
        if isinstance(s, str):
            return s

        s = get_state().global_interpreter.check_object(s, not_convert=True)

        if not isinstance(s, str):
            return '<(NON-STRING STR) AIL Object at %s>' % hex(id(self))

        return s

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
        repr_func = self['__repr__']
        
        if repr_func is None:
            return self.__str__()

        r = repr_func(self)
        if isinstance(r, str):
            return r
        r = get_state().global_interpreter.check_object(r, not_convert=True)
        if not isinstance(r, str):
            return '<(NON-STRING REPR) AIL Object at %s>' % hex(id(self))
        return r

    def __hash__(self) -> int:
        if self.hash_handler is None:
            return hash(self.__hash_target)
        hash_val = check_object(self.hash_handler(self), not_convert=True)

        return hash_val
    
    def set_hash_target(self, hash_target: object):
        self.__hash_target = hash_target


class AILObjectType:
    """Object Type"""

    def __init__(self, 
            tname: str, otype=None, methods: dict = None, **required):
        super().__init__()
        self.name = tname
        self.required = required
        self.otype = types.I_TYPE_TYPE if otype is None else otype
        self.methods = methods if methods is not None else dict()

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
                if not isinstance(mo, AILObject):
                    f = ObjectCreater.__to_wrapper(mo)

                    f.properties['__this__'] = obj  # bound self to __this__
                    obj.properties[mn] = f

        # check normal required
        t_req_keys = set(obj_type.required.keys())

        for name, default in ObjectCreater.__required_normal.items():
            if name in t_req_keys:
                continue
            obj.properties[name] = default

        # call init method
        init_mthd = obj.properties['__init__']
        r = init_mthd(obj, *args)

        if isinstance(r, error.AILRuntimeError):
            return r

        return obj


create_object = ObjectCreater.new_object


# cache
_STRING_TYPE = None
_INTEGER_TYPE = None
_FLOAT_TYPE = None
_COMPLEX_TYPE = None
_ARRAY_TYPE = None
_MAP_TYPE = None
_WRAPPER_TYPE = None
_PY_FUNCTION_TYPE = None
_BYTES_TYPE = None
_null = None
_not_loaded = True


def convert_to_ail_object(pyobj: object) -> AILObject:
    global _not_loaded
    global _STRING_TYPE
    global _INTEGER_TYPE
    global _FLOAT_TYPE
    global _COMPLEX_TYPE
    global _ARRAY_TYPE
    global _MAP_TYPE
    global _WRAPPER_TYPE
    global _PY_FUNCTION_TYPE
    global _BYTES_TYPE
    global _null

    if isinstance(pyobj, AILObject):
        return pyobj
    
    if _not_loaded:
        from ..objects.string import STRING_TYPE as _STRING_TYPE
        from ..objects.integer import INTEGER_TYPE as _INTEGER_TYPE
        from ..objects.float import FLOAT_TYPE as _FLOAT_TYPE
        from ..objects.complex import COMPLEX_TYPE as _COMPLEX_TYPE
        from ..objects.array import ARRAY_TYPE as _ARRAY_TYPE
        from ..objects.map import MAP_TYPE as _MAP_TYPE
        from ..objects.wrapper import WRAPPER_TYPE as _WRAPPER_TYPE
        from ..objects.function import PY_FUNCTION_TYPE as _PY_FUNCTION_TYPE
        from ..objects.bytes import BYTES_TYPE as _BYTES_TYPE
        from ..objects.null import null as _null
        _not_loaded = False

    if pyobj is None:
        return _null

    py_t = type(pyobj)
    ail_t = _WRAPPER_TYPE

    if py_t is int:
        ail_t = _INTEGER_TYPE
    elif py_t is float:
        ail_t  = _FLOAT_TYPE
    elif py_t is complex:
        ail_t = _COMPLEX_TYPE
    elif py_t is str:
        ail_t = _STRING_TYPE
    elif py_t is bytes:
        ail_t = _BYTES_TYPE
    elif py_t is bool:
        from .abuiltins import true, false
        return true if pyobj else false
    elif py_t is list:
        ail_t = _ARRAY_TYPE
    elif py_t is dict:
        ail_t = _MAP_TYPE
    elif py_t is FunctionType:
        ail_t = _PY_FUNCTION_TYPE

    return ObjectCreater.new_object(ail_t, pyobj)


def convert_to_ail_number(pynum: Union[int, float]) -> AILObject:
    from ..objects import integer
    from ..objects import float as afloat
    from ..objects import complex as acomplex

    if isinstance(pynum, int):
        return integer.get_integer(pynum)
    elif isinstance(pynum, float):
        return afloat._new_object(afloat.FLOAT_TYPE, pynum)
    elif isinstance(pynum, complex):
        return acomplex.to_complex(pynum)
    else:
        return pynum


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


def get_state():
    global _MAIN_INTERPRETER_STATE
    if _MAIN_INTERPRETER_STATE is None:
        from .astate import MAIN_INTERPRETER_STATE as _MAIN_INTERPRETER_STATE
    return _MAIN_INTERPRETER_STATE


_MAIN_INTERPRETER_STATE = None


def call_object(obj, *args,
                type_check: bool = False, 
                frame=None, handle_error=True,
                throw_top=False) -> bool:
    """
    :return: an AIL runtime error has occurred or not.
    """
    global _MAIN_INTERPRETER_STATE

    if isinstance(obj, FunctionType):
        return obj(*args)

    if _MAIN_INTERPRETER_STATE is None:
        from .astate import MAIN_INTERPRETER_STATE as _MAIN_INTERPRETER_STATE

    args = list(args)

    if type_check:
        for i, ele in enumerate(args):
            if not isinstance(ele, AILObject):
                args[i] = convert_to_ail_object(ele)

    interpreter = _MAIN_INTERPRETER_STATE.global_interpreter
    ok = interpreter.call_function(
        obj, len(args), args, frame=frame)
    if not ok:
        raise VMInterrupt(MII_ERR_POP_TO_TRY)
    if throw_top:
        interpreter.pop_top()
    return True


def check_object(obj, not_convert=False):
    return get_state().global_interpreter.check_object(obj, not_convert)
