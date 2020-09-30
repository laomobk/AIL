import time
import os.path


class Logger:
    WARRING = 'WARRING'
    ERROR = 'ERROR'
    NORMAL = 'NORMAL'

    def __init__(self, fpath='vmlog/'):
        self.__buffer = []

        if not os.path.exists(fpath) or os.path.isfile(fpath):
            os.mkdir(fpath)

        p = os.path.abspath(fpath)
        self.__file = open(os.path.join(p, self.__get_file_name()), 'w')

    def __get_file_name(self) -> str:
        return 'VMErrorLog [%s].log' % self.__now_time_str

    @property
    def __now_time_str(self):
        return time.strftime('%Y - %M - %d  %H : %m : %S')

    def __add_log(self, log_level: str, msg: str):
        self.__buffer.append(
            '[%s] [%s] [%s]' % (self.__now_time_str, log_level, msg)
        )

        self.flush()

    def warring(self, msg):
        self.__add_log(self.WARRING, msg)

    def error(self, msg):
        self.__add_log(self.ERROR, msg)

    def normal(self, msg):
        self.__add_log(self.NORMAL, msg)

    def flush(self):
        self.__file.write('\n'.join(self.__buffer))
        self.__buffer
