# Integer
from ..core.aobjects import (
        unpack_ailobj, compare_type, ObjectCreater, 
        AILObject, AILObjectType, create_object
)

from ..core.error import AILRuntimeError
from . import float as afloat, types
from . import integer as aint
from . import bool as abool


_PY_NUM_TYPES = (int, float)


def _replace_j_with_i(complex_repr: str) -> str:
    return complex_repr.replace('j', 'i', 1)


def complex_str(self: AILObject):
    return _replace_j_with_i(str(self['__value__']))


def complex_repr(self):
    return _replace_j_with_i(repr(self['__value__']))


def complex_init(self: AILObject, *real_imag_or_complex):
    if len(real_imag_or_complex) == 2:
        real, imag = real_imag_or_complex
        if type(real) in _PY_NUM_TYPES and type(imag) in _PY_NUM_TYPES:
            self['__value__'] = complex(real, imag)
        else:
            return AILRuntimeError('real and imag must be integer', 'TypeError')
    elif len(real_imag_or_complex) == 1:
        cplx = real_imag_or_complex[0]
        if compare_type(cplx, COMPLEX_TYPE):
            self['__value__'] = cplx['__value__']
        elif type(cplx) == complex:
            self['__value__'] = cplx
        else:
            return AILRuntimeError('argument must be complex number', 'TypeError')
    else:
        return AILRuntimeError('the number of arguments should be 1 or 2', 'TypeError')


def complex_add(self: AILObject, other: AILObject) -> AILObject:
    if not compare_type(other, *_VALID_TYPES):
        return AILRuntimeError(
            'Not support \'+\' with type %s' % other['__class__'].name, 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv + so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return to_complex(res)


def complex_sub(self: AILObject, other: AILObject) -> AILObject:
    if not compare_type(other, *_VALID_TYPES):
        return AILRuntimeError(
            'Not support \'-\' with type %s' % other['__class__'].name, 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv - so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return to_complex(res)


def complex_muit(self: AILObject, other: AILObject) -> AILObject:
    if not compare_type(other, *_VALID_TYPES):
        return AILRuntimeError(
            'Not support \'*\' with type %s' % other['__class__'].name, 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv * so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return to_complex(res)


def complex_div(self: AILObject, other: AILObject) -> AILObject:
    if compare_type(other, *_VALID_TYPES):
        return AILRuntimeError(
            'Not support \'/\' with type %s' % other['__class__'].name, 'TypeError')

    sv = self['__value__']
    so = other['__value__']

    try:
        res = sv / so
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonRuntimeError')

    return to_complex(res)


def complex_eq(self: AILObject, o: AILObject):
    if isinstance(o, AILObject):
        return create_object(
                abool.BOOL_TYPE, self['__value__'] == o['__value__'])
    return create_object(
            abool.BOOL_TYPE, self['__value__'] == o)


def int_to_string(self):
    return str(self)


COMPLEX_TYPE = AILObjectType('<complex type>', types.I_COMPLEX_TYPE,
                                 __init__=complex_init,
                                 __add__=complex_add,
                                 __div__=complex_div,
                                 __muit__=complex_muit,
                                 __sub__=complex_sub,
                                 __eq__=complex_eq,
                                 __repr__=complex_repr,
                                 __str__=complex_str,
                                 )

_VALID_TYPES = (aint.INTEGER_TYPE, afloat.FLOAT_TYPE, COMPLEX_TYPE)


def to_complex(num):
    if isinstance(num, complex):
        return create_object(COMPLEX_TYPE, num)
    elif compare_type(num, COMPLEX_TYPE):
        return num
    else:
        return AILRuntimeError('cannot convert number to complex', 'ObjectError')

