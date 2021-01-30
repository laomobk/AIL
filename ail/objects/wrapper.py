# Object wrapper

from ..core import aobjects as obj
from . import types
from ..core.error import AILRuntimeError


def wrapper_func_init(self, pyobj: object):
    self['__pyobject__'] = pyobj
    self['__value__'] = pyobj


def wrapper_func_str(self):
    return str(self['__pyobject__'])


def wrapper_func_repr(self):
    return repr(self['__pyobject__'])


def wrapper_func_getattr(self, name):
    if not hasattr(self['__pyobject__'], name):
        return AILRuntimeError('python object \'%s\' has no attribute \'%s\'' %
                               (type(self['__pyobject__']), name),
                               'AttributeError')
    return getattr(self['__pyobject__'], name)


def wrapper_func_setattr(self, name, value):
    return AILRuntimeError('Wrapper object\'s attribute is read-only',
                           'AttributeError')


WRAPPER_TYPE = obj.AILObjectType('<python object wrapper type>', types.I_WRAPPER_TYPE,
                                 __init__=wrapper_func_init,
                                 __str__=wrapper_func_str,
                                 __repr__=wrapper_func_repr,
                                 __getattr__=wrapper_func_getattr,
                                 __setattr__=wrapper_func_setattr)
