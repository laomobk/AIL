from .functions import *
from .objects import convert_object

from ..core import abuiltins as _builtins
from ..core.aobjects import unpack_ailobj
from ..core.modules.console import get_console_object as _get_console_object


_builtins.init_builtins()


_PY_BUILTINS = {
    'globals', 'locals'
}


AIL_PY_GLOBAL = {
    k: convert_object(v)
    for k, v in _builtins.BUILTINS.items()
    if k not in _PY_BUILTINS
}


AIL_PY_GLOBAL.update({
    '__ail_input__': ail_input,
    '__ail_import__': ail_import,
    'console': convert_object(_get_console_object()),
})

