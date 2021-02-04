from .error import AILRuntimeError

from . import aconfig
from . import aobjects as objs
from . import corecom as ccom

from .version import (
    AIL_MAIN_VERSION as _AIL_MAIN_VERSION,
    AIL_VERSION as _AIL_VERSION
)

from .modules._fileio import _open
from .modules.console import get_console_object
from .modules.helper import print_help

from .anamespace import Namespace
from .astate import MAIN_INTERPRETER_STATE

from .err_types import *

from ..objects import (
    string  as astr,
    integer as aint,
    bool    as abool,
    wrapper as awrapper,
    float   as afloat,
    complex as acomplex,
    array   as array,
    map     as amap,
    struct  as struct,
    module  as amodule,
    fastnum,
    null,
    super_object
)


def func_abs(x: objs.AILObject):
    if x['__value__'] is not None and x['__class__'] in (aint.INTEGER_TYPE, afloat.FLOAT_TYPE):
        v = x['__value__']
        return v if v >= 0 else -v

    return AILRuntimeError('abs need a AIL number argument, but got %s' % repr(x))


def func_neg(x: objs.AILObject):
    if x['__value__'] is not None and x['__class__'] in (aint.INTEGER_TYPE, afloat.FLOAT_TYPE):
        v = x['__value__']
        return -v if v > 0 else v

    return AILRuntimeError('abs need a AIL number argument, but got %s' % repr(x))


def func_globals():
    ns_dict = MAIN_INTERPRETER_STATE.namespace_state.ns_global.ns_dict
    return amap.convert_to_ail_map(ns_dict)


def func_builtins():
    ns_dict = MAIN_INTERPRETER_STATE.namespace_state.ns_builtins.ns_dict
    return amap.convert_to_ail_map(ns_dict)


def func_locals():
    frame_stack = MAIN_INTERPRETER_STATE.frame_stack
    if len(frame_stack) > 0:
        return amap.convert_to_ail_map(frame_stack[-1].variable)
    return AILRuntimeError('No frame found', 'VMError')


def func_dir(module):
    if objs.compare_type(module, amodule.MODULE_TYPE):
        return amap.convert_to_ail_map(module['__namespace__'])
    return AILRuntimeError('dir() requires a module object', 'TypeError')


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


def func_int_input(msg: objs.AILObject):
    try:
        i = int(input(str(msg)))

        return i
    except ValueError as e:
        return AILRuntimeError(str(e), 'ValueError')


def func_make_type(name, default_attrs: objs.AILObject = None):
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
        md = {k: v for k, v in zip(m, default_list)}
    else:
        md = {k: null.null for k in m}
    
    bind_func = struct_type['__bind_functions__']
    md.update(bind_func)

    name = struct_type['__name__']
    pl = struct_type.protected 

    return objs.ObjectCreater.new_object(
        struct.STRUCT_OBJ_TYPE, name, md, struct_type, pl)


def func_len(o: objs.AILObject):
    if isinstance(o, objs.AILObject):
        if o['__len__'] is not None:
            return o['__len__'](o)
        return AILRuntimeError('\'%s\' object has no len()' %
                               o['__class__'].name, 'TypeError')


def func_type(o: objs.AILObject):
    if o['__class__'] == struct.STRUCT_OBJ_TYPE:
        return o['__type__']
    return o['__class__'].otype


def func_equal(a, b):
    return a == b


def func_array(size, default=None):
    if objs.compare_type(size, aint.INTEGER_TYPE):
        if default is None:
            l = [null.null for _ in range(size['__value__'])]
        else:
            l = [objs.unpack_ailobj(default)
                    for _ in range(size['__value__'])]
        o = objs.ObjectCreater.new_object(array.ARRAY_TYPE, l)
        return o
    return AILRuntimeError('array() needs an integer.', 'TypeError')


def func_map(*args):
    if len(args) == 0:
        return amap.convert_to_ail_map(dict())
    elif len(args) == 1:
        pairs = args[0]

        if not isinstance(pairs, list):
            return AILRuntimeError(
                    'all of map(pairs) arguments must be array.', 'TypeError')

        m = dict()
        for p in pairs:
            p = objs.unpack_ailobj(p)
            if not isinstance(p, list) or len(p) != 2:
                return AILRuntimeError(
                        'each pair must like: [key, value]', 'ValueError')
            k, v = p
            m[k] = v

        return amap.convert_to_ail_map(m)
    else:
        return AILRuntimeError('map() needs 0 or 1 arguments', 'ValueError')


def func_isinstance(o, stype):
    if objs.compare_type(o, struct.STRUCT_OBJ_TYPE) and \
            objs.compare_type(stype, struct.STRUCT_TYPE):
        return o['__type__'] == stype
    return False


