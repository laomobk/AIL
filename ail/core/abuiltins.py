
from .error import AILRuntimeError
from . import aobjects as objs
from . import corecom as ccom

from .version import (
    AIL_MAIN_VERSION as _AIL_MAIN_VERSION, 
    AIL_VERSION as _AIL_VERSION
)

from .modules._fileio import _open

from ..objects import (
    string  as astr,
    integer as aint,
    bool    as abool,
    wrapper as awrapper,
    float   as afloat,
    array   as array,
    struct  as struct,
    fastnum,
    null,
)


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


'''
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
'''


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


def func_make_type(name, default_attrs :objs.AILObject=None):
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

    if objs.compare_type(struct_type, struct.STRUCT_OBJ_TYPE):
        return AILRuntimeError('new() needs a struct type, not a struct object', 
                               'TypeError')

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

    md.update(struct_type['__bind_functions__'])

    name = struct_type['__name__']
    pl = struct_type.protected

    return objs.ObjectCreater.new_object(
        struct.STRUCT_OBJ_TYPE, name, md, struct_type, pl)


def func_len(o :objs.AILObject):
    if isinstance(o, objs.AILObject):
        if o['__len__'] is not None:
            return o['__len__'](o)
        return AILRuntimeError('\'%s\' object has no len()' %
                o['__class__'].name, 'TypeError')


def func_type(o :objs.AILObject):
    if o['__class__'] == struct.STRUCT_OBJ_TYPE:
        return o['__type__']
    return o['__class__'].otype


def func_equal(a, b):
    return a == b


def func_array(size):
    if objs.compare_type(size, aint.INTEGER_TYPE):
        l = [null.null for _ in range(size['__value__'])]
        o = objs.ObjectCreater.new_object(array.ARRAY_TYPE, l)
        return o
    return AILRuntimeError('array() needs an integer.', 'TypeError')


def func_isinstance(o, stype):
    if objs.compare_type(o, struct.STRUCT_OBJ_TYPE) and \
            objs.compare_type(stype, struct.STRUCT_TYPE):
        return o['__type__'] == stype
    return False


def func_equal_type(a, b):
    if isinstance(a, objs.AILObject) and isinstance(b, objs.AILObject):
        return a['__class__'].otype == b['__class__'].otype
    return False


def func_str(a):
    return str(a)


def func_repr(a):
    return repr(a)


def func_show_struct(sobj):
    if not (objs.compare_type(sobj, struct.STRUCT_OBJ_TYPE) or
                objs.compare_type(sobj, struct.STRUCT_TYPE)):
        return AILRuntimeError('show_struct needs a struct type or object', 'TypeError')
    
    ln1 = str(sobj) + '\n'
    memb = sobj.members.items()
    meml = '\n'.join(['\t%s : %s' % (k, v) for k, v in memb 
                        if k[:2] != '__'])
    block = '{\n%s\n}' % meml

    return ln1 + block


def func_int(obj):
    v = objs.unpack_ailobj(obj)

    try:
        return int(v)
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonError')


def func_float(obj):
    v = objs.unpack_ailobj(obj)

    try:
        return float(v)
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonError')


def func_addr(obj):
    return id(obj)


def func_fnum(obj):
    v = objs.unpack_ailobj(obj)

    if type(v) in (int, float):
        return fastnum.FastNumber(v)


true = objs.ObjectCreater.new_object(abool.BOOL_TYPE, 1)
false = objs.ObjectCreater.new_object(abool.BOOL_TYPE, 0)


BUILTINS = {
    'abs' : objs.convert_to_ail_object(func_abs),
    'ng' : objs.convert_to_ail_object(func_neg),
    'int_input' : objs.convert_to_ail_object(func_int_input),
    '__version__' : objs.convert_to_ail_object(_AIL_VERSION),
    '__main_version__' : objs.convert_to_ail_object(_AIL_MAIN_VERSION),
    'chr' : objs.convert_to_ail_object(func_chr),
    'ord' : objs.convert_to_ail_object(func_ord),
    'hex' : objs.convert_to_ail_object(func_hex),
    'make_type' : objs.convert_to_ail_object(func_make_type),
    'new' : objs.convert_to_ail_object(new_struct),
    'null' : null.null,
    'true' : true,
    'false' : false,
    'len' : objs.convert_to_ail_object(func_len),
    'equal' : objs.convert_to_ail_object(func_equal),
    'type' : objs.convert_to_ail_object(func_type),
    'array' : objs.convert_to_ail_object(func_array),
    'equal_type' : objs.convert_to_ail_object(func_equal_type),
    'isinstance' : objs.convert_to_ail_object(func_isinstance),
    'str' : objs.convert_to_ail_object(func_str),
    'repr' : objs.convert_to_ail_object(func_repr),
    '_get_ccom' : objs.convert_to_ail_object(ccom.get_cc_object),
    'open' : objs.convert_to_ail_object(_open),
    'int' : objs.convert_to_ail_object(func_int),
    'float': objs.convert_to_ail_object(func_float),
    'addr': objs.convert_to_ail_object(func_addr),
    'fnum': objs.convert_to_ail_object(func_fnum),
}
