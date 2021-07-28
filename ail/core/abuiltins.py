
from . import corecom as ccom

from .version import (
    AIL_MAIN_VERSION as _AIL_MAIN_VERSION,
    AIL_VERSION as _AIL_VERSION
)


def func_neg(x):
    """
    neg(x: number) - number
    """
    return -x


def func_globals():
    """
    globals() -> Map[string, any]
    @returns the global namespace
    """
    return globals()


def func_builtins():
    """
    builtins() -> Map[string, any]
    @returns the builtin namespace
    """
    return __builtins__.globals()


def func_int_input(prompt):
    """
    int_input(prompt: string) -> integer
    @throws ValueError if the input value not a ordinal number
    """
    return int(input(prompt))


def func_array(size, default=None):
    """
    array(size: integer [, default: Any]) -> array
    @param size the size of array
    @param default the default value of array
    """
    return [default for _ in range(size)]


def contains(a, b) -> bool:
    """
    :return: b in a
    """
    return a in b


BUILTINS = {}


def init_builtins():
    global BUILTINS

    BUILTINS = {
        'ng': func_neg,
        'int_input': func_int_input,
        '__version__': _AIL_VERSION,
        '__main_version__': _AIL_MAIN_VERSION,
        'array': func_array,
        '_ccom': ccom.get_cc_object(),
        'builtins': func_builtins,
        'contains': contains,
    }
