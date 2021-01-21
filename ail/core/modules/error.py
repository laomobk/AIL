
from ail.core.modules._error import make_err_struct_object
from ail.core.aobjects import AILObject, unpack_ailobj
from ail.core.error import AILRuntimeError


def error(err_type: AILObject, err_msg: AILObject) -> AILObject:
    err_type = unpack_ailobj(err_type)
    err_msg = unpack_ailobj(err_msg)

    if not isinstance(err_type, str) or not isinstance(err_msg, str):
        return AILRuntimeError('\'err_type\' and \'err_msg\' must be string')

    err_obj = AILRuntimeError(err_type, err_msg)
    return make_err_struct_object(err_obj, '<Unknown>', -1)

