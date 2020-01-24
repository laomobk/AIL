# Integer
import aobjects as obj
from error import AILRuntimeError
from . import float

POOL_RANGE = (-5, 128)


def int_str(self :obj.AILObject):
    return '%d' % self['__value__']


def int_init(self :obj.AILObject, value :obj.AILObject):
    if isinstance(value, int):
        self['__value__'] = value
    elif obj.compare_type(value, INTEGER_TYPE):
        self['__value__'] = value['__value__']


def int_add(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if not other['__value__']:   # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv + so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    if res in range(*POOL_RANGE):
        return INTEGER_POOL[int(res - POOL_RANGE[0])]
    return obj.ObjectCreater.new_object(INTEGER_TYPE, res)


def int_sub(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if not other['__value__']:   # do not have __value__ property
        return AILRuntimeError('Not support \'-\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv - so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    if res in range(*POOL_RANGE):
        return INTEGER_POOL[int(POOL_RANGE[0] + res)]
    return obj.ObjectCreater(INTEGER_TYPE, res)


def int_div(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if not other['__value__']:   # do not have __value__ property
        return AILRuntimeError('Not support \'/\' with type %s' % str(other), 'TypeError')

    if other['__value__'] == 0:
        return AILRuntimeError('0 cannot be used as a divisor', 'ZeroDivisonError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv / so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return obj.ObjectCreater.new_object(float.FLOAT_TYPE, res)


def int_muit(self :obj.AILObject, other :obj.AILObject) -> obj.AILObject:
    if not other['__value__']:   # do not have __value__ property
        return AILRuntimeError('Not support \'*\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv * so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    if res in range(*POOL_RANGE):
        return INTEGER_POOL[int(POOL_RANGE[0] + res)]
    return obj.ObjectCreater.new_object(INTEGER_TYPE, res)


INTEGER_TYPE = obj.AILObjectType('<AIL integer type>',
                             __init__=int_init,
                             __add__=int_add,
                             __str__=int_str,
                             __div__=int_div,
                             __muit__=int_muit)


class _IntegerPool:
    def __init__(self):
        self.__pool = list()

        self.__init_pool()

    def __init_pool(self):
        mi, ma = POOL_RANGE

        for num in range(mi, ma):
            num = ObjectCreater.new_object(INTEGER_TYPE, num)
            self.__pool.append(num)

    @property
    def pool(self):
        return self.__pool


INTEGER_POOL = _IntegerPool().pool
