from ..core import aobjects as obj
from . import types


def null_init(self):
    self['__value__'] = None

    self.set_hash_target(None)


def null_str(self):
    return 'null'


_NULL_TYPE = obj.AILObjectType('<null type>', types.I_NULL_TYPE,
                               __str__=null_str,
                               __init__=null_init)

null = obj.ObjectCreater.new_object(_NULL_TYPE)

