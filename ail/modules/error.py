
from ail.modules._error import get_err_struct
from ail.core.aobjects import AILObject, unpack_ailobj, convert_to_ail_object
from ail.core.astate import MAIN_INTERPRETER_STATE
from ail.core.error import AILRuntimeError


def error(err_type: AILObject, err_msg: AILObject) -> AILObject:
    """
    error(err_type: string, err_msg: string) -> Error
    @returns an Error object which can throw to AIL Runtime
    """
    err_type = unpack_ailobj(err_type)
    err_msg = unpack_ailobj(err_msg)

    if not isinstance(err_type, str) or not isinstance(err_msg, str):
        return AILRuntimeError(
                '\'err_type\' and \'err_msg\' must be string', 'TypeError')

    return MAIN_INTERPRETER_STATE.global_interpreter.make_runtime_error_obj(
            err_msg, err_type)


_IS_AIL_MODULE_ = True

_AIL_NAMESPACE_ = {
    'error': convert_to_ail_object(error),
    'Error': get_err_struct(),
}

