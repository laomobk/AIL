# String
import aobjects as obj
from error import AILRuntimeError
from objects import bool, integer
from . import types


def str_init(self, anystr :str):
    if type(anystr) == str:
        self['__value__'] = anystr
    elif type(anystr) == obj.AILObject:
        if anystr['__class__'] == STRING_TYPE:
            self['__value__'] = anystr['__value__']
        else:
            pstr = self['__str__']()
            self['__value__'] = pstr

    else:
        self['__value__'] = str(anystr)


def str_add(self, ostr :obj.AILObject) -> obj.AILObject:
    if type(ostr) != obj.AILObject:
        return AILRuntimeError('Cannot operate with Python object', 'TypeError')
    if ostr['__class__'] != STRING_TYPE:
        return AILRuntimeError('Not support \'+\' with type %s' % ostr['__class__'])

    ss = self['__value__']
    os = ostr['__value__']

    rs = ss + os

    return obj.ObjectCreater.new_object(STRING_TYPE, rs)


def str_muit(self, times :obj.AILObject) -> obj.AILObject:
    if type(times) != obj.AILObject:
        return AILRuntimeError('Cannot operate with Python object', 'TypeError')

    if times['__class__'] != integer.INTEGER_TYPE:
        return AILRuntimeError('Not support \'*\' with type %s' % times['__class__'], 'TypeError')

    t = times['__value__']
    rs = self['__value__'] * t

    return obj.ObjectCreater.new_object(STRING_TYPE, rs)


def str_str(self):
    return '%s' % self['__value__']


def str_repr(self):
    return '\'%s\'' % self['__value__']


def str_eq(self, ostr :obj.AILObject) -> obj.AILObject:
    if type(ostr) != obj.AILObject:
        return AILRuntimeError('Cannot operate with Python object', 'TypeError')

    if ostr['__class__'] != STRING_TYPE:
        return AILRuntimeError('Not support \'==\' with type %s' % ostr['__class__'], 'TypeError')

    ss = self['__value__']
    os = ostr['__value__']

    if len(ss) != len(os):
        return obj.ObjectCreater.new_object(bool.BOOL_TYPE, 0)
    else:
        s = sum([a == b for a, b in zip(ss, os)])
        return obj.ObjectCreater.new_object(bool.BOOL_TYPE, s == len(os))


def convert_to_string(aobj) -> obj.AILObject:
    if isinstance(aobj, obj.AILObject):
        return aobj['__str__'](aobj)
    else:
        return obj.ObjectCreater.new_object(STRING_TYPE, str(aobj))


STRING_TYPE = obj.AILObjectType('<AIL string type>', types.I_STR_TYPE,
                                __init__=str_init,
                                __add__=str_add,
                                __muit__=str_muit,
                                __str__=str_str,
                                __repr__=str_repr,
                                __eq__=str_eq)
