# Integer
from ..core import aobjects as obj

from ..core.aobjects import (
    AILObjectType,
    AILObject, convert_to_ail_object, 
    unpack_ailobj, call_object, create_object,
    compare_type
)

from ..core.error import AILRuntimeError
from . import float as afloat, types
from . import bool as abool

from .bool import BOOL_TYPE
from .float import FLOAT_TYPE


POOL_RANGE_MIN = -1
POOL_RANGE_MAX = 100
POOL_RANGE = (POOL_RANGE_MIN, POOL_RANGE_MAX)


def _get_a_b(self, other, op: str) -> tuple:
    if other['__value__'] is None:  # do not have __value__ property
        return AILRuntimeError(
                'Not support \'%s\' with type %s' % (op, str(other)), 'TypeError'), 0

    sv = self['__value__']
    so = other['__value__']

    return sv, so


def int_str(self: AILObject):
    return '%d' % self['__value__']


def int_repr(self):
    return '%d' % self['__value__']


def int_init(self: AILObject, value: AILObject):
    if isinstance(value, int):
        self['__value__'] = value
    elif isinstance(value, float):
        o = create_object(FLOAT_TYPE, value)
        self.reference = o.reference
        self.properties = o.properties
    elif compare_type(value, INTEGER_TYPE):
        self['__value__'] = value['__value__']
    else:
        return AILRuntimeError('invalid number type \'%s\'' % type(value), 'TypeError')

    self.set_hash_target(self['__value__'])


def int_add(self: AILObject, other: AILObject) -> AILObject:
    if other['__class__'] not in (INTEGER_TYPE, FLOAT_TYPE):  # do not have __value__ property
        return AILRuntimeError(
            'Not support \'+\' with type %s' % other['__class__'].name, 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv + so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return get_integer(res)


def int_sub(self: AILObject, other: AILObject) -> AILObject:
    if other['__value__'] is None:  # do not have __value__ property
        return AILRuntimeError('Not support \'-\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv - so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return get_integer(res)


def int_div(self: AILObject, other: AILObject) -> AILObject:
    if other['__value__'] is None:  # do not have __value__ property
        return AILRuntimeError('Not support \'/\' with type %s' % str(other), 'TypeError')

    if other['__value__'] == 0:
        return AILRuntimeError('0 cannot be used as a divisor', 'ZeroDivisonError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv / so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return get_integer(res)


def int_muit(self: AILObject, other: AILObject) -> AILObject:
    if other['__value__'] is None:  # do not have __value__ property
        return AILRuntimeError('Not support \'*\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv * so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return get_integer(res)


def int_mod(self: AILObject, other: AILObject) -> AILObject:
    if other['__value__'] is None:  # do not have __value__ property
        return AILRuntimeError('Not support \'mod\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv % so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return get_integer(res)


def int_pow(self: AILObject, other: AILObject) -> AILObject:
    if other['__value__'] is None:  # do not have __value__ property
        return AILRuntimeError('Not support \'^\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv ** so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return get_integer(res)


def int_lshift(self: AILObject, other: AILObject) -> AILObject:
    sv, so = _get_a_b(self, other, '<<')
    if isinstance(sv, AILRuntimeError):
        return sv

    try:
        res = sv << so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return get_integer(res)


def int_rshift(self: AILObject, other: AILObject) -> AILObject:
    sv, so = _get_a_b(self, other, '>>')
    if isinstance(sv, AILRuntimeError):
        return sv

    try:
        res = sv >> so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return get_integer(res)


def int_and(self: AILObject, other: AILObject) -> AILObject:
    sv, so = _get_a_b(self, other, '&')
    if isinstance(sv, AILRuntimeError):
        return sv

    try:
        res = sv & so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return get_integer(res)


def int_or(self: AILObject, other: AILObject) -> AILObject:
    sv, so = _get_a_b(self, other, '|')
    if isinstance(sv, AILRuntimeError):
        return sv

    try:
        res = sv | so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return get_integer(res)


def int_xor(self: AILObject, other: AILObject) -> AILObject:
    sv, so = _get_a_b(self, other, 'xor')
    if isinstance(sv, AILRuntimeError):
        return sv

    try:
        res = sv ^ so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return get_integer(res)


def int_inc(self: AILObject):
    val = self['__value__']
    
    return get_integer(val + 1)


def int_dec(self: AILObject):
    val = self['__value__']
    
    return get_integer(val - 1)


def int_eq(self: AILObject, o: AILObject):
    if isinstance(o, AILObject):
        return create_object(BOOL_TYPE, self['__value__'] == o['__value__'])
    return create_object(BOOL_TYPE, self['__value__'] == o)


def int_to_string(self):
    return str(self)


INTEGER_TYPE = AILObjectType('<integer type>', types.I_INT_TYPE,
                                 methods={'to_string': int_to_string},
                                 __init__=int_init,
                                 __add__=int_add,
                                 __str__=int_str,
                                 __div__=int_div,
                                 __muit__=int_muit,
                                 __sub__=int_sub,
                                 __eq__=int_eq,
                                 __repr__=int_repr,
                                 __mod__=int_mod,
                                 __pow__=int_pow,
                                 __lshift__=int_lshift,
                                 __rshift__=int_rshift,
                                 __and__=int_and,
                                 __or__=int_or,
                                 __xor__=int_xor,
                                 __inc__=int_inc,
                                 __dec__=int_dec,
                                 )


def get_integer(pyint: int) -> AILObject:
    """
    get an integer object.

    if pyint in [POOL_RANGE_MIN, POOL_RANGE_MAX), returns the integer in pool,
    otherwise, create an integer object.

    :return: Integer object
    """
    if not isinstance(pyint, int):
        return pyint

    if POOL_RANGE_MIN < pyint < POOL_RANGE_MAX:
        return INTEGER_POOL[pyint - POOL_RANGE_MIN]
    return create_object(INTEGER_TYPE, pyint)


class _IntegerPool:
    def __init__(self):
        self.__pool = list()

        self.__init_pool()

    def __init_pool(self):
        mi, ma = POOL_RANGE

        for num in range(mi, ma):
            num = create_object(INTEGER_TYPE, num)
            num.reference += 1
            self.__pool.append(num)

    @property
    def pool(self):
        return self.__pool


INTEGER_POOL = _IntegerPool().pool

_conv_types = (int, float, str)


def convert_to_integer(pyint: int):
    from .string import STRING_TYPE

    if type(pyint) in _conv_types:
        return get_integer(pyint)
    
    cls = pyint['__class__']
    if cls is INTEGER_TYPE or cls is FLOAT_TYPE:
        pyint['__value__'] = int(pyint['__value__'])
        return pyint
    elif cls is STRING_TYPE:
        v = pyint['__value__']  # type: str
        if v.isnumeric():
            pyint['__value__'] = int(v)

    return AILRuntimeError('argument must be a string or a number', 'TypeError')
