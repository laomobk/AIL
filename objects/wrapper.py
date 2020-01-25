# Object wrapper

import aobjects as obj
from . import types


def wrapper_func_init(self, pyobj :object):
    self['__pyobject__'] = pyobj


WRAPPER_TYPE = obj.AILObjectType('<Python object wrapper>', types.I_WRAPPER_TYPE,
                                 __init__=wrapper_func_init)
