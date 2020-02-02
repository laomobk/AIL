# float
import aobjects as obj
from error import AILRuntimeError
from . import types


def float_str(self :obj.AILObject):
    return '%s' % self['__value__']


def float_repr(self):
    return '<%s>' % self['__value__']


def float_init(self :obj.AILObject, value :obj.AILObject):
    if type(value) in (float, int):
        self['__value__'] = value
    elif obj.compare_type(value, FLOAT_TYPE):
        self['__value__'] = value['__value__']


def float_add(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if other['__value__'] is None:   # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = self['__value__']

    try:
        res = sv + so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return obj.ObjectCreater.new_object(FLOAT_TYPE, res)


def float_sub(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if other['__value__'] is None:   # do not have __value__ property
        return AILRuntimeError('Not support \'-\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = self['__value__']

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
    so = self['__value__']

    try:
        res = sv / so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return obj.ObjectCreater.new_object(FLOAT_TYPE, res)


def float_muit(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if other['__value__'] is None:   # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = self['__value__']

    try:
        res = sv * so
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
                             )
