from time import (
    ctime,
    time_ns, time, strftime
)

from ail.api.object import *
from ail.api.error import AILRuntimeError


def time_nano_time():
    return time_ns()


def time_time():
    return time()


def time_format_time(format):
    format = object_unpack_ailobj(format)
    if not isinstance(format, str):
        return AILRuntimeError('required a string', 'TypeError')
    return strftime(format)


def time_ctime(second=None):
    if second is None:
        return ctime()
    second = object_unpack_ailobj(second)
    if type(second) not in (int, float):
        return AILRuntimeError('required integer or float', 'TypeError')
    return ctime(second)


_IS_AIL_MODULE_ = True
_AIL_NAMESPACE_ = {
    'nanoTime': time_nano_time,
    'time': time_time,
    'formatTime': time_format_time,
    'currentTime': time_ctime,
}

