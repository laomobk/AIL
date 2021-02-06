from copy import deepcopy
from .types import I_SUPER_TYPE

from ..core.aobjects import (
    AILObjectType,
    convert_to_ail_object, ObjectCreater
)
from ..core.error import AILRuntimeError
from ..core.err_types import ATTRIBUTE_ERROR


def super_init(self, instance, bases, _class):
    self['__this_class__'] = _class
    self['__instance__'] = instance
    self['__bases__'] = bases
    self['__mro__'] = instance['__this_class__']['__mro__']


def _find_class_from_order(self, name):
    order = self['__mro__']
    assert isinstance(order, list)

    cls = self['__this_class__']
    t = order.index(cls)
    
    for base in order[t + 1:]:
        b_dict = base['__dict__']
        assert isinstance(b_dict, dict)

        val = b_dict.get(name)
        if val is not None:
            return base

    return None


def super_getattr(self, name):
    cls = _find_class_from_order(self, name)
    
    if cls is not None:
        return cls['__dict__'][name]

    return AILRuntimeError(
            'super: cannot find attribute from super class', ATTRIBUTE_ERROR)


def super_setattr(self, name, value):
    cls = _find_class_from_order(self, name)

    if cls is not None:
        cls['__dict__'][name] = convert_to_ail_object(value)


def super_str(self):
    cls = self['__this_class__']
    return '<super of %s>' % str(cls)


SUPER_TYPE = AILObjectType(
    '<super type>', I_SUPER_TYPE, 
    __init__=super_init,
    __str__=super_str,
    __getattr__=super_getattr,
    __setattr__=super_setattr,
)


def get_super(_class, instance):
    return ObjectCreater.new_object(
            SUPER_TYPE, instance, _class['__bases__'], _class)

