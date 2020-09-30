# normal methods for ail object
from ..core import aobjects as obj
from . import bool
from ..core.error import AILRuntimeError


def _is_reserved_attr_name(name: str):
    """
    所有以双下划线开头并以之结尾的，
    都属于保留属性名，不能在 AIL 中访问
    """
    if (name[:2], name[-2:]) == ('__', '__'):
        return True
    return False


def obj_func_str(aobj):
    oid = id(aobj)
    hex_id = hex(oid)

    return '<AIL %s object at %s>' % (aobj['__class__'].name, hex_id)


def obj_func_init(aobj):
    """
    :return : Do nothing...
    """
    pass


def obj_func_eq(aobj, oobj):
    b = 0 if id(aobj) != id(oobj) else 1

    return obj.ObjectCreater.new_object(bool.BOOL_TYPE, b)


def obj_getattr(aobj, name):
    if not _is_reserved_attr_name(name) and name in aobj.properties:
        return aobj[name]

    return AILRuntimeError('\'%s\' object has no attribute \'%s\'' %
                           (aobj['__class__'].name, name),
                           'AttributeError')


def obj_setattr(aobj, name, value):
    from . import string

    if obj.compare_type(name, string.STRING_TYPE):
        name = string.convert_to_string(name)

    if not _is_reserved_attr_name(name):
        return AILRuntimeError('\'%s\' object has no attribute \'%s\'' %
                               (aobj['__class__'].name, name),
                               'AttributeError')

    aobj.properties[name] = value


def obj_equals(self, other):
    return self == other
