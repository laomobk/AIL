# Bool
from ..core import aobjects as obj

from . import types


AILObject = obj.AILObject
AILObjectType = obj.AILObjectType


def bool_init(self: AILObject, v: AILObject):
    if not isinstance(v, AILObject):
        vv = False if not v else True
    else:
        if obj.has_attr(v, '__value__'):
            vv = bool(v['__value__'])

    self['__value__'] = vv


def bool_eq(self: AILObject, o: AILObject) -> AILObject:
    return obj.create_object(BOOL_TYPE, o is self)


def bool_str(self: AILObject):
    return '%s' % ('false' if not self['__value__'] else 'true')


BOOL_TYPE = AILObjectType('<bool type>', types.I_TYPE_TYPE,
                              __init__=bool_init,
                              __eq__=bool_eq,
                              __str__=bool_str)
