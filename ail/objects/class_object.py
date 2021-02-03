
from typing import List

from .function import PY_FUNCTION_TYPE, FUNCTION_TYPE
from .types import I_CLASS_TYPE, I_OBJECT_TYPE

from ..core.aobjects import (
    AILObject, AILObjectType, ObjectCreater,
    call_object, compare_type, convert_to_ail_object as _conv,
)

from ..core.err_types import TYPE_ERROR, NAME_ERROR
from ..core.aframe import Frame
from ..core.error import AILRuntimeError
from ..core.avmsig import VMInterrupt, MII_CONTINUE


def _get_method_str_func(obj_name: str):
    def _method_str(m):
        return '<method %s of %s at %s>' % (
                m['__name__'], obj_name, hex(id(m)))
    return _method_str


def _check_bound(self, aobj: AILObject):
    if isinstance(aobj, AILObject) and \
            aobj['__class__'] in (FUNCTION_TYPE, PY_FUNCTION_TYPE):

        aobj['__repr__'] = _get_method_str_func(self['__name__'])
        aobj['__this__'] = self  # bound self to __this__
        return aobj
    return None


def class_init(self, 
               name: str, bases: List[AILObject], dict_: dict):
    self['__name__'] = name
    self['__base__'] = bases
    self['__dict__'] = dict_


def class_getattr_with_default(cls, name, default=None):
    return cls['__dict__'].get(name, default)


def class_getattr(cls, name):
    cls['__dict__'].get(
        name, AILRuntimeError('name %s is not define' % name, NAME_ERROR))


def class_setattr(self, name, value):
    self['__dict__'][name] = value


def class_str(self):
    return '<class \'%s\'>' % self['__name__']


def check_class(cls):
    if not compare_type(cls, CLASS_TYPE):
        return False
    return True


def build_class(class_func, class_name, bases) -> AILObject:
    func_frame = Frame()

    call_object(class_func, frame=func_frame)

    class_dict = func_frame.variable

    return ObjectCreater.new_object(CLASS_TYPE, class_name, bases, class_dict)


def new_object(_class, *args):
    if not compare_type(_class, CLASS_TYPE):
        return AILRuntimeError('__new__() needs class object', TYPE_ERROR)

    obj = ObjectCreater.new_object(OBJECT_TYPE)

    obj['__this_class__'] = _class

    obj_dict = dict()
    obj['__dict__'] = obj_dict

    for k, v in _class['__dict__'].items():
        if _check_bound(obj, v):
            obj_dict[k] = v

    init = class_getattr_with_default(_class, '__init__')
    call_object(init, *args)

    return obj


CLASS_TYPE = AILObjectType('<class type>', I_CLASS_TYPE,
                           __init__=class_init,
                           __str__=class_str,
                           __setattr__=class_setattr,
                           __getattr__=class_getattr,)


def object_getattr_with_default(self, name, default=None):
    return self['__dict__'].get(name, default)


def object_getattr(self, name):
    val = self['__dict__'].get(name, None)
    if val is not None:
        return val

    cls = self['__this_class__']
    class_getattr(cls, name)


def object_setattr(self, name, value):
    self['__dict__'][name] = value


def object_getitem(self, name):
    getitem = object_getattr_with_default(self, '__getitem__')
    if getitem is None:
        return AILRuntimeError('\'%s\' object is not subscriptable', TYPE_ERROR)
    call_object(getitem, name)

    raise VMInterrupt(MII_CONTINUE)  # jump over the last operation in VM


def object_setitem(self, name, value):
    setitem = object_getattr_with_default(self, '__setitem__')
    if setitem is None:
        return AILRuntimeError('\'C\' object does not support item assignment', TYPE_ERROR)
    call_object(setitem, name, value)

    raise VMInterrupt(MII_CONTINUE)  # jump over the last operation in VM


def object_str(self):
    cls = self['__this_class__']
    return '<%s object at %s>' % (cls['__name__'], hex(id(self)))


OBJECT_TYPE = AILObjectType(
    '<object type>', I_OBJECT_TYPE,
    __getattr__=object_getattr,
    __setattr__=object_setattr,
    __str__=object_str,
    __repr__=object_str,
)