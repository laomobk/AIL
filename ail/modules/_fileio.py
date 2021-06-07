# file IO for AIL
from ail.core.error import AILRuntimeError

from ail.core.aobjects import (
    compare_type, has_attr, unpack_ailobj, ObjectCreater)

from ail.objects.struct import STRUCT_OBJ_TYPE, convert_to_pyobj, new_struct_object
from ail.objects.function import convert_to_func_wrapper
from ail.objects.null import null


def _convert_to_iobuffer(iobuffer):
    struct_d = {
        'close': convert_to_func_wrapper(_close),
        '__buffer': iobuffer,
        'closed': iobuffer.closed,
        'read': convert_to_func_wrapper(_read),
        'peek': convert_to_func_wrapper(_peek),
        'write': convert_to_func_wrapper(_write)
    }

    return new_struct_object('iobuffer_t', null, struct_d, struct_d.keys())


def _read(this, size):
    this = convert_to_pyobj(this)
    size = unpack_ailobj(size)
    buf = this.__this___buffer

    if type(size) != int:
        return AILRuntimeError('iobuffer.read() needs an integer.')

    try:
        if not buf.readable():
            return AILRuntimeError('not readable', 'OSError')

        return buf.read(size)
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonError')


def _write(this, string):
    this = convert_to_pyobj(this)
    string = unpack_ailobj(string)
    buf = this.__this___buffer

    if type(string) != str:
        return AILRuntimeError('iobuffer.write() needs a string.')

    try:
        if not buf.writable():
            return AILRuntimeError('not writeable', 'OSError')

        return buf.write(string)
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonError')


def _close(this):
    this = convert_to_pyobj(this)
    try:
        this.__this___buffer.close()
        this.__this_closed = True
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonError')


def _peek(this, size):
    this = convert_to_pyobj(this)
    size = unpack_ailobj(size)

    if type(size) != int:
        return AILRuntimeError('iobuffer.peek() needs an integer.')

    try:
        return this.__this___buffer.peek(size)
    except Exception as e:
        return AILRuntimeError(str(e), 'PythonError')


def _open(fp, mode):
    fp = unpack_ailobj(fp)
    mode = unpack_ailobj(mode)

    if not (type(fp) == type(mode) == str):
        return AILRuntimeError('open() needs 2 string as argument')

    try:
        iobuf = open(fp, mode)
    except FileNotFoundError:
        return null
    except OSError as e:
        return AILRuntimeError(str(e), 'OSError')
    except Exception as e:
        return AILRuntimeError(str(e), 'RuntimeError')

    return _convert_to_iobuffer(iobuf)
