from typing import Iterable

from . import types
from . import integer
from ..core import aobjects as objs
from ..core.error import AILRuntimeError


def array_init(self: objs.AILObject, pylist: list):
    # check object
    pl = pylist.copy()

    for index, item in enumerate(pl):
        pl[index] = objs.convert_to_ail_object(item)

    self['__value__'] = pl


def array_str(self: objs.AILObject):
    return '{%s}' % (', '.join([repr(x) for x in self['__value__']]))


def _check_index(self, index):
    if isinstance(index, objs.AILObject) and \
            index['__class__'] == integer.INTEGER_TYPE:
        i = index['__value__']

    elif isinstance(index, int):
        i = index

    else:
        return AILRuntimeError('array subscript index must be integer.', 'TypeError')

    l = self['__value__']

    if i >= len(l):
        return AILRuntimeError('index out of range (len %s, index %s)' %
                               (len(l), str(i)), 'IndexError')
    return i


def array_getitem(self, index: int):
    i = _check_index(self, index)
    if isinstance(i, AILRuntimeError):
        return i

    l = self['__value__']

    return objs.convert_to_ail_object(l[i])


def array_setitem(self, index, value):
    i = _check_index(self, index)
    if isinstance(i, AILRuntimeError):
        return i

    l = self['__value__']

    l[i] = value


def array_len(self):
    return len(self['__value__'])


ARRAY_TYPE = objs.AILObjectType('<AIL array type>', types.I_ARRAY_TYPE,
                                __init__=array_init,
                                __getitem__=array_getitem,
                                __setitem__=array_setitem,
                                __str__=array_str,
                                __repr__=array_str,
                                __len__=array_len,
                                )


def convert_to_array(iterable: Iterable):
    if type(iterable) in (list, set, tuple):
        return objs.ObjectCreater.new_object(ARRAY_TYPE, list(iterable))
    return None
