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


def array_init(self: AILObject, pylist: list):
    # check object
    pl = pylist.copy()

    for index, item in enumerate(pl):
        pl[index] = convert_to_ail_object(item)

    self['__value__'] = pl


def array_str(self: AILObject):
    return '[%s]' % (
            ', '.join(
                [repr(x) 
                    if x is not self else '[...]' 
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


def array_getitem(self, index: int):
    i = _check_index(self, index)
    if isinstance(i, AILRuntimeError):
        return i

    l = self['__value__']

    return convert_to_ail_object(l[i])


def array_setitem(self, index, value):
    i = _check_index(self, index)
    if isinstance(i, AILRuntimeError):
        return i

    l = self['__value__']

    l[i] = value


def array_len(self):
    return len(self['__value__'])


def array_append(self, value):
    arr = self['__value__']

    arr.append(value)


def array_pop(self):
    arr = self['__value__']
    
    if len(arr) == 0:
        return AILRuntimeError('pop from empty array', 'IndexError')
    return arr.pop()


def array_contains(self, value):
    arr = self['__value__']
    val = unpack_ailobj(value)

    for x in arr:
        x = unpack_ailobj(x)
        if x == val:
            return True
    return False


def array_count(self, value):
    arr = self['__value__']
    unp = unpack_ailobj
    arr = [unp(x) for x in arr]

    return arr.count(unp(value))


def array_insert(self, index, value):
    arr = self['__value__']
    index = unpack_ailobj(index)

    if not isinstance(index, int):
        return AILRuntimeError(
                'array.insert(x) required an integer', 'TypeError')

    arr.insert(index, value)


def array_remove(self, value):
    arr = self['__value__']
    unp = unpack_ailobj
    arr = [unp(x) for x in arr]
    
    try:
        return arr.remove(unp(value))
    except ValueError:
        return AILRuntimeError('array.remove(x): x not in array', 'ValueError')


def array_sort(self):
    self['__value__'].sort()


def array_index(self, value):
    arr = self['__value__']
    unp = unpack_ailobj
    arr = [unp(x) for x in arr]
    
    try:
        return arr.index(unp(value))
    except ValueError:
        return -1


def array_extend(self, x):
    arr = self['__value__']  # type: list
    x = unpack_ailobj(x)

    if not isinstance(x, list):
        return AILRuntimeError('array.extend(x): x must a array')

    arr.extend(x)


def array_clear(self):
    self['__value__'].clear()


def array_reverse(self):
    self['__value__'].reverse()


def array_copy(self):
    return self['__value__'].copy()


def array_for_each(self, func):
    arr = self['__value__']
    for i, ele in enumerate(arr):
        if not call_object(func, i, ele, type_check=True):
            break



ARRAY_TYPE = AILObjectType('<array type>', types.I_ARRAY_TYPE,
                                methods={
                                    'append': array_append,
                                    'pop': array_pop,
                                    'contains': array_contains,
                                    'count': array_count,
                                    'insert': array_insert,
                                    'remove': array_remove,
                                    'sort': array_sort,
                                    'index': array_index,
                                    'extend': array_extend,
                                    'clear': array_clear,
                                    'reverse': array_reverse,
                                    'copy': array_copy,
                                    'forEach': array_for_each,
                                },
                                __init__=array_init,
                                __getitem__=array_getitem,
                                __setitem__=array_setitem,
                                __str__=array_str,
                                __repr__=array_str,
                                __len__=array_len,
                                )


def convert_to_array(iterable: Iterable):
    if isinstance(iterable, IterableType):
        return create_object(ARRAY_TYPE, list(iterable))
    return None
