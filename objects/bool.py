# Bool
import aobjects as obj

def bool_init(self :obj.AILObject, v :obj.AILObject):
    if v == obj.null or v['__value__'] == 0 or v['__value__'] == False or (not v):
        vv = False
    else:
        vv = True

    self['__value__'] = vv


def bool_eq(self :obj.AILObject, o :obj.AILObject) -> obj.AILObject:
    return obj.ObjectCreater.new_object(BOOL_TYPE, o)


BOOL_TYPE = obj.AILObjectType('<AIL bool type>',
                              __init__=bool_init,
                              __eq__=bool_eq)
