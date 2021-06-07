
import sys

from ail.core.version import AIL_VERSION


class System:
    @staticmethod
    def println(*args):
        print(*args)

    @staticmethod
    def print(*args):
        print(*args, end='')

    @staticmethod
    def printf(text, *format):
        print(text % format, end='')

    @property
    def py_version(self):
        return sys.version

    @property
    def version(self):
        return AIL_VERSION

    @property
    def stdout(self):
        return sys.stdout

    @stdout.setter
    def stdout(self, file):
        sys.stdout = file

    @property
    def stdin(self):
        return sys.stdin

    @stdin.setter
    def stdin(self, file):
        sys.stdin = file

    @property
    def stderr(self):
        return sys.stderr

    @stderr.setter
    def stderr(self, file):
        sys.stderr = file


SYSTEM_OBJECT = System()

_AIL_PYC_MODULE_ = True
_AIL_NAMESPACE_ = {
    'System': System,
    'system': SYSTEM_OBJECT,
}
