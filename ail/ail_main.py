# AIL Launcher

import os.path
import sys
from importlib import import_module
from .core import shared
from .core.avmsig import WHY_HANDLING_ERR, WHY_ERROR

from ._config import (
    AIL_DIR_PATH, BUILTINS_MODULE_PATH, CORE_PATH, LIB_PATH, CURRENT_WORK_PATH,
)

_HELP = r''' ail [filename] [--help | -h]'''


class _Option:
    def __init__(self):
        self.shell_mode = True
        self.filename = None
        self.rest_args = []


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
        self.__ok = False

    _do_h = _do_help

    def _do_literal(self, opt: _Option):
        n = self.__now_single_arg
        if n is not None:
            opt.shell_mode = False
            opt.filename = n

            return True
        self.__ok = False
        return False

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
                    self, '_do_%s' % arg[2:], self._do_h)
                handler(option)
            else:
                if self._do_literal(option):
                    break

            if not self.__ok:
                self._do_help()
                return None

            arg = self.__next_arg()

        option.rest_args = list(self.__now_arg_iter)

        return option


# load AIL_PATH in environ
shared.GLOBAL_SHARED_DATA.cwd = CURRENT_WORK_PATH
shared.GLOBAL_SHARED_DATA.ail_path = AIL_DIR_PATH
shared.GLOBAL_SHARED_DATA.boot_dir = os.getcwd()


def init_paths():
    # init_lib_path
    shared.GLOBAL_SHARED_DATA.find_path = [
        BUILTINS_MODULE_PATH, CORE_PATH, LIB_PATH, CURRENT_WORK_PATH
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


def launch_main(argv: list) -> int:
    init_paths()

    option = ArgParser().parse(argv)

    if option.shell_mode:
        from .core import ashell
        ashell.Shell().run_shell()
        return 0

    if option is None:
        return 1

    file_path = option.filename
    file_dir = os.path.dirname(
                os.path.normpath(
                    os.path.abspath(file_path)))

    shared.GLOBAL_SHARED_DATA.find_path.append(file_dir)

    try:
        from .core.alex import Lex
        from .core.aparser import Parser
        from .core.acompiler import Compiler
        from .core.avm import Interpreter

        if not os.path.exists(file_path):
            raise FileNotFoundError('file \'%s\' not found' % file_path)

        ast = Parser(file_path).parse(Lex(file_path).lex())
        code_object = Compiler(
                ast, filename=file_path).compile(ast).code_object
        code_object.is_main = True

        why = Interpreter(option.rest_args).exec(code_object)
        if why in (WHY_HANDLING_ERR, WHY_ERROR):
            return 1

    except FileNotFoundError as e:
        print('AIL: can\'t open file \'%s\': %s' % (file_path, str(e)))
        return 1


if __name__ == '__main__':
    sys.exit(launch_main(sys.argv[1:]))
