
from . import AIL_PY_GLOBAL


def fill_namespace(ns: dict, name: str = '__main__', main: bool = True):
    ns.update(AIL_PY_GLOBAL)
    ns['__name__'] = name
    ns['__main__'] = main

