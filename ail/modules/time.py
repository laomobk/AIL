from time import (
    ctime,
    time, strftime,
    sleep,
)

from ail.api.object import *
from ail.api.error import AILRuntimeError

_TIME_24H = 60*60*24


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


def time_sleep_micro(ms):
    ms = object_unpack_ailobj(ms)
    if not isinstance(ms, int):
        return AILRuntimeError('required integer', 'TypeError')
    sleep(ms * 1e-6)


def time_sleep(sec):
    sec = object_unpack_ailobj(sec)
    if type(sec) not in (int, float):
        return AILRuntimeError('required integer or float', 'TypeError')
    sleep(sec)


_IS_AIL_MODULE_ = True
_AIL_NAMESPACE_ = {
    'time': time_time,
    'formatTime': time_format_time,
    'currentTime': time_ctime,
    'sleep': time_sleep,
    'sleepMicro': time_sleep_micro,
    'sec_24h': _TIME_24H,
}

