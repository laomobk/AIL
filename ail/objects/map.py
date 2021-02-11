
from .types import I_MAP_TYPE

from ..core.aobjects import (
    AILObject, AILObjectType, ObjectCreater, compare_type, call_object,
    create_object
)
from ..core.error import AILRuntimeError


def map_init(self, pydict: dict = None):
    if pydict is None:
        pydict = dict()

    if compare_type(pydict, MAP_TYPE):
        pydict = pydict['__value__']

    self['__value__'] = pydict


def map_getitem(self, key):
    v = self['__value__'].get(key)

    if v is not None:
        return v
    else:
        return AILRuntimeError('%s' % str(key), 'KeyError')


def map_setitem(self, key, value):
    self['__value__'][key] = value


def map_str(self):
    return str(self['__value__'])


def map_for_each(self, func):
    d = self['__value__']
    for key, value in d.items():
        if not call_object(func, key, value, type_check=True):
            break


MAP_TYPE = AILObjectType('<map type>', I_MAP_TYPE,
                         methods={
                            'forEach': map_for_each,
                         },
                         __init__=map_init,
                         __getitem__=map_getitem,
                         __setitem__=map_setitem,
                         __str__=map_str,
                         __repr__=map_str)


def convert_to_ail_map(pydict):
    if isinstance(pydict, AILObject):
        return pydict

    if isinstance(pydict, dict):
        return create_object(MAP_TYPE, pydict)

    return pydict

