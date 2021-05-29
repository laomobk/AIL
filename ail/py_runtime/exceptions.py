
from os.path import join as _join

from .. import _config

from types import TracebackType as _TracebackType
import sys as _sys
import traceback as _traceback


_PY_RUNTIME_DIR = _join(_config.AIL_DIR_PATH, 'py_runtime')
_PY_EXEC_FILE = _join(_config.AIL_DIR_PATH, 'core', 'pyexec.py')
_AIL_SHELL_FILE = _join(_config.AIL_DIR_PATH, 'core', 'ashell.py')

_PATHS = (_PY_RUNTIME_DIR, _PY_EXEC_FILE, _AIL_SHELL_FILE)


class AILRuntimeError(Exception):
    pass


class AILInputException(Exception):
    pass


class AILImportError(Exception):
    pass


class AILModuleNotFoundError(AILImportError):
    pass


def remove_py_runtime_traceback(tb: _TracebackType):
    current = tb
    last: _TracebackType = None
    head: _TracebackType = None 

    while current is not None:
        if current.tb_frame.f_code.co_filename.startswith(_PATHS):
            current = current.tb_next
            if current is None:
                last.tb_next = None
            continue

        if head is None:
            head = current
        
        if last is not None:
            last.tb_next = current
            last = current
        else:
            last = current

        current = current.tb_next

    return head


def erase_py_runtime_stack_trace_in_exception(exception: BaseException):
    exception.__traceback__ = remove_py_runtime_traceback(exception.__traceback__)
    context = exception.__context__
    if context is None:
        return
    return erase_py_runtime_stack_trace_in_exception(context)


def print_py_traceback():
    tb_type, tb_value, tb_traceback = _sys.exc_info()

    if _config.REMOVE_PY_RUNTIME_TRACEBACK:
        erase_py_runtime_stack_trace_in_exception(tb_value)

    _sys.last_traceback = tb_value.__traceback__
    _sys.last_type = tb_type
    _sys.last_value = tb_value

    _traceback.print_exception(tb_type, tb_value, tb_value.__traceback__)

