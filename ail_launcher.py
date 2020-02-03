# AIL Launcher

import sys
from importlib import import_module
import ashell

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
    if len(argv) == 0:
        ashell.Shell().run_shell()
        return

    if len(argv) > 1:
        print('Usage : ./ail_launcher.py file')
        sys.exit(1)

    fpath = argv[0]

    try:
        from alex import Lex
        from aparser import Parser
        from acompiler import Compiler
        from avm import Interpreter

        ast = Parser(Lex(fpath).lex(), fpath).parse()
        Interpreter().exec(Compiler(ast, filename=fpath).compile(ast).code_object)

    except Exception as e:
        print('AIL : can\'t open file \'%s\' : %s' % str(e))
        sys.exit(1)


if __name__ == '__main__':
    launch_main(sys.argv[1:])
