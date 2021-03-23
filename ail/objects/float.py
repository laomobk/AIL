from copy import copy

from ..core import aobjects as obj

from ..core.aobjects import (
    AILObjectType,
    AILObject, convert_to_ail_object, 
    unpack_ailobj, call_object, create_object
)

from ..core.error import AILRuntimeError
from . import types

_new_object = obj.ObjectCreater.new_object


def float_str(self: AILObject):
    return '%s' % self['__value__']


def float_repr(self):
    return '%s' % self['__value__']


def float_init(self: AILObject, value: AILObject):
    _vtype = type(value)

    if _vtype is float or _vtype is int:
        self.properties['__value__'] = value
    elif value['__class__'] is FLOAT_TYPE:
        self['__value__'] = value['__value__']
    else:
        return AILRuntimeError('invalid number type \'%s\'' % type(value), 'TypeError')

    self.set_hash_target(self['__value__'])


def float_add(self: AILObject, other: AILObject) -> AILObject:
    if type(other['__value__']) not in (int, float):  # do not have __value__ property
        return AILRuntimeError(
                'Not support \'+\' with type %s' % other['__class__'].name, 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    res = sv + so

    return _new_object(FLOAT_TYPE, res)


def float_sub(self: AILObject, other: AILObject) -> AILObject:
    if other['__value__'] is None:  # do not have __value__ property
        return AILRuntimeError('Not support \'-\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    res = sv - so

    return _new_object(FLOAT_TYPE, res)


def float_div(self: AILObject, other: AILObject) -> AILObject:
    if other['__value__'] is None:  # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    if other['__value__'] == 0:
        return AILRuntimeError('0 cannot be used as a divisor', 'ZeroDivisonError')

    sv = self['__value__']
    so = other['__value__']

    res = sv / so

    return _new_object(FLOAT_TYPE, res)


def float_muit(self: AILObject, other: AILObject) -> AILObject:
    if other['__value__'] is None:  # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    res = sv * so

    return _new_object(FLOAT_TYPE, res)


def float_mod(self: AILObject, other: AILObject) -> AILObject:
    if other['__value__'] is None:  # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    res = sv % so

    return _new_object(FLOAT_TYPE, res)


def float_pow(self: AILObject, other: AILObject) -> AILObject:
    if other['__value__'] is None:  # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    res = sv ** so

    return _new_object(FLOAT_TYPE, res)


FLOAT_TYPE = AILObjectType('<float type>', types.I_FLOAT_TYPE,
                               __init__=float_init,
                               __add__=float_add,
                               __str__=float_str,
                               __div__=float_div,
                               __sub__=float_sub,
                               __muit__=float_muit,
                               __repr__=float_repr,
                               __mod__=float_mod,
                               __pow__=float_pow
                               )


_conv_types = (int, float, str)


def convert_to_integer(pyint: int):
    from .integer import INTEGER_TYPE
    from .string import STRING_TYPE
    
    cls = pyint['__class__']

    if type(pyint) in _conv_type:
        return _new_object(INTEGER_TYPE, float(pyint))

    if cls is INTEGER_TYPE or cls is FLOAT_TYPE:
        pyint['__value__'] = float(pyint['__value__'])
        return pyint

    elif cls is STRING_TYPE:
        v = pyint['__value__']  # type: str
        if v.isnumeric():
            pyint['__value__'] = float(v)

    return AILRuntimeError('argument must be a string or a number', 'TypeError')
