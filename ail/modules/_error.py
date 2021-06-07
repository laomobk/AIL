import sys

from ail.core.error import AILRuntimeError, get_line_from_file
from ail.objects.struct import new_struct_object, convert_to_pyobj, new_struct
from ail.core.astate import MAIN_INTERPRETER_STATE
from ail.core.aobjects import unpack_ailobj, convert_to_ail_object


_ERR_STRUCT_MEMBERS = [
    'err_msg',
    'err_type',
    'err_where',
    'err_filename',
    '__lineno',
    '__frame',
]

_ERR_STRUCT_TEMP = None


def _err_to_string(this):
    this = convert_to_pyobj(this)

    lno = this.__this___lineno
    frame = this.__this___frame
    msg = this.__this_err_msg
    type = this.__this_err_type
    where = frame.code.name
    filename = frame.code.filename

    source_line = get_line_from_file(lno, filename)
    line_detail = ''

    if source_line != '':
        line_detail = '    %s\n' % source_line

    return '%s%s%s: %s' % ('  File \'%s\', line %s, in %s\n' %
                            (filename, lno, where) if where else '',
                            line_detail, type, msg)


def _err_eq(this, type_name):
    return this.members['err_type'] == type_name


def _err_init(this, msg, type):
    this.members['err_msg'] = str(msg)
    this.members['err_type'] = str(type)


def get_err_struct():
    global _ERR_STRUCT_TEMP

    if _ERR_STRUCT_TEMP is None:
        _ERR_STRUCT_TEMP = new_struct(
            'Error', _ERR_STRUCT_MEMBERS, _ERR_STRUCT_MEMBERS)
        _ERR_STRUCT_TEMP['__bind_functions__'] = {
            '__init__': convert_to_ail_object(_err_init),
            '__eq__': convert_to_ail_object(_err_eq),
            'toString': convert_to_ail_object(_err_to_string),
        }

    return _ERR_STRUCT_TEMP


def make_err_struct_object(err_obj: AILRuntimeError, where: str, lineno: int = -1):
    msg = err_obj.msg
    type = err_obj.err_type
    frame = err_obj.frame
    filename = frame.code.filename

    err_d = {
        'err_msg': convert_to_ail_object(msg),
        'err_type': convert_to_ail_object(type),
        'err_where': convert_to_ail_object(where),
        'err_filename': convert_to_ail_object(filename),
        'toString': convert_to_ail_object(_err_to_string),
        '__lineno': lineno,
        '__frame': frame,
        '__eq__': convert_to_ail_object(_err_eq),
        '__init__': convert_to_ail_object(_err_init),
    }

    err_struct = new_struct_object(str(type), get_err_struct(), err_d, list(err_d.keys()))
    err_struct.error_object = err_obj

    return err_struct


def catch_error():
    estack = MAIN_INTERPRETER_STATE.err_stack[::-1]
    te = estack.pop() if estack else None

    return te


def print_all_error(exit=False, exit_code=1):
    es = MAIN_INTERPRETER_STATE.err_stack[::-1]

    for e in es:
        eo = convert_to_pyobj(e)
        print(unpack_ailobj(eo.__this_to_string)(e))

    if exit:
        sys.exit(exit_code)


# for AIL Runtime
print_err = lambda: print_all_error(False)


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
