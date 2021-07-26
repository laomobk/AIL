
from sys import stdout
from sys import stderr

from ail.api.object import *
from ail.api.error import AILRuntimeError


_console_struct_object_cache = None


def _console_writeln(_, msg):
    msg = object_unpack_ailobj(msg)

    if not isinstance(msg, str):
        return AILRuntimeError('message must be a string', 'TypeError')

    stdout.write(msg + '\n')
    stdout.flush()


def _console_write(_, msg):
    msg = object_unpack_ailobj(msg)

    if not isinstance(msg, str):
        return AILRuntimeError('message must be a string', 'TypeError')

    stdout.write(msg)
    stdout.flush()


def _console_errorln(_, msg):
    msg = object_unpack_ailobj(msg)

    if not isinstance(msg, str):
        return AILRuntimeError('message must be a string', 'TypeError')

    stderr.write(msg + '\n')


def _console_error(_, msg):
    msg = object_unpack_ailobj(msg)

    if not isinstance(msg, str):
        return AILRuntimeError('message must be a string', 'TypeError')

    stderr.write(msg)


def _console_readln(_, msg):
    msg = object_unpack_ailobj(msg)

    if not isinstance(msg, str):
        return AILRuntimeError('message must be a string', 'TypeError')

    return input(msg)


def get_console_object() -> AILObject:
    global _console_struct_object_cache

    # cache
    if _console_struct_object_cache is not None:
        return _console_struct_object_cache

    obj_dict = {
        'write': object_convert_to_ail_object(_console_write),
        'writeln': object_convert_to_ail_object(_console_writeln),
        'error': object_convert_to_ail_object(_console_error),
        'errorln': object_convert_to_ail_object(_console_errorln),
        'readln': object_convert_to_ail_object(_console_readln),
    }

    _console_struct_object_cache = struct_new_struct_object(
        'console', null,
        obj_dict, list(obj_dict.keys())
    )

    return _console_struct_object_cache


_IS_AIL_MODULE_ = True
_AIL_NAMESPACE_ = {
    'console': get_console_object()
}
