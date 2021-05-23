from . import functions as _func

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
    'Object', 'FileIO', 'fnum'
}


AIL_PY_GLOBAL = {
    k: convert_object(v)
    for k, v in _builtins.BUILTINS.items()
    if k not in _PY_BUILTINS
}


AIL_PY_GLOBAL.update({
    '__ail_input__': _func.ail_input,
    '__ail_import__': _func.ail_import,
    '__ail_make_struct__': _func.make_struct,
    '__ail_bind_function__': _func.bind_function,
    'new': _func.new_struct_object,
    'contains': _func.contains,
    'console': convert_object(_get_console_object()),
    'fnum': _func.func_fnum,
    'true': True,
    'false': False,
})


# rename py_runtime modules
if RENAME_PY_RUNTIME:
    import sys
    for name, module in sys.modules.items():
        if module.__name__.startswith('ail.py_runtime.'):
            module.__spec__.origin = '<ail python runtime component %s>' % \
                    (module.__name__)

