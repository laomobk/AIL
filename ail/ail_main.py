# AIL Launcher

import os.path
import sys
from importlib import import_module
from .core import shared

from ._config import (
    AIL_DIR_PATH, BUILTINS_MODULE_PATH, CORE_PATH, LIB_PATH
)


# load AIL_PATH in environ
shared.GLOBAL_SHARED_DATA.cwd = os.getcwd()
shared.GLOBAL_SHARED_DATA.ail_path = AIL_DIR_PATH


def init_paths():
    # init_lib_path
    shared.GLOBAL_SHARED_DATA.find_path = [
        BUILTINS_MODULE_PATH, CORE_PATH, LIB_PATH
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


def launch_main(argv :list):
    init_paths()

    if len(argv) == 0:
        from .core import ashell
        ashell.Shell().run_shell()
        return

    if len(argv) > 1:
        print('Usage : ail file')
        sys.exit(1)

    fpath = argv[0]

    try:
        from .core.alex import Lex
        from .core.aparser import Parser
        from .core.acompiler import Compiler
        from .core.avm import Interpreter

        ast = Parser(fpath).parse(Lex(fpath).lex())
        Interpreter().exec(Compiler(ast, filename=fpath).compile(ast).code_object)

    except FileNotFoundError as e:
        print('AIL : can\'t open file \'%s\' : %s' % (fpath, str(e)))
        sys.exit(1)


if __name__ == '__main__':
    launch_main(sys.argv[1:])
