import aobjects as obj
from objects import null
from error import AILRuntimeError
from objects import types
from objects import function as afunc


def _is_reserved_name(name):
    return name[:2] == '__'


def _check_bound(self, aobj :obj.AILObject):
    if isinstance(aobj, obj.AILObject) and \
            aobj['__class__'] == afunc.FUNCTION_TYPE:
        self.reference += 1
        aobj['__this__'] = self  # bound self to __this__
    return aobj


def struct_init(self, name :str, name_list :list):
    d = {n : null.null for n in name_list}  # init members

    self.members = d
    self['__name__'] = name


def structobj_init(self, name :str, members :dict, type :obj.AILObject):
    self.members = {k : _check_bound(self, v)
                        for k, v in members.items() }

    self['__type__'] = type
    self['__name__'] = name


def struct_getattr(self, name :str):
    pthis = hasattr(self, '_pthis_')
    
    if name in self.members and (pthis or not _is_reserved_name(name)):
        return self.members[name]

    return AILRuntimeError('struct \'%s\' has no attribute \'%s\'' % 
                           (self['__name__'], name),
                           'AttributeError')


def structobj_setattr(self, name :str, value):
    pthis = hasattr(self, '_pthis_')   # check _pthis_ attr

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
    return '<struct \'%s\' at %d>' % (self['__name__'], hex(id(self)))


def structobj_str(self):
    return '<struct \'%s\' object at %s>' % (self['__name__'], hex(id(self)))


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
