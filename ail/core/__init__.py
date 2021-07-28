import builtins

from . import abuiltins as _builtins, exceptions as _exception, objects as _object, functions as _func
from .aconfig import RENAME_PY_RUNTIME
from .error import AILSyntaxError, BuiltinAILRuntimeError
from ail.modules.console import console as _console
from ail.modules.system import SYSTEM_OBJECT

_builtins.init_builtins()


_PY_BUILTINS = {
    'globals', 'locals', 'builtins',
    'help', 'dir',
    'chr', 'ord', 'hex', 'oct',
    'len', 'type', 'isinstance',
    'isimplement', 'str', 'repr',
    'int', 'float', 'super',
    'Object', 'FileIO', 'fnum',
    'abs', 'map',
    'open',
}


AIL_PY_GLOBAL = {
    k: v
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
    'console': _console,
    'fnum': _func.func_fnum,
    'true': True,
    'false': False,
    'system': SYSTEM_OBJECT,
    'UnhandledMatchError': _exception.UnhandledMatchError,
    'aeval': _func.ail_eval,
    'AILSyntaxError': AILSyntaxError,
    'BuiltinAILRuntimeError': BuiltinAILRuntimeError,

    'py::UnhandledMatchError': _exception.UnhandledMatchError,
    'py::raise': _func.raise_exception,
    'py::locals': locals,

    'ail::match': _func.ail_match,
    'ail::ObjectPattern': _object.ObjectPattern,
    'ail::namespace': _func.convert_to_namespace,
    'ail::using': _func.ail_using,
})


# overwrite builtins
builtins.__dict__.update(AIL_PY_GLOBAL)


# rename py_runtime modules
if RENAME_PY_RUNTIME:
    import sys
    for name, module in sys.modules.items():
        if module.__name__.startswith('ail.py_runtime.'):
            module.__spec__.origin = '<ail python runtime component %s>' % \
                                     module.__name__

