from .error import AILRuntimeError

from . import aobjects as objs
from . import corecom as ccom

from .version import (
    AIL_MAIN_VERSION as _AIL_MAIN_VERSION,
    AIL_VERSION as _AIL_VERSION
)

from ail.modules._fileio import _open
from ail.modules.console import get_console_object
from ail.modules.helper import print_help
from ail.modules.fileio import CLASS_FILEIO

from .anamespace import Namespace
from .astate import MAIN_INTERPRETER_STATE

from .err_types import *

from ..objects import (
    string  as astr,
    integer as aint,
    bool    as abool,
    float   as afloat,
    complex as acomplex,
    array   as array,
    map     as amap,
    struct  as struct,
    module  as amodule,
    fastnum,
    null,
    super_object,
    class_object,
)


def func_abs(x: objs.AILObject):
    """
    abs(x: integer) -> integer
    @returns x if x >= 0 else -x
    """
    x = objs.unpack_ailobj(x)
    if isinstance(x, int):
        return x if x >= 0 else -x

    return AILRuntimeError('abs need a AIL number argument, but got %s' % repr(x), 'TypeError')


def func_neg(x: objs.AILObject):
    """
    neg(x: number) - number
    """
    if x['__value__'] is not None and x['__class__'] in (
            aint.INTEGER_TYPE, afloat.FLOAT_TYPE):
        v = x['__value__']
        return -v if v > 0 else v

    return AILRuntimeError('abs need a AIL number argument, but got %s' % repr(x), 'TypeError')


def func_globals():
    """
    globals() -> Map[string, any]
    @returns the global namespace
    """
    ns_dict = MAIN_INTERPRETER_STATE.namespace_state.ns_global.ns_dict
    return amap.convert_to_ail_map(ns_dict)


def func_builtins():
    """
    builtins() -> Map[string, any]
    @returns the builtin namespace
    """
    ns_dict = MAIN_INTERPRETER_STATE.namespace_state.ns_builtins.ns_dict
    return amap.convert_to_ail_map(ns_dict)


def func_locals():
    """
    locals() -> Map[string, any]
    @returns the local namespace
    """
    frame_stack = MAIN_INTERPRETER_STATE.frame_stack
    if len(frame_stack) > 0:
        return amap.convert_to_ail_map(frame_stack[-1].variable)
    return AILRuntimeError('No frame found', 'VMError')


def func_dir(module):
    """
    dir(module: module) -> Map[string, any]
    @returns a map of namespace
    """
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
    """
    chr(x: integer) -> string
    @param x x in [0, 0x10ffff]
    @returns an unicode string of one character with ordinal x
    """
    if isinstance(x, objs.AILObject) and \
            x['__class__'] == aint.INTEGER_TYPE:
        v = x['__value__']
    elif isinstance(x, int):
        v = x
    else:
        return AILRuntimeError('chr() needs an integer', 'TypeError')

    return chr(v)


def func_ord(x):
    """
    ord(x: string) -> integer
    @param x an unicode string of one charater
    @returns the unicode code point for x.
    """
    if isinstance(x, objs.AILObject) and \
            x['__class__'] == astr.STRING_TYPE:
        v = x['__value__']
    elif isinstance(x, int):
        v = x
    else:
        return AILRuntimeError('ord() needs a string', 'TypeError')

    return ord(v)


def func_hex(x):
    """
    hex(x: integer) -> string
    @returns the representation of x
    """
    if isinstance(x, objs.AILObject) and \
            x['__class__'] == aint.INTEGER_TYPE:
        v = x['__value__']
    elif isinstance(x, int):
        v = x
    else:
        return AILRuntimeError('hex() needs an integer', 'TypeError')

    return hex(v)


def func_int_input(msg: objs.AILObject):
    """
    int_input(prompt: string) -> integer
    @throws ValueError if the input value not a ordinal number
    """
    try:
        i = int(input(str(msg)))
        return i
    except ValueError as e:
        return AILRuntimeError(str(e), 'ValueError')


def new_struct(struct_type, default_list=None):
    """
    new(structType: Struct [, defaultList: array]) -> StructObject
    @returns a struct object of StructType, if no default list provided, all attributes
    will set null
    """
    # return a struct object

    if default_list is not None and \
            not objs.compare_type(default_list, array.ARRAY_TYPE):
        return AILRuntimeError('member initialize need an array', 'TypeError')
    elif default_list is not None:
        default_list = default_list['__value__']

    if objs.compare_type(struct_type, struct.STRUCT_OBJ_TYPE):
        return AILRuntimeError('new() needs a struct type, not a struct object',
                               'TypeError')

    if not objs.compare_type(struct_type, struct.STRUCT_TYPE):
        return AILRuntimeError('new() need a struct type', 'TypeError')

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
    """
    len(o: array|string) -> int
    @returns the length of the param o
    """
    if isinstance(o, objs.AILObject):
        if o['__len__'] is not None:
            return o['__len__'](o)
        return AILRuntimeError('\'%s\' object has no len()' %
                               o['__class__'].name, 'TypeError')
    else:
        return len(o)


def func_type(o: objs.AILObject):
    """
    type(o: Any) -> integer
    @returns the type number of param o
    """
    if o['__class__'] == struct.STRUCT_OBJ_TYPE:
        return o['__type__']
    return o['__class__'].otype


def func_equal(a, b):
    """
    equal(a: Any, b: Any) -> boolean
    @returns address of a == address of b
    """
    return id(a) == id(b)


def func_array(size, default=None):
    """
    array(size: integer [, default: Any]) -> array
    @param size the size of array
    @param default the default value of array
    """
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
    """
    map(pairs: Array[List])
    """
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


