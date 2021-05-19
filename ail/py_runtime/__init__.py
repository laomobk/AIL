from .functions import *
from .objects import convert_object

from ..core import abuiltins as _builtins
from ..core.aconfig import RENAME_PY_RUNTIME
from ..core.aobjects import unpack_ailobj
from ..core.modules.console import get_console_object as _get_console_object


_builtins.init_builtins()


_PY_BUILTINS = {
    'globals', 'locals', 'builtins',
    'help', 'dir',
    'chr', 'ord', 'hex', 'oct',
    'len', 'type', 'isinstance',
    'isimplement', 'str', 'repr',
    'int', 'float', 'super',
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


# rename py_runtime modules
if RENAME_PY_RUNTIME:
    import sys
    for name, module in sys.modules.items():
        if module.__name__.startswith('ail.py_runtime.'):
            module.__spec__.origin = '<ail python runtime component %s>' % \
                    (module.__name__)

