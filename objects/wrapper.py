# Object wrapper

import aobjects as obj
from . import types


def wrapper_func_init(self, pyobj :object):
    self['__pyobject__'] = pyobj


def wrapper_func_str(self):
    return str(self['__pyobject__'])


def wrapper_func_repr(self):
    return repr(self['__pyobject__'])


WRAPPER_TYPE = obj.AILObjectType('<Python object wrapper>', types.I_WRAPPER_TYPE,
                                 __init__=wrapper_func_init,
                                 __str__=wrapper_func_str,
                                 __repr__=wrapper_func_repr)
