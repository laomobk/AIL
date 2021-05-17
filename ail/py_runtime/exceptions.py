
import sys as _sys
import traceback as _traceback


class AILInputException(Exception):
    pass


class AILImportError(Exception):
    pass


class AILModuleNotFoundError(AILImportError):
    pass


def print_py_traceback():
    tb_type, tb_value, tb_traceback = _sys.exc_info()

    _sys.last_traceback = tb_traceback
    _sys.last_type = tb_type
    _sys.last_value = tb_value

    _traceback.print_exception(tb_type, tb_value, tb_traceback.tb_next)

