from core import shared
from core.aobjects import ObjectCreater, AILObject, compare_type
from core.error import AILRuntimeError
from objects.struct import STRUCT_OBJ_TYPE
from objects.function import convert_to_func_wrapper
from objects.null import null

from core.shared import GLOBAL_SHARED_DATA


def _get_sys_path():
    return shared.GLOBAL_SHARED_DATA.find_path


def _get_recur_depth():
    return shared.GLOBAL_SHARED_DATA.max_recursion_depth


def get_cc_object():
    _ccom_t_memb = {
                'paths' : GLOBAL_SHARED_DATA.find_path,
                'max_recursion_depth' : GLOBAL_SHARED_DATA.max_recursion_depth,
                'cwd' : GLOBAL_SHARED_DATA.cwd,
                '_refresh' : convert_to_func_wrapper(get_cc_object)
            }

    _ccom_t = ObjectCreater.new_object(
        STRUCT_OBJ_TYPE, 'CCOM_T', _ccom_t_memb, null, _ccom_t_memb.keys())

    return _ccom_t
