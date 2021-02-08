
from .types import I_BYTES_TYPE

from ..core.aobjects import (
    AILObjectType, unpack_ailobj
)
from ..core.error import AILRuntimeError


def bytes_init(self, py_bytes: bytes):
    self['__value__'] = py_bytes


def bytes_repr(self):
    return repr(self['__value__'])


def bytes_str(self):
    return str(self['__value__'])


def bytes_decode(self, encoding='UTF-8'):
    encoding = unpack_ailobj(encoding)
    if not isinstance(encoding, str):
        return AILRuntimeError(
            '\'encoding\' must be string', 'TypeError')

    val = self['__value__']

    try:
        return val.decode(encoding)
    except UnicodeDecodeError as e:
        return AILRuntimeError(e.reason, 'UnicodeDecodeError')


BYTES_TYPE = AILObjectType(
    '<bytes type>', I_BYTES_TYPE,
    methods={
        'decode': bytes_decode,
    },
    __init__=bytes_init,
    __repr__=bytes_repr,
    __str__=bytes_str,
)
