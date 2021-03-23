
from copy import deepcopy
from typing import List

from .function import PY_FUNCTION_TYPE, FUNCTION_TYPE
from .super_object import get_super
from .types import I_CLASS_TYPE, I_OBJECT_TYPE

from ..core.aobjects import (
    AILObject, AILObjectType, ObjectCreater,
    call_object, compare_type, convert_to_ail_object as _conv, get_state,
    create_object
)

from ..core.err_types import TYPE_ERROR, NAME_ERROR
from ..core.aframe import Frame
from ..core.error import AILRuntimeError
from ..core.avmsig import VMInterrupt, MII_CONTINUE


_func_type = (FUNCTION_TYPE, PY_FUNCTION_TYPE)


def _clear_empty(x):
    i = 0

    while i < len(x):
        if len(x[i]) == 0:
            x.pop(i)
        else:
            i += 1


def _get_method_str_func(obj_name: str, is_pyfunc: bool=False):
    def _method_str(m):
        return '<method%s %s of %s object at %s>' % (
                ' wrapper' if is_pyfunc else '',
                m['__name__'], obj_name, hex(id(m)))
    return _method_str


def _copy_function(f: AILObject) -> AILObject:
    new_f = deepcopy(f)
    new_f.properties = f.properties.copy()

    return new_f


def _check_bound(self, aobj, class_name: str):
    cls = aobj['__class__']
    if isinstance(aobj, AILObject) and cls in _func_type:
        aobj = _copy_function(aobj)

        aobj['__repr__'] = _get_method_str_func(
                class_name, cls is PY_FUNCTION_TYPE)
        aobj['__self__'] = self  # bound self to __this__
        return aobj
    return None


def class_init(self, 
               name: str, bases: List[AILObject], dict_: dict, doc_string='', 
               protected_member: list = None):
    self['__name__'] = name
    self['__bases__'] = bases
    self['__dict__'] = dict_
    self['__protected_member__'] = protected_member 
    
    mro = calculate_mro(self)

    self['__mro__'] = mro
    dict_['__mro__'] = _conv(mro)
    self['__doc__'] = doc_string

    dict_['__doc__'] = doc_string


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

    call_object(class_func, frame=func_frame, throw_top=True)

    class_dict = func_frame.variable

    doc_string = class_func['__doc__']
    if doc_string is None:
        doc_string = ''

    return create_object(
            CLASS_TYPE, class_name, bases, class_dict, doc_string)


def new_class(class_name: str, bases: List[AILObject], _dict: dict, doc_string=''):
    return create_object(
        CLASS_TYPE, class_name, bases, _dict, doc_string)


def calculate_mro(cls):
    # using C3 linearization algorithm to calculate mro
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

    cls_new = class_getattr_with_default(_class, '__new__')
    if cls_new is not None:
        call_object(cls_new, _class, *args)
        return get_state().global_interpreter.pop_top()

    obj = create_object(OBJECT_TYPE)

    obj['__this_class__'] = _class

    obj['__init__'](obj)

    init = class_getattr_with_default(_class, '__init__')
    if init is not None:
        call_object(init, obj, *args, throw_top=True)

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


def object_init(self):
    self._bound_methods = dict()
    self.hash_handler = object_hash
    obj_dict = dict()

    self['__dict__'] = obj_dict

    obj_dict['__class__'] = self['__this_class__']


def object_getattr(self, name):
    if name == '__attrs__':
        return self['__dict__']
    val = self['__dict__'].get(name, None)
    if val is not None:
        return val

    cls = self['__this_class__']
    val = class_getattr_with_default(cls, name)

    if val is None:
        return AILRuntimeError('name %s is not define' % name, NAME_ERROR)

    if val['__class__'] not in _func_type:
        return val

    # method key = %CLASS_NAME%$%INSTANCE_ID%$%METHOD_NAME%
    method_key = '%s$%s$%s' % (cls['__name__'], id(self), name)
    bound_methods = self._bound_methods
    m = bound_methods.get(method_key)
    
    if m is not None:
        return m

    m = _check_bound(self, val, cls['__name__'])
    bound_methods[method_key] = m
    
    return m


def object_setattr(self, name, value):
    self['__dict__'][name] = value


def object_getitem(self, name):
    getitem = class_getattr_with_default(self, '__getitem__')
    if getitem is None:
        return AILRuntimeError('\'%s\' object is not subscriptable', TYPE_ERROR)
    call_object(getitem, self, name)

    raise VMInterrupt(MII_CONTINUE)  # jump over the last operation in VM


def object_setitem(self, name, value):
    setitem = class_getattr_with_default(self, '__setitem__')
    if setitem is None:
        return AILRuntimeError('\'C\' object does not support item assignment', TYPE_ERROR)
    call_object(setitem, self, name, value)

    raise VMInterrupt(MII_CONTINUE)  # jump over the last operation in VM


def object_str(self):
    cls = self['__this_class__']
    to_str = class_getattr_with_default(cls, '__str__')
    if to_str is not None:
        call_object(to_str, self)
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


def object_hash(self):
    cls = self['__this_class__']
    hash_m = class_getattr_with_default(cls, '__hash__')

    if hash_m is None:
        return AILRuntimeError('unhashable object', 'TypeError')

    call_object(hash_m, self)
    return VMInterrupt(MII_CONTINUE)


def object___str__(self):
    cls = self['__this_class__']
    return '<%s object at %s>' % (cls['__name__'], hex(id(self)))


def object___repr__(self):
    cls = self['__this_class__']
    return '<%s object at %s>' % (cls['__name__'], hex(id(self)))


OBJECT_TYPE = AILObjectType(
    '<object type>', I_OBJECT_TYPE,
    __init__=object_init,
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
