# normal methods for ail object
import aobjects as obj
from objects import bool
from error import AILRuntimeError


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


def obj_getattr(aobj, name):
    if name not in obj.INVISIBLE_ATTRS and name in aobj.properties:
        return aobj[name]
    return AILRuntimeError('\'%s\' object has no attribute \'%s\'' % (aobj['__class__'].name, name),
                           'AttributeError')


def obj_setattr(aobj, name, value):
    from objects import string

    if obj.compare_type(name, string.STRING_TYPE):
        name = string.convert_to_string(name)
    aobj.properties[name] = value
