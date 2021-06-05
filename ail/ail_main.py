# AIL Launcher

import os.path
import sys
from importlib import import_module
from .core import shared
from .core import aconfig
from .core.astate import MAIN_INTERPRETER_STATE
from .core.avmsig import WHY_HANDLING_ERR, WHY_ERROR
from .core.abuiltins import init_builtins
from .core.pyexec import exec_pyc_main
from .core.alex import Lex
from .core.aparser import Parser, ASTConverter
from .core.acompiler import Compiler
from .core.avm import Interpreter, InterpreterWrapper


from ._config import (
    AIL_DIR_PATH, BUILTINS_MODULE_PATH, CORE_PATH, LIB_PATH, CURRENT_WORK_PATH,
)

from . import _config

_HELP = r''' ail [filename] [--help | -h]'''


class _Option:
    def __init__(self):
        self.shell_mode = True
        self.filename = ''
        self.rest_args = []
        self.source = False


class ArgParser:
    def __init__(self):
        self.__now_arg_list = list()
        self.__now_arg_iter = None
        self.__has_next_arg = True
        self.__ok = True
        self.__now_single_arg = None

    def __next_arg(self) -> str:
        try:
            n = next(self.__now_arg_iter)
            self.__now_single_arg = n

            return n
        except StopIteration:
            self.__has_next_arg = False
            return None

    def _do_help(self, _):
        print(_HELP)
        self.__ok = -1

    def _do_v(self, _):
        _config.REMOVE_PY_RUNTIME_TRACEBACK = False
        self.__ok = True

    _do_h = _do_help

    def _do_s(self, opt: _Option):
        self.__ok = True
        opt.source = True

    def _do_literal(self, opt: _Option):
        n = self.__now_single_arg
        if n is not None:
            opt.shell_mode = False
            opt.filename = n

            return True
        self.__ok = False
        return False

    def _do_debug(self, opt: _Option):
        n = self.__next_arg()
        if n == 'show_syntax_error_frame':
            aconfig.DEBUG_SHOW_FRAME = True
        else:
            print('--debug: invalid debug setting')
            self.__ok = False
            return
        self.__ok = True

    _do_d = _do_debug

    def _do_old(self, _):
        aconfig.OLD_PRINT = True
        self.__ok = True

    def parse(self, arg_list: list) -> _Option:
        option = _Option()
        self.__now_arg_list = arg_list
        self.__now_arg_iter = iter(arg_list)

        if len(arg_list) == 0:
            return option

        arg = self.__next_arg()

        while self.__has_next_arg:
            if arg[:2] == '--':
                handler = getattr(
                    self, '_do_%s' % arg[2:], self._do_h)
                handler(option)
            elif arg[:1] == '-':
                handler = getattr(
                    self, '_do_%s' % arg[1:], self._do_h)
                handler(option)
            else:
                if self._do_literal(option):
                    break

            if self.__ok == -1:
                return None

            if not self.__ok:
                self._do_help(option)
                return None

            arg = self.__next_arg()

        option.rest_args = list(self.__now_arg_iter)

        return option


# load AIL_PATH in environ
shared.GLOBAL_SHARED_DATA.cwd = CURRENT_WORK_PATH
shared.GLOBAL_SHARED_DATA.ail_path = AIL_DIR_PATH
shared.GLOBAL_SHARED_DATA.boot_dir = os.getcwd()

shared.GLOBAL_SHARED_DATA.find_path = [
    BUILTINS_MODULE_PATH, LIB_PATH, CURRENT_WORK_PATH
]


def launch_py_test(test_name):
    try:
        mod = import_module('obj_test.%s' % test_name)
        if hasattr(mod, 'test'):
            mod.test()
        else:
            print('Test module do not have \'test\' function!')
    except ModuleNotFoundError:
        print('No test named \'%s\'' % test_name)


def _launch_main(argv: list, pyc_mode: bool = True) -> int:
    init_builtins()

    option = ArgParser().parse(argv)
    option.rest_args.insert(0, option.filename)
    shared.GLOBAL_SHARED_DATA.prog_argv = option.rest_args
    sys.argv = option.rest_args

    if option is None:
        return 1

    if option.shell_mode:
        from .core import ashell
        ashell.Shell().run_shell()
        return 0

    source_mode = option.source

    file_path = option.filename
    file_dir = os.path.dirname(
                os.path.normpath(
                    os.path.abspath(file_path)))

    shared.GLOBAL_SHARED_DATA.find_path.append(file_dir)

    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError('file \'%s\' not found' % file_path)

        source = open(file_path, encoding='UTF-8').read()

        if pyc_mode and not source_mode:
            MAIN_INTERPRETER_STATE.global_interpreter = InterpreterWrapper()
            return exec_pyc_main(source, file_path, dict())

        ast = Parser().parse(Lex().lex(source), source, file_path, source_mode)
        if source_mode:
            try:
                import astunparse

                from .core.version import AIL_VERSION, AIL_VERSION_STATE

                print('# file: %s' % file_path)
                print('# AST generated by AIL ASTConverter')
                print('# code generated by astunparse')
                print('# AIL %s' % AIL_VERSION)
                print()
                print(astunparse.unparse(ASTConverter().convert_module(ast)))
                return 0
            except (ModuleNotFoundError, ImportError):
                print('AIL: require module \'astunparse\'')
                return 1

        code_object = Compiler(
                ast, filename=file_path).compile(ast).code_object
        code_object.is_main = True

        why = MAIN_INTERPRETER_STATE.global_interpreter.exec(
                code_object)

        if why in (WHY_HANDLING_ERR, WHY_ERROR):
            return 1

    except FileNotFoundError as e:
        print('AIL: can\'t open file \'%s\': %s' % (file_path, str(e)))
        return 1


def launch_main(argv: list, pyc_mode: bool = True):
    try:
        return _launch_main(argv, pyc_mode)
    except SystemExit:
        return 0


if __name__ == '__main__':
    sys.exit(launch_main(sys.argv[1:]))

