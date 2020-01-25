# Bool
import aobjects as obj
from . import types

def bool_init(self :obj.AILObject, v :obj.AILObject):
    if not isinstance(v, obj.AILObject):
        vv = False if not v else True
    else:
        if v['__class__'].otype in (types.I_INT_TYPE, types.I_FLOAT_TYPE):
            vv = False if not v['__value__'] else True
        elif v['__class__'].otype == types.I_STR_TYPE:
            vv = False if not v['__value__'] else True
        elif v == obj.null:
            vv = False
        else:
            vv = True

    self['__value__'] = vv


def bool_eq(self :obj.AILObject, o :obj.AILObject) -> obj.AILObject:
    return obj.ObjectCreater.new_object(BOOL_TYPE, o)


def bool_str(self :obj.AILObject):
    return '%s' % ('false' if not self['__value__'] else 'true')


BOOL_TYPE = obj.AILObjectType('<AIL bool type>', types.I_TYPE_TYPE,
                              __init__=bool_init,
                              __eq__=bool_eq,
                              __str__=bool_str)