def func_isinstance(o, _type):
    """
    isinstance(obj :Object|StructObject, clsOrStruct: Class|Struct) -> boolean
    @return whether a object is an instance of a class or subclass or whether
            an struct object is created from that struct
    """
    if objs.compare_type(o, struct.STRUCT_OBJ_TYPE) and \
            objs.compare_type(_type, struct.STRUCT_TYPE):
        return o['__type__'] == _type
    elif objs.compare_type(o, class_object.OBJECT_TYPE):
        o_cls = o['__this_class__']
        if not objs.compare_type(_type, class_object.CLASS_TYPE):
            return False

        if _type is o_cls:
            return True

        o_mro = o_cls['__mro__']
        for cls in o_mro:
            if _type is cls:
                return True
    return False


def func_isimplement(type_or_obj, *stypes):
    """
    isimplement(typeOrObject: Struct|StructObject, *structTypes: StructType) -> boolean
    @return whether a struct type or struct object have all bound functions in struct type(s)
    """
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
        return AILRuntimeError('isimplement() needs struct or object', 'TypeError')

    members = _type.members + list(_type['__bind_functions__'].keys())

    for stype in stypes:
        if not objs.compare_type(stype, struct.STRUCT_TYPE):
            return AILRuntimeError('isimplement(): not a struct', 'TypeError')

        for s_member in stype.members + list(stype['__bind_functions__'].keys()):
            if _is_reserved_name(s_member):
                continue
            if s_member not in members:
                return False


def func_doc(o):
    """
    doc(o: Any) -> string
    @return the doc string of an object
    @return '' if no doc string
    """
    doc_string = o['__doc__']
    if doc_string is None:
        return ''
    return doc_string


def func_equal_type(a, b):
    """
    equal_type(a: Any, b: Any) -> boolean
    @return whether the type of a equals the type of b
    """
    if isinstance(a, objs.AILObject) and isinstance(b, objs.AILObject):
        return a['__class__'].otype == b['__class__'].otype
    return False


def func_str(a):
    """
    str(x: Any) -> string
    @returns the string form of an object
    """
    return objs.get_state().global_interpreter.check_object(
        a['__str__'](a), not_convert=True)


def func_repr(a):
    """
    repr(x: Any) -> string
    @returns the printable representation of an object
    """
    repr_f = a['__repr__']
    if repr_f is None:
        repr_f = a['__str__']
    return objs.get_state().global_interpreter.check_object(repr_f(a))


def func_show_struct(sobj):
    """
    show_struct(obj: StructObject) -> string
    @returns a pretty info string of the struct object
    """
    if not (objs.compare_type(sobj, struct.STRUCT_OBJ_TYPE) or
            objs.compare_type(sobj, struct.STRUCT_TYPE)):
        return AILRuntimeError('show_struct needs a struct type or object', 'TypeError')

    ln1 = str(sobj) + '\n'
    memb = sobj.members.items()
    meml = '\n'.join(['\t%s : %s' % (k, v) for k, v in memb
                      if k[:2] != '__'])
    block = '{\n%s\n}' % meml

    return ln1 + block


_py_int_func_types = (str, int, float)


def func_int(obj):
    """
    int(x: string|integer|float) -> integer
    convert x to integer
    """
    v = objs.unpack_ailobj(obj)

    try:
        return int(v)
    except (ValueError, TypeError) as _:
        return AILRuntimeError('cannot convert %s to integer' % obj, 'TypeError')
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonError')


def func_float(obj):
    """
    float(x: string|integer|float) -> float
    convert x to float
    """

    v = objs.unpack_ailobj(obj)

    try:
        return float(v)
    except (ValueError, TypeError) as _:
        return AILRuntimeError('cannot convert %s to float' % obj, 'TypeError')
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonError')


def func_addr(obj):
    """
    addr(x: Any) -> integer
    @returns the address of the object in memory.
    """
    return id(obj)


def func_fnum(obj):
    """
    fnum(x: integer|float) -> _fastnum
    @returns the FastNumber wrapper of x
    """
    v = objs.unpack_ailobj(obj)

    if type(v) in (int, float):
        return fastnum.FastNumber(v)


def func_complex(real, imag):
    """
    complex(real: integer, imag: integer) -> Complex
    @returns an complex: real + imag j
    """
    real = objs.unpack_ailobj(real)
    imag = objs.unpack_ailobj(imag)

    return objs.ObjectCreater.new_object(acomplex.COMPLEX_TYPE, real, imag)


def func_super(_class, instance):
    """
    super(type: Class, obj: Object) -> Class
    @returns the next (or last) class in the MRO table of an object
    """
    if objs.compare_type(_class, class_object.CLASS_TYPE) and \
            objs.compare_type(instance, class_object.OBJECT_TYPE):
        return super_object.get_super(_class, instance)


def func_hash(o):
    return hash(o)


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
        'super': objs.convert_to_ail_object(func_super),
        'doc': objs.convert_to_ail_object(func_doc),
        'hash': objs.convert_to_ail_object(func_hash),
        'show_struct': objs.convert_to_ail_object(func_show_struct),
        'Object': class_object.CLASS_OBJECT,
        'FileIO': CLASS_FILEIO,

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
        UNICODE_DECODE_ERROR: objs.convert_to_ail_object(UNICODE_DECODE_ERROR),
        UNICODE_ENCODE_ERROR: objs.convert_to_ail_object(UNICODE_ENCODE_ERROR),
        FILE_NOT_FOUND_ERROR: objs.convert_to_ail_object(FILE_NOT_FOUND_ERROR),
    }

    BUILTINS_NAMESPACE = Namespace('builtins', BUILTINS)
