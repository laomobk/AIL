from time import (
    ctime,
    time, strftime,
    sleep,
)


_TIME_24H = 60*60*24


def time_time():
    return time()


def time_format_time(format):
    return strftime(format)


def time_ctime(second=None):
    if second is None:
        return ctime()
    return ctime(second)


def time_sleep_micro(ms):
    sleep(ms * 1e-6)


def time_sleep(sec):
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

