from . import shared

from .aobjects import (
    ObjectCreater, AILObject, compare_type, unpack_ailobj, convert_to_ail_object
)

from .astate import MAIN_INTERPRETER_STATE
from .error import AILRuntimeError
from ..objects.struct import STRUCT_OBJ_TYPE, convert_to_pyobj, new_struct_object
from ..objects.function import convert_to_func_wrapper
from ..objects.null import null
from ..objects.integer import INTEGER_TYPE

from .shared import GLOBAL_SHARED_DATA


def _get_sys_path():
    return shared.GLOBAL_SHARED_DATA.find_path


def _get_recur_depth():
    return shared.GLOBAL_SHARED_DATA.max_recursion_depth


def _get_err_stack_object():
    es = MAIN_INTERPRETER_STATE.err_stack

    def _empty(this):
        this = convert_to_pyobj(this)
        return len(this.__this___stack) == 0

    def _pop(this):
        this = convert_to_pyobj(this)
        if this.__this___stack:
            return this.__this___stack.pop()
        return null

    stack_d = {
        '__stack': es,
        'empty': convert_to_func_wrapper(_empty),
        'pop': convert_to_func_wrapper(_pop),
    }

    return new_struct_object('ERROR_STACK_T', null, stack_d, stack_d.keys())


def _set_raise_python_error(_, b):
    b = unpack_ailobj(b)
    if isinstance(b, bool):
        MAIN_INTERPRETER_STATE.global_interpreter.set_raise_python_error(b)
        return
    return AILRuntimeError('needs a bool value')


def _sys_exit(_, code):
    if not compare_type(code, INTEGER_TYPE):
        return AILRuntimeError('exit() needs an integer.')

    c = unpack_ailobj(code)

    import sys
    try:
        sys.exit(c)
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonError')


def _get_cc_object(_):
    _ccom_t_memb = {
        'paths': GLOBAL_SHARED_DATA.find_path,
        'max_recursion_depth': GLOBAL_SHARED_DATA.max_recursion_depth,
        'cwd': GLOBAL_SHARED_DATA.cwd,
        '_refresh': convert_to_func_wrapper(_get_cc_object),
        # 'get_err_stack' : convert_to_func_wrapper(_get_err_stack_object)
        'exit': convert_to_func_wrapper(_sys_exit),
        'argv': convert_to_ail_object(shared.GLOBAL_SHARED_DATA.prog_argv),
        'setPythonErrorRaise': convert_to_ail_object(_set_raise_python_error)
    }

    _ccom_t = ObjectCreater.new_object(
        STRUCT_OBJ_TYPE, 'CCOM_T', _ccom_t_memb, null, _ccom_t_memb.keys())

    return _ccom_t


def get_cc_object():
    return _get_cc_object(None)
