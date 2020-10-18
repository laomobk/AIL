
from ..core.aobjects import AILObject
from ..core.error import AILRuntimeError


def map_init(self, pymap: dict = None):
    if pymap is None:
        pymap = dict()
    self['__value__'] = pymap


def map_getitem(self, key: dict):
    return self['__value__'].get(
            key, AILRuntimeError('%s' % str(key)), 'KeyError')

