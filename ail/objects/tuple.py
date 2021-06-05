from collections import Iterable as IterableType
from typing import Iterable

from . import types
from . import integer

from ..core.aobjects import (
    AILObjectType,
    AILObject, convert_to_ail_object, 
    unpack_ailobj, call_object, create_object
)

from ..core.astate import MAIN_INTERPRETER_STATE
from ..core.error import AILRuntimeError


def tuple_init(self: AILObject, pylist: list):
    # check object
    pl = pylist.copy()

    for index, item in enumerate(pl):
        pl[index] = convert_to_ail_object(item)

    self['__value__'] = pl


def tuple_str(self: AILObject):
    return '(%s)' % (
            ', '.join(
                [repr(x) 
                    if x is not self else '(...)' 
                    for x in self['__value__']]))


def _check_index(self, index):
    if isinstance(index, AILObject) and \
            index['__class__'] == integer.INTEGER_TYPE:
        i = index['__value__']

    elif isinstance(index, int):
        i = index

    else:
        return AILRuntimeError(
                'array subscript index must be integer.', 'TypeError')

    l = self['__value__']
    vlen = len(l)
    ri = i

    if i < 0:
        i = vlen + i

    if i >= vlen or i < 0:
        return AILRuntimeError('index out of range (len %s, index %s)' %
                               (vlen, str(ri)), 'IndexError')
    return i


def tuple_getitem(self, index: int):
    i = _check_index(self, index)
    if isinstance(i, AILRuntimeError):
        return i

    l = self['__value__']

    return convert_to_ail_object(l[i])


def tuple_len(self):
    return len(self['__value__'])




TUPLE_TYPE = AILObjectType('<tuple type>', types.I_TUPLE_TYPE,
                                __init__=tuple_init,
                                __getitem_=tuple_getitem,
                                __str__=tuple_str,
                                __repr__=tuple_str,
                                __len__=tuple_len,
                                )


def convert_to_tuple(iterable: Iterable):
    if isinstance(iterable, IterableType):
        return create_object(TUPLE_TYPE, list(iterable))
    return None

