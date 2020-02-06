
from error import AILRuntimeError
import aobjects as objs

import objects.bool as abool
import objects.integer as aint
import objects.string as astr
import objects.float as afloat
import objects.function as afunc
import objects.wrapper as awrapper
import objects.null as null
import objects.type as atype
import objects.array as array
import objects.struct as struct


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


def func_type(name, default_attrs :objs.AILObject=None):
    if default_attrs is not None and \
            not objs.compare_type(default_attrs, array.ARRAY_TYPE):
        return AILRuntimeError('type() needs an array to set default attribute.')
    return objs.ObjectCreater.new_object(atype.TYPE_TYPE, name, default_attrs)


def new_struct(struct_type, default_list=None):
    # return a struct object

    if default_list is not None and \
            not objs.compare_type(default_list, array.ARRAY_TYPE):
        return AILRuntimeError('member initialize need an array')
    elif default_list is not None:
        default_list = default_list['__value__']

    if not objs.compare_type(struct_type, struct.STRUCT_TYPE):
        return AILRuntimeError('new() need a struct type')

    m = struct_type.members.keys()

    if default_list is not None:
        if len(default_list) < len(m):
            return AILRuntimeError(
                'struct \'%s\' initialize missing %d required argument(s) : %s' %
                (struct_type['__name__'], len(m), '(%s)' % (', '.join(m))),
                'TypeError')
        elif len(default_list) > len(m):
            return AILRuntimeError(
                'struct \'%s\' initialize takes %d argument(s) but %d were given' %
                (struct_type['__name__'], len(m), len(default_list)),
                'TypeError')

    if default_list is not None:
        md = {k:v for k, v in zip(m, default_list)}
    else:
        md = {k:null.null for k in m}

    n = struct_type['__name__']

    return objs.ObjectCreater.new_object(
        struct.STRUCT_OBJ_TYPE, n, md)
