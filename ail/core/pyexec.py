# python compatible

from .alex import Lex
from .aparser import ASTConverter, Parser

from ..py_runtime.namespace import fill_namespace
from ..py_runtime.exceptions import print_py_traceback


SIG_OK = 0
SIG_EXCEPTION = 1
SIG_STOP = 3
SIG_SYSTEM_EXIT = 2


class StopExec(BaseException):
    pass


def _test_run():

    source = open('./tests/test.ail').read()
    l = Lex()
    ts = l.lex(source)

    p = Parser()
    t = p.parse(ts, source, '<test>', True)

    converter = ASTConverter()
    code = compile(converter.convert_module(t), './tests/test.ail', 'exec')

    exec(code, AIL_PY_GLOBAL)


def exec_as_python(source: str, filename: str, globals: dict) -> int:
    """
    :return: code: 0 -> ok | 1 -> exception occurred | 2 -> system exit
    """
    l = Lex()
    ts = l.lex(source, filename)

    p = Parser()
    node = p.parse(ts, source, filename, True)

    converter = ASTConverter()
    code = compile(converter.convert_module(node), filename, 'exec')

    fill_namespace(globals)
    
    try:
        exec(code, globals)
        return 0
    except StopExec:
        return 1


def exec_pyc_main(source: str, filename: str, globals: dict) -> int:
    try:
        return exec_as_python(source, filename, globals)
    except Exception:
        print_py_traceback()
        return 1


if __name__ == '__main__':
    _test_run()

