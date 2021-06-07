from types import FunctionType

from ail.core.error import AILRuntimeError
from ail.core.aobjects import convert_to_ail_object, compare_type

from ail.objects.function import PY_FUNCTION_TYPE
from ail.objects.struct import new_struct_object


def inspect_see_function(ailfunc):
    if not compare_type(ailfunc, PY_FUNCTION_TYPE):
        return AILRuntimeError('py_function_wrapper required')
    pyfunc: FunctionType = ailfunc['__pyfunction__']

    return _new_pyfunc_info(pyfunc)


def _new_pyfunc_info(func: FunctionType):
    name = func.__name__
    addr = id(func)

    _PYFUNC_INFO_STRUCT_DICT['name'] = name
    _PYFUNC_INFO_STRUCT_DICT['addr'] = addr

    return new_struct_object(
            '<PYFUNC_INFO>', None, 
            _PYFUNC_INFO_STRUCT_DICT, _PYFUNC_INFO_STRUCT_DICT.keys())


_PYFUNC_INFO_STRUCT_DICT = {
    'name': None,
    'addr': None,
}

_IS_AIL_MODULE_ = True

_AIL_NAMESPACE_ = {
    'see_pyfunction': convert_to_ail_object(inspect_see_function)
}
