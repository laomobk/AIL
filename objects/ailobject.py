# normal methods for ail object
import aobjects as obj
from objects import bool


def obj_func_str(aobj):
    oid = id(aobj)
    hex_id = hex(oid)

    return '<AIL %s object at %s>' % (aobj['__class__'].name, hex_id)


def obj_func_init(aobj):
    '''
    :return : Do nothing...
    '''
    pass


def obj_func_eq(aobj, oobj):
    b = 0 if id(aobj) != id(oobj) else 1

    return obj.ObjectCreater.new_object(bool.BOOL_TYPE, b)
