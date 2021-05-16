# python compatible

from .alex import Lex
from .aparser import ASTConverter, Parser

from ..py_runtime import AIL_PY_GLOBAL


def _test_run():

    source = open('./tests/test.ail').read()
    l = Lex()
    ts = l.lex(source)

    p = Parser()
    t = p.parse(ts, source, '<test>', True)

    converter = ASTConverter()
    code = compile(converter.convert_module(t), './tests/test.ail', 'exec')

    exec(code, AIL_PY_GLOBAL)


def exec_as_python(source: str, filename: str, globals: dict, locals: dict):
    l = Lex()
    ts = l.lex(source, filename)

    p = Parser()
    node = p.parse(ts, source, filename, True)

    converter = ASTConverter()
    code = compile(converter.convert_module(node), filename, 'exec')

    globals.update(AIL_PY_GLOBAL)

    exec(code, globals, locals)


if __name__ == '__main__':
    _test_run()

