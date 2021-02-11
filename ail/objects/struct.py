from copy import deepcopy

from ..core import aobjects as obj

from ..core.aobjects import (
    AILObjectType,
    AILObject, convert_to_ail_object, 
    unpack_ailobj, call_object, create_object,
    compare_type
)

from . import null
from ..core.error import AILRuntimeError
from . import types
from . import function as afunc


_BIND_BOUND_FUNCTION = object()


def _is_reserved_name(name):
    return name[:2] == '__' and name[-2:] != '__'


def _copy_function(f: AILObject) -> AILObject:
    new_f = deepcopy(f)
    new_f.properties = f.properties.copy()

    return new_f


def _get_method_str_func(obj_name: str):
    def _method_str(m):
        return '<method %s of %s at %s>' % (
                m['__name__'], obj_name, hex(id(m)))
    return _method_str


def _check_bound(self, aobj: AILObject):
    if isinstance(aobj, AILObject) and \
            aobj['__class__'] in (afunc.FUNCTION_TYPE, afunc.PY_FUNCTION_TYPE):
        aobj = _copy_function(aobj)

        self.reference += 1
        if aobj['__this__'] is not None:
            return _BIND_BOUND_FUNCTION

        aobj['__repr__'] = _get_method_str_func(self['__name__'])
        aobj['__this__'] = self  # bound self to __this__
    return aobj


def struct_init(self, name: str, members: list,
                protected_members: list):
    self['__name__'] = name
    self['__bind_functions__'] = {}

    d = {n: null.null for n in members}  # init members
    self.protected = protected_members
    self.members = d


def structobj_init(self, name: str, members: dict, struct_type: AILObject,
                   protected_members: list, bind_funcs: dict = None):
    self['__type__'] = struct_type
    self['__name__'] = name

    if bind_funcs is None:
        bind_funcs = {}

    members.update(bind_funcs)

    self.members = {k: _check_bound(self, v)
                    for k, v in members.items()}
    self.protected = protected_members


def struct_getattr(self, name: str):
    pthis = hasattr(self, '_pthis_')

    if name in self.members and (
            pthis or not _is_reserved_name(name)):
        return self.members[name]

    return AILRuntimeError('struct \'%s\' has no attribute \'%s\'' %
                           (self['__name__'], name),
                           'AttributeError')


def structobj_setattr(self, name: str, value):
    pthis = hasattr(self, '_pthis_')  # check _pthis_ attr

    if name in self.protected and not pthis:
        return AILRuntimeError(
                'Cannot modify a protected attribute.', 'AttributeError')

    if name in self.members and (pthis or not _is_reserved_name(name)):
        val = _check_bound(self, value)
        if val is _BIND_BOUND_FUNCTION:
            return AILRuntimeError('bind a bound function', 'TypeError')
        self.members[name] = val
    else:
        return AILRuntimeError('struct \'%s\' object has no attribute \'%s\'' %
                               (self['__name__'], name),
                               'AttributeError')


def struct_setattr(self, name: str, value):
    return AILRuntimeError('struct type \'%s\' has no attribute \'%s\'' %
                           (self['__name__'], name),
                           'AttributeError')


def struct_str(self):
    return '<struct \'%s\' at %s>' % (self['__name__'], hex(id(self)))


def structobj_str_old(self):
    return '<struct \'%s\' object at %s> -> {\n%s\n}' % (
        self['__name__'], hex(id(self)),
        '\n'.join(['\t%s%s : %s' % (
            '' if k not in self.protected else '$P ', k, repr(v))
                   for k, v in self.members.items() if k[:2] != '__']))


def structobj_str(self):
    return '<\'%s\' object at %s>' % (self['__name__'], hex(id(self)))


STRUCT_OBJ_TYPE = AILObjectType('<struct object type>', 
                                    types.I_STRUCT_OBJ_TYPE,
                                    __init__=structobj_init,
                                    __setattr__=structobj_setattr,
                                    __getattr__=struct_getattr,
                                    __str__=structobj_str,
                                    __repr__=structobj_str)

STRUCT_TYPE = AILObjectType('<struct type>', types.I_STRUCT_TYPE,
                                __init__=struct_init,
                                __getattr__=struct_getattr,
                                __setattr__=struct_setattr,
                                __str__=struct_str,
                                __repr__=struct_str)


class _StructObjectWrapper:
    def __init__(self, struct_obj):
        self.__struct = struct_obj
        self.__members = struct_obj.members

    def __getattr__(self, item: str):
        if isinstance(item, str) and item.startswith('__this_'):
            item = item = item[7:]
            if item in self.__members:
                return self.__members[item]
        else:
            super().__getattribute__(item)

    def __setattr__(self, key, value):
        if isinstance(key, str) and key.startswith('__this_'):
            item = item = key[7:]
            if item in self.__members:
                self.__members[item] = value
            else:
                super().__setattr__(key, value)
        else:
            super().__setattr__(key, value)

    def to_struct(self):
        return self.__struct


def convert_to_pyobj(struct_obj) -> _StructObjectWrapper:
    if not compare_type(struct_obj, STRUCT_OBJ_TYPE):
        return None
    st = _StructObjectWrapper(struct_obj)

    return st


def new_struct_object(name: str, struct_type: AILObject,
                      members: dict, protected_members: list) -> AILObject:
    if struct_type is None:
        struct_type = null

    return create_object(
        STRUCT_OBJ_TYPE, name, members, struct_type, protected_members)


def struct_object_getattr(struct_obj: AILObject, name: str) -> AILObject:
    if not struct_compare_type(struct_obj, STRUCT_OBJ_TYPE):
        return None

    members = struct_obj.members

    return members.get(name, None)


def struct_object_setattr(struct_obj: AILObject,
                          name: str, value: AILObject) -> AILObject:
    if not compare_type(struct_obj, STRUCT_OBJ_TYPE):
        return None

    value = convert_to_ail_object(value)

    struct_obj.members[name] = value


def new_struct(
        name: str, members: list, protected_members: list, bind_functions: dict = None):
    s = create_object(
        STRUCT_TYPE, name, members, protected_members)
    s['__bind_functions__'] = bind_functions
    return s


def struct_obj_isinstance(struct_obj, struct_type) -> bool:
    if not compare_type(struct_obj, STRUCT_OBJ_TYPE) or \
            not compare_type(struct_type, STRUCT_TYPE):
        return False
    return struct_obj['__type__'] is struct_type
