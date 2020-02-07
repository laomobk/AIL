# float
import aobjects as obj
from error import AILRuntimeError
from . import types


def float_str(self :obj.AILObject):
    return '%s' % self['__value__']


def float_repr(self):
    return '< %s >' % self['__value__']


def float_init(self :obj.AILObject, value :obj.AILObject):
    if type(value) in (float, int):
        self['__value__'] = value
    elif obj.compare_type(value, FLOAT_TYPE):
        self['__value__'] = value['__value__']


def float_add(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if type(other['__value__']) not in (int , float):   # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % other['__class__'].name, 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv + so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return obj.ObjectCreater.new_object(FLOAT_TYPE, res)


def float_sub(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if other['__value__'] is None:   # do not have __value__ property
        return AILRuntimeError('Not support \'-\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv - so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return obj.ObjectCreater.new_object(FLOAT_TYPE, res)


def float_div(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if other['__value__'] is None:   # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    if other['__value__'] == 0:
        return AILRuntimeError('0 cannot be used as a divisor', 'ZeroDivisonError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv / so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return obj.ObjectCreater.new_object(FLOAT_TYPE, res)


def float_muit(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if other['__value__'] is None:   # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv * so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return obj.ObjectCreater.new_object(FLOAT_TYPE, res)


def float_mod(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if other['__value__'] is None:   # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv % so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return obj.ObjectCreater.new_object(FLOAT_TYPE, res)


def float_pow(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if other['__value__'] is None:   # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv ** so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return obj.ObjectCreater.new_object(FLOAT_TYPE, res)


FLOAT_TYPE = obj.AILObjectType('<AIL float type>', types.I_FLOAT_TYPE,
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


def convert_to_integer(pyint :int):
    from objects import integer, string

    try:
        if pyint['__class__'] in (
                integer.INTEGER_TYPE, FLOAT_TYPE, string.STRING_TYPE):
                pyint['__value__'] = float(pyint['__value__'])
                return pyint

        elif type(pyint) in (int, float, str):
                return obj.ObjectCreater.new_object(integer.INTEGER_TYPE, float(pyint))

    except ValueError as e:
        return AILRuntimeError(str(e), 'ValueError')

    return AILRuntimeError('argument must be a string or a number', 'TypeError')