def func_isimplement(type_or_obj, *stypes):
    if len(stypes) == 0:
        return AILRuntimeError(
                'isimplement() needs two or more arguments', 'ValueError')

    _type = type_or_obj
    _is_reserved_name = struct._is_reserved_name

    if objs.compare_type(type_or_obj, struct.STRUCT_TYPE):
        pass
    elif objs.compare_type(type_or_obj, struct.STRUCT_OBJ_TYPE):
        _type = type_or_obj['__type__']
    else:
        return AILRuntimeError('isimplement() needs struct or object')

    members = _type.members + list(_type['__bind_functions__'].keys())

    for stype in stypes:
        if not objs.compare_type(stype, struct.STRUCT_TYPE):
            return AILRuntimeError('isimplement(): not a struct')

        for s_member in stype.members + list(stype['__bind_functions__'].keys()):
            if _is_reserved_name(s_member):
                continue
            if s_member not in members:
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


def func_complex(real, imag):
    real = objs.unpack_ailobj(real)
    imag = objs.unpack_ailobj(imag)

    return objs.ObjectCreater.new_object(acomplex.COMPLEX_TYPE, real, imag)


true = objs.ObjectCreater.new_object(abool.BOOL_TYPE, 1)
false = objs.ObjectCreater.new_object(abool.BOOL_TYPE, 0)

BUILTINS = {}
BUILTINS_NAMESPACE = Namespace('builtins', BUILTINS)

def init_builtins():
    global BUILTINS, BUILTINS_NAMESPACE

    BUILTINS = {
        'abs': objs.convert_to_ail_object(func_abs),
        'ng': objs.convert_to_ail_object(func_neg),
        'int_input': objs.convert_to_ail_object(func_int_input),
        '__version__': objs.convert_to_ail_object(_AIL_VERSION),
        '__main_version__': objs.convert_to_ail_object(_AIL_MAIN_VERSION),
        'chr': objs.convert_to_ail_object(func_chr),
        'ord': objs.convert_to_ail_object(func_ord),
        'hex': objs.convert_to_ail_object(func_hex),
        'make_type': objs.convert_to_ail_object(func_make_type),
        'new': objs.convert_to_ail_object(new_struct),
        'null': null.null,
        'true': true,
        'false': false,
        'len': objs.convert_to_ail_object(func_len),
        'equal': objs.convert_to_ail_object(func_equal),
        'type': objs.convert_to_ail_object(func_type),
        'array': objs.convert_to_ail_object(func_array),
        'equal_type': objs.convert_to_ail_object(func_equal_type),
        'isinstance': objs.convert_to_ail_object(func_isinstance),
        'isimplement': objs.convert_to_ail_object(func_isimplement),
        'str': objs.convert_to_ail_object(func_str),
        'repr': objs.convert_to_ail_object(func_repr),
        '_get_ccom': objs.convert_to_ail_object(ccom.get_cc_object),
        'open': objs.convert_to_ail_object(_open),
        'int': objs.convert_to_ail_object(func_int),
        'float': objs.convert_to_ail_object(func_float),
        'addr': objs.convert_to_ail_object(func_addr),
        'fnum': objs.convert_to_ail_object(func_fnum),
        'globals': objs.convert_to_ail_object(func_globals),
        'builtins': objs.convert_to_ail_object(func_builtins),
        'locals': objs.convert_to_ail_object(func_locals),
        'dir': objs.convert_to_ail_object(func_dir),
        'console': objs.convert_to_ail_object(get_console_object()),
        'help': objs.convert_to_ail_object(print_help),
        'complex': objs.convert_to_ail_object(func_complex),
        'map': objs.convert_to_ail_object(func_map),
        'super': objs.convert_to_ail_object(super_object.get_super),

        ATTRIBUTE_ERROR: objs.convert_to_ail_object(ATTRIBUTE_ERROR),
        PYTHON_ERROR: objs.convert_to_ail_object(PYTHON_ERROR),
        TYPE_ERROR: objs.convert_to_ail_object(TYPE_ERROR),
        UNHASHABLE_ERROR: objs.convert_to_ail_object(UNHASHABLE_ERROR),
        INDEX_ERROR: objs.convert_to_ail_object(INDEX_ERROR),
        OBJECT_ERROR: objs.convert_to_ail_object(OBJECT_ERROR),
        OS_ERROR: objs.convert_to_ail_object(OS_ERROR),
        LOAD_ERROR: objs.convert_to_ail_object(LOAD_ERROR),
        IMPORT_ERROR: objs.convert_to_ail_object(IMPORT_ERROR),
        RECURSION_ERROR: objs.convert_to_ail_object(RECURSION_ERROR),
        VM_ERROR: objs.convert_to_ail_object(VM_ERROR),
        NAME_ERROR: objs.convert_to_ail_object(NAME_ERROR),
        ZERO_DIVISION_ERROR: objs.convert_to_ail_object(ZERO_DIVISION_ERROR),
        KEY_ERROR: objs.convert_to_ail_object(KEY_ERROR),
    }

    BUILTINS_NAMESPACE = Namespace('builtins', BUILTINS)

