
from ..error import AILRuntimeError
from ..aobjects import compare_type, unpack_ailobj
from ...objects.array import convert_to_array
from ...objects.function import convert_to_func_wrapper
from ...objects.integer import INTEGER_TYPE


def func_range(a, b, step=1):
    if not (compare_type(a, INTEGER_TYPE) and compare_type(b, INTEGER_TYPE)) \
            and compare_type(step, INTEGER_TYPE):

        return AILRuntimeError('a and b must be an integer!')

    va = unpack_ailobj(a)
    vb = unpack_ailobj(b)
    vs = unpack_ailobj(step)

    if va > vb:
        return convert_to_array([])
    return convert_to_array(list(range(va, vb, vs)))


_IS_AIL_MODULE_ = True
_AIL_NAMESPACE_ = {
    'range': convert_to_func_wrapper(func_range)
}
