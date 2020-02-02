
from error import AILRuntimeError
import aobjects as objs

import objects.bool as abool
import objects.integer as aint
import objects.string as astr
import objects.float as afloat
import objects.function as afunc
import objects.wrapper as awrapper
import objects.null as null


def func_abs(x :objs.AILObject):
    if x['__value__'] is not None and x['__class__'] in (aint.INTEGER_TYPE, afloat.FLOAT_TYPE):
        v = x['__value__']
        return v if v >= 0 else -v

    return AILRuntimeError('abs need a AIL number argument, but got %s' % repr(x))


def func_neg(x :objs.AILObject):
    if x['__value__'] is not None and x['__class__'] in (aint.INTEGER_TYPE, afloat.FLOAT_TYPE):
        v = x['__value__']
        return -v if v > 0 else v

    return AILRuntimeError('abs need a AIL number argument, but got %s' % repr(x))


def func_int_input(msg :objs.AILObject):
    try:
        i = int(input(str(msg)))

        return i
    except ValueError as e:
        return AILRuntimeError(str(e), 'ValueError')
