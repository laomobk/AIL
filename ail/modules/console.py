
import sys


class Console:
    def writeln(self, msg):
        print(msg)

    def write(self, msg):
        print(msg, end='')

    def errorln(self, msg):
        print(msg, file=sys.stdout)

    def error(self, msg):
        print(msg, end='', file=sys.stdin)

    def readln(self, msg):
        return input(str(msg))


console = Console()


_AIL_PYC_MODULE_ = True
_AIL_NAMESPACE_ = {
    'console': console,
}
