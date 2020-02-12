
from core.error import AILRuntimeError
from objects.string import convert_to_string
from objects.struct import new_struct_object, convert_to_pyobj
from objects.null import null
from core.astate import MAIN_INTERPRETER_STATE
from objects.function import convert_to_func_wrapper
from core.aobjects import unpack_ailobj


def _err_to_string(this):
    this = convert_to_pyobj(this)

    msg = this.__this_err_msg
    type = this.__this_err_type
    where = this.__this_err_where

    return '%s%s : %s' % ('in %s :\n\t' % where if where else '',
                          type, where)


def make_err_struct_object(err_obj :AILRuntimeError, where :str):
    msg = err_obj.msg
    type = err_obj.err_type
    frame = err_obj.frame

    err_d = {
        'err_msg' : convert_to_string(msg),
        'err_type' : convert_to_string(type),
        'err_where' : convert_to_string(where),
        'to_string' : convert_to_func_wrapper(_err_to_string),
        '__frame' : frame
    }

    return new_struct_object('ERR_T', null, err_d, err_d.keys())


def catch_error():
    estack = MAIN_INTERPRETER_STATE.err_stack[::-1]

    return estack.pop() if estack else None


def throw_error(msg, etype=None):
    now_f = MAIN_INTERPRETER_STATE.frame_stack[-1]
    where = now_f.code.name

    msg = unpack_ailobj(msg)
    if type is not None:
        etype = unpack_ailobj(etype)

    if not (type(msg) == type(etype) == str):
        return AILRuntimeError('throw() needs 1 or 2 string as arguments.')

    erro = AILRuntimeError(msg, etype, now_f)

    MAIN_INTERPRETER_STATE.err_stack.append(
        make_err_struct_object(erro, where))
