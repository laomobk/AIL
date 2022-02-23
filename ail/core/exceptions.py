
from ail import _config

from os.path import join as _join
from types import TracebackType as _TracebackType
import sys as _sys
import traceback as _traceback


_PY_RUNTIME_DIR = _join(_config.AIL_DIR_PATH, 'core')
_PY_EXEC_FILE = _join(_config.AIL_DIR_PATH, 'core', 'pyexec.py')
_AIL_SHELL_FILE = _join(_config.AIL_DIR_PATH, 'core', 'ashell.py')
_AIL_PARSER_FILE = _join(_config.AIL_DIR_PATH, 'core', 'aparser.py')
_AIL_ERROR_FILE = _join(_config.AIL_DIR_PATH, 'core', 'error.py')

_PATHS = (
    _PY_RUNTIME_DIR, 
    _PY_EXEC_FILE, 
    _AIL_SHELL_FILE, 
    _AIL_PARSER_FILE,
    _AIL_ERROR_FILE
)

_CHINESE_CHARACTER_UTF_RANGE = range(0x4e00, 0x9fa6)


class AILRuntimeError(Exception):
    pass


class AILInputException(Exception):
    pass


class AILImportError(Exception):
    pass


class AILModuleNotFoundError(AILImportError):
    pass


class UnhandledMatchError(Exception):
    pass


class _AILTracebackException(_traceback.TracebackException):
    def format_exception_only(self) -> str:
        # re-write SyntaxError format only
        if not issubclass(self.exc_type, SyntaxError):
            yield from super().format_exception_only()
            return

        stype = self.exc_type.__qualname__

        filename = self.filename or "<string>"
        lineno = str(self.lineno) or '?'
        yield '  File "{}", line {}\n'.format(filename, lineno)

        badline = self.text
        offset = self.offset

        if badline is not None:
            yield '    {}\n'.format(badline.strip())
            if offset is not None:
                caret_space = badline.rstrip('\n')
                offset = min(len(caret_space), offset) - 1
                caret_space = caret_space[:offset].lstrip()
                caret_space = (self.__get_space(c) for c in caret_space)
                yield '    {}^\n'.format(''.join(caret_space))

        msg = self.msg or "<no detail available>"
        yield "{}: {}\n".format(stype, msg)

    def __get_space(self, char: str) -> str:
        # align tab or some non-space character
        if char.isspace() and char:
            return char

        if ord(char) in _CHINESE_CHARACTER_UTF_RANGE:
            return '　'  # full-width space
        return ' '


def remove_py_runtime_traceback(tb: _TracebackType):
    current = tb
    last: _TracebackType = tb
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

    _print_exception(tb_value, tb_value.__traceback__)


def _print_exception(value, tb, limit=None, file=None, chain=True):
    if file is None:
        file = _sys.stderr
    for line in _AILTracebackException(
            type(value), value, tb, limit=limit).format(chain=chain):
        print(line, file=file, end="")
