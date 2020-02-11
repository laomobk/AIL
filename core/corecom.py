from core import shared
from core.aobjects import ObjectCreater, AILObject, compare_type
from core.error import AILRuntimeError
from objects.struct import STRUCT_OBJ_TYPE, convert_to_pyobj, new_struct_object
from objects.function import convert_to_func_wrapper
from objects.null import null
from core.astate import MAIN_INTERPRETER_STATE

from core.shared import GLOBAL_SHARED_DATA


def _get_sys_path():
    return shared.GLOBAL_SHARED_DATA.find_path


def _get_recur_depth():
    return shared.GLOBAL_SHARED_DATA.max_recursion_depth


def _get_err_stack_object(*_):
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
        '__stack' : es,
        'empty' : convert_to_func_wrapper(_empty),
        'pop' : convert_to_func_wrapper(_pop),
    }

    return new_struct_object('ERROR_STACK_T', null, stack_d, stack_d.keys())


def get_cc_object():
    _ccom_t_memb = {
                'paths' : GLOBAL_SHARED_DATA.find_path,
                'max_recursion_depth' : GLOBAL_SHARED_DATA.max_recursion_depth,
                'cwd' : GLOBAL_SHARED_DATA.cwd,
                '_refresh' : convert_to_func_wrapper(get_cc_object),
                'get_err_stack' : convert_to_func_wrapper(_get_err_stack_object)
            }

    _ccom_t = ObjectCreater.new_object(
        STRUCT_OBJ_TYPE, 'CCOM_T', _ccom_t_memb, null, _ccom_t_memb.keys())

    return _ccom_t
