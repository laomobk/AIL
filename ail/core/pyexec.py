# python compatible
import dis
from sys import stderr

from .acompile import Compiler, Assembler
from .alex import Lex
from .aparser import ASTConverter, Parser
from .error import AILSyntaxError

from . import AIL_PY_GLOBAL
from ail.core.namespace import fill_namespace
from ail.core.exceptions import print_py_traceback


_globals = globals


SIG_OK = 0
SIG_EXCEPTION = 1
SIG_STOP = 3
SIG_SYSTEM_EXIT = 2


CP_PY_AST = 0x1
CP_PY_CODE = 0x2
AIL_CP_MODES = ('exec', 'eval', 'single')


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


def _ail_exec(
        source: str, filename: str, globals: dict, main: bool = True,
        compiler=CP_PY_AST) -> int:
    """
    :return: code: 0 -> ok | 1 -> exception occurred | 2 -> system exit
    """

    code = ail_compile(source, filename, 'exec', compiler=compiler)

    name = '__main__'

    if not main:
        name = filename

    fill_namespace(globals, name, main, filename=filename)

    if compiler == CP_PY_CODE:
        print('Warning: AIL is running in self compilation mode, '
              'some features in may not supported.', file=stderr)

    exec(code, globals)
    return 0


def ail_exec(source: str, filename: str, globals: dict, compiler=CP_PY_AST) -> int:
    try:
        return _ail_exec(source, filename, globals, compiler=compiler)
    except Exception:
        print_py_traceback()
        return 1
    except (KeyboardInterrupt, EOFError):
        print_py_traceback()
        return 0


def ail_parse_ail_ast(source: str, filename: str, mode: str, flags: int):
    if mode not in AIL_CP_MODES:
        raise ValueError('compile mode must in (%s, %s %s)' %
                         tuple((repr(x) for x in AIL_CP_MODES)))

    ts = Lex().lex(source, filename)
    return Parser().parse(ts, source, filename, flags & CP_PY_AST == 1, mode == 'eval')


def ail_parse_pyast(source: str, filename: str, mode: str, flags: int):
    converter = ASTConverter()
    conv_func = {
        'eval': converter.convert_eval,
        'exec': converter.convert_module,
        'single': converter.convert_single,
    }.get(mode, None)

    return conv_func(ail_parse_ail_ast(source, filename, mode, flags))


def ail_eval(source, globals=None, locals=None):
    l = Lex()
    ts = l.lex(source, '<eval>')

    p = Parser()
    node = p.parse(ts, source, '<eval>', True, True)

    converter = ASTConverter()
    code = compile(converter.convert_eval(node), '<eval>', 'eval')

    if globals is None:
        globals = {}

    fill_namespace(globals)

    return eval(code, globals, locals)


def ail_compile(
        source: str, filename: str, mode: str, flags: int = 0, compiler: int = CP_PY_AST):

    if compiler == CP_PY_CODE:
        from sys import version_info
        if version_info.major < 3 or version_info.minor != 8:
            raise PythonVersionError(
                'native compile mode must run on Python 3.8.x, but got %s.%s.%s' %
                (version_info.major, version_info.minor, version_info.micro))

    if mode not in AIL_CP_MODES:
        raise ValueError('compile mode must in ()' % (repr(x) for x in AIL_CP_MODES))

    eval_mode = mode == 'eval'
    single_mode = mode == 'single'

    ts = Lex().lex(source, filename)
    node = Parser().parse(ts, source, filename, flags & CP_PY_AST == 1, eval_mode)

    if compiler == CP_PY_AST:
        converter = ASTConverter()
        if single_mode:
            code = compile(
                converter.convert_single(node),
                filename, 'single')
        else:
            code = compile(
                converter.convert_module(node),
                filename, 'eval' if eval_mode else 'exec')
    elif compiler == CP_PY_CODE:
        compiler = Compiler()
        compiler.compile(node, source, filename, mode=mode)
        code = Assembler().assemble(compiler.unit.top_block, compiler)
    else:
        raise ValueError('Invalid flag: %s' % flags)

    return code


class PythonVersionError(Exception):
    pass


if __name__ == '__main__':
    _test_run()

