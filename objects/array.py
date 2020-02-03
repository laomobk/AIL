
from objects import types
from objects import integer
import aobjects as objs
from error import AILRuntimeError


def array_init(self :objs.AILObject, pylist :list):
    # check object
    pl = pylist.copy()

    for index, item in enumerate(pl):
        pl[index] = objs.convert_to_ail_object(item)

    self['__value__'] = pl


def array_str(self :objs.AILObject):
    return '{%s}' % (', '.join([str(x) for x in self['__value__']]))


def array_getitem(self, index :int):
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

    return objs.convert_to_ail_object(l[i])


ARRAY_TYPE = objs.AILObjectType('<AIL array type>', types.I_ARRAY_TYPE,
                                __init__=array_init,
                                __getitem__=array_getitem,
                                __str__=array_str,
                                __repr__=array_str)
