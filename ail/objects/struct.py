from copy import deepcopy

from ..core import aobjects as obj
from . import null
from ..core.error import AILRuntimeError
from . import types
from . import function as afunc


def _is_reserved_name(name):
    return name[:2] == '__'


def _copy_function(f: obj.AILObject) -> obj.AILObject:
    new_f = deepcopy(f)
    new_f.properties = f.properties.copy()

    return new_f


def _check_bound(self, aobj :obj.AILObject):
    if isinstance(aobj, obj.AILObject) and \
            aobj['__class__'] in (afunc.FUNCTION_TYPE, afunc.PY_FUNCTION_TYPE):

        aobj = _copy_function(aobj)

        self.reference += 1
        aobj['__this__'] = self  # bound self to __this__
    return aobj


def struct_init(self, name :str, name_list :list,
                protected_members :list):
    d = {n : null.null for n in name_list}  # init members
    
    self.protected = protected_members
    self.members = d

    self['__name__'] = name
    self['__bind_functions__'] = {}


def structobj_init(self, name :str, members :dict, type :obj.AILObject,
                   protected_members :list, bind_funcs: dict=None):
    if bind_funcs is None:
        bind_funcs = {}

    members.update(bind_funcs)

    self.members = {k : _check_bound(self, v)
                        for k, v in members.items()}
    self.protected = protected_members

    self['__type__'] = type
    self['__name__'] = name


def struct_getattr(self, name :str):
    pthis = hasattr(self, '_pthis_')
    
    if name in self.members and (
            pthis or not _is_reserved_name(name)):
        return self.members[name]

    return AILRuntimeError('struct \'%s\' has no attribute \'%s\'' % 
                           (self['__name__'], name),
                           'AttributeError')


def structobj_setattr(self, name :str, value):
    pthis = hasattr(self, '_pthis_')   # check _pthis_ attr

    if name in self.protected and not pthis:
        return AILRuntimeError('Cannot modify a protected attribute.', 'AttributeError')

    if name in self.members and (pthis or not _is_reserved_name(name)):
        self.members[name] = _check_bound(self, value)
    else:
        return AILRuntimeError('struct \'%s\' object has no attribute \'%s\'' %
                               (self['__name__'], name),
                               'AttributeError')


def struct_setattr(self, name :str, value):
    return AILRuntimeError('struct type \'%s\' has no attribute \'%s\'' %
                           (self['__name__'], name),
                           'AttributeError')


def struct_str(self):
    return '<struct \'%s\' at %s>' % (self['__name__'], hex(id(self)))


def structobj_str(self):
    return '<struct \'%s\' object at %s> -> {\n%s\n}' % (
            self['__name__'], hex(id(self)),
            '\n'.join(['\t%s%s : %s' % (
                            '' if k not in self.protected else '$P ', k, repr(v)) 
                        for k, v in self.members.items() if k[:2] != '__']))


STRUCT_OBJ_TYPE = obj.AILObjectType('<AIL struct object type>', types.I_STRUCT_OBJ_TYPE,
                                __init__=structobj_init,
                                __setattr__=structobj_setattr,
                                __getattr__=struct_getattr,
                                __str__=structobj_str,
                                __repr__=structobj_str)

STRUCT_TYPE = obj.AILObjectType('<AIL struct type>', types.I_STRUCT_TYPE,
                                __init__=struct_init,
                                __getattr__=struct_getattr,
                                __setattr__=struct_setattr,
                                __str__=struct_str,
                                __repr__=struct_str)


class _StructObjectWrapper:
    def __init__(self, struct_obj):
        self.__struct = struct_obj
        self.__members = struct_obj.members

    def __getattr__(self, item :str):
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
    if not obj.compare_type(struct_obj, STRUCT_OBJ_TYPE):
        return None
    st = _StructObjectWrapper(struct_obj)

    return st


def new_struct_object(name :str, type :obj.AILObject,
                      members :dict, protected_members :list):
    return obj.ObjectCreater.new_object(
        STRUCT_OBJ_TYPE, name, members, type, protected_members)
