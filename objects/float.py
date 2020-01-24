# float
from aobjects import AILObject, AILObjectType, compare_type, ObjectCreater
from error import AILRuntimeError


def float_str(self :AILObject):
    return '%s' % self['__value__']


def float_init(self :AILObject, value :AILObject):
    if type(value) in (float, int):
        self['__value__'] = value
    elif compare_type(value, FLOAT_TYPE):
        self['__value__'] = value['__value__']


def float_add(self :AILObject, other :AILObject) -> AILObject:
    if not other['__value__']:   # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = self['__value__']

    try:
        res = sv + so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return ObjectCreater.new_object(FLOAT_TYPE, res)


def float_sub(self :AILObject, other :AILObject) -> AILObject:
    if not other['__value__']:   # do not have __value__ property
        return AILRuntimeError('Not support \'-\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = self['__value__']

    try:
        res = sv - so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return ObjectCreater.new_object(FLOAT_TYPE, res)


def float_div(self :AILObject, other :AILObject) -> AILObject:
    if not other['__value__']:   # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    if other['__value__'] == 0:
        return AILRuntimeError('0 cannot be used as a divisor', 'ZeroDivisonError')

    sv = self['__value__']
    so = self['__value__']

    try:
        res = sv / so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return ObjectCreater.new_object(FLOAT_TYPE, res)


def float_muit(self :AILObject, other :AILObject) -> AILObject:
    if not other['__value__']:   # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = self['__value__']

    try:
        res = sv * so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return ObjectCreater.new_object(FLOAT_TYPE, res)


FLOAT_TYPE = AILObjectType('<AIL float type>',
                             __init__=float_init,
                             __add__=float_add,
                             __str__=float_str,
                             __div__=float_div,
                             __muit__=float_muit)
