
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


def func_py_getattr(pyobj, name):
    if isinstance(pyobj, objs.AILObject) and \
            pyobj['__class__'] == awrapper.WRAPPER_TYPE:
        o = pyobj['__pyobject__']

        if isinstance(name, objs.AILObject) and \
            name['__class__'] == astr.STRING_TYPE:
                n = name['__value__']
                if hasattr(o, n):
                    return getattr(o, n)
        else:
            return AILRuntimeError('attribute name must be string ', 'TypeError')
        return AILRuntimeError('\'%s\' object has attribute \'%s\'' % (str(type(o)), str(name)))
    else:
        return AILRuntimeError('A python object wrapper required.', 'TypeError')


def func_chr(x):
    if isinstance(x, objs.AILObject) and \
            x['__class__'] == aint.INTEGER_TYPE:
        v = x['__value__']
    elif isinstance(x, int):
        v = x
    else:
        return AILRuntimeError('chr() needs an integer', 'TypeError')

    return chr(v)


def func_ord(x):
    if isinstance(x, objs.AILObject) and \
            x['__class__'] == astr.STRING_TYPE:
        v = x['__value__']
    elif isinstance(x, int):
        v = x
    else:
        return AILRuntimeError('ord() needs a string', 'TypeError')

    return ord(v)


def func_hex(x):
    if isinstance(x, objs.AILObject) and \
            x['__class__'] == aint.INTEGER_TYPE:
        v = x['__value__']
    elif isinstance(x, int):
        v = x
    else:
        return AILRuntimeError('hex() needs an integer', 'TypeError')

    return hex(v)


def func_int_input(msg :objs.AILObject):
    try:
        i = int(input(str(msg)))

        return i
    except ValueError as e:
        return AILRuntimeError(str(e), 'ValueError')
