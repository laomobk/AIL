
from copy import deepcopy
from typing import List

from .function import PY_FUNCTION_TYPE, FUNCTION_TYPE
from .super_object import get_super
from .types import I_CLASS_TYPE, I_OBJECT_TYPE

from ..core.aobjects import (
    AILObject, AILObjectType, ObjectCreater,
    call_object, compare_type, convert_to_ail_object as _conv,
)

from ..core.err_types import TYPE_ERROR, NAME_ERROR
from ..core.aframe import Frame
from ..core.error import AILRuntimeError
from ..core.avmsig import VMInterrupt, MII_CONTINUE


def _clear_empty(x):
    i = 0

    while i < len(x):
        if len(x[i]) == 0:
            x.pop(i)
        else:
            i += 1


def _get_method_str_func(obj_name: str):
    def _method_str(m):
        return '<method %s of %s at %s>' % (
                m['__name__'], obj_name, hex(id(m)))
    return _method_str


def _copy_function(f: AILObject) -> AILObject:
    new_f = deepcopy(f)
    new_f.properties = f.properties.copy()

    return new_f


def _check_bound(self, aobj):
    if isinstance(aobj, AILObject) and \
            aobj['__class__'] in (FUNCTION_TYPE, PY_FUNCTION_TYPE):

        aobj = _copy_function(aobj)

        aobj['__repr__'] = _get_method_str_func(self['__name__'])
        aobj['__this__'] = self  # bound self to __this__
        return aobj
    return None


def class_init(self, 
        name: str, bases: List[AILObject], dict_: dict):
    self['__name__'] = name
    self['__bases__'] = bases
    self['__dict__'] = dict_
    
    mro = calculate_mro(self)

    self['__mro__'] = mro
    dict_['__mro__'] = _conv(mro)


def class_getattr_with_default(cls, name, default=None):
    mro = cls['__mro__']
    for cls in mro:
        val = cls['__dict__'].get(name)
        if val is not None:
            return val
    return default


def class_getattr(cls, name):
    mro = cls['__mro__']
    for cls in mro:
        val = cls['__dict__'].get(name)
        if val is not None:
            return val
    return AILRuntimeError('name %s is not define' % name, NAME_ERROR)


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

    if len(bases) == 0:
        bases.append(CLASS_OBJECT)

    call_object(class_func, frame=func_frame)

    class_dict = func_frame.variable

    return ObjectCreater.new_object(
            CLASS_TYPE, class_name, bases, class_dict)


def new_class(class_name: str, bases: List[AILObject], _dict: dict):
    return ObjectCreater.new_object(CLASS_TYPE, class_name, bases, _dict)


def calculate_mro(cls):
    # use C3 linearization algorithm to calculate mro
    bases = cls['__bases__']

    if len(bases) == 0:
        return [cls]
    
    items = [c['__mro__'].copy() for c in bases] + [[c for c in bases]]

    mro = list()
    last_items = items
    
    i = 0
    while i < len(last_items):
        head = last_items[i][0]

        for item in last_items:
            if item is last_items[i]:
                continue

            if head in item[1:]:
                break
        else:
            for _item in last_items:
                if head in _item:
                    _item.remove(head)
            mro.append(head)
            _clear_empty(last_items)
            i = 0
            continue
        i += 1
    
    mro.insert(0, cls)
    return mro


def new_object(_class, *args):
    if not compare_type(_class, CLASS_TYPE):
        return AILRuntimeError('__new__() needs class object', TYPE_ERROR)

    obj = ObjectCreater.new_object(OBJECT_TYPE)

    obj['__this_class__'] = _class

    obj_dict = dict()
    obj['__dict__'] = obj_dict

    for k, v in _class['__dict__'].items():
        v = _check_bound(obj, v)
        if v is not None:
            obj_dict[k] = v

    init = object_getattr_with_default(obj, '__init__')
    if init is not None:
        call_object(init, *args)

    return obj


CLASS_TYPE = AILObjectType('<class type>', I_CLASS_TYPE,
                           __init__=class_init,
                           __str__=class_str,
                           __setattr__=class_setattr,
                           __getattr__=class_getattr,)


def object_getattr_with_default(self, name, default=None):
    val = self['__dict__'].get(name, None)
    if val is not None:
        return val

    cls = self['__this_class__']
    return class_getattr_with_default(cls, name, default)


def object_getattr(self, name):
    val = self['__dict__'].get(name, None)
    if val is not None:
        return val

    cls = self['__this_class__']
    return class_getattr(cls, name)


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
    to_str = object_getattr_with_default(cls, '__str__')
    if to_str is not None:
        call_object(to_str)
        return VMInterrupt(MII_CONTINUE)

    cls = self['__this_class__']
    return '<%s object at %s>' % (cls['__name__'], hex(id(self)))


def object_repr(self):
    cls = self['__this_class__']
    to_str = class_getattr_with_default(cls, '__repr__')
    if to_str is not None:
        call_object(to_str, self)
        return VMInterrupt(MII_CONTINUE)

    cls = self['__this_class__']
    return '<%s object at %s>' % (cls['__name__'], hex(id(self)))


def object___str__(self):
    cls = self['__this_class__']
    return '<%s object at %s>' % (cls['__name__'], hex(id(self)))


def object___repr__(self):
    cls = self['__this_class__']
    return '<%s object at %s>' % (cls['__name__'], hex(id(self)))


OBJECT_TYPE = AILObjectType(
    '<object type>', I_OBJECT_TYPE,
    __getattr__=object_getattr,
    __setattr__=object_setattr,
    __str__=object_str,
    __repr__=object_repr,
)


CLASS_OBJECT = new_class(
    'Object', [], 
    {
        '__str__': _conv(object___str__),
        '__repr__': _conv(object___repr__),
    }
)

