
from sys import stdout
from sys import stderr


class Console:
    def __init__(self):
        self._out_file = stdout
        self._err_file = stderr

    def writeln(self, msg):
        out = self._out_file
        out.write(str(msg) + '\n')
        out.flush()


    def write(self, msg):
        out = self._out_file
        out.write(str(msg))
        out.flush()

    def errorln(self, msg):
        err = self._err_file
        err.write(msg + '\n')
        err.flush()

    def error(self, msg):
        err = self._err_file
        err.write(msg)
        err.flush()

    def readln(self, msg):
        return input(str(msg))


console = Console()


_AIL_PYC_MODULE_ = True
_AIL_NAMESPACE_ = {
    'console': console,
}
