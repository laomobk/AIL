from ..core import aobjects as obj
from . import types


def type_init(self, name: str):
    self['__name__'] = name


def type_str(self):
    return '<type \'%s\'>' % self['__name__']


TYPE_TYPE = obj.AILObjectType('<AIL type type>', types.I_TYPE_TYPE,
                              __init__=type_init,
                              __str__=type_str,
                              __repr__=type_str)
