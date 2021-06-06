import sys
import traceback

from time import ctime

from .acompiler import Compiler
from .abuiltins import BUILTINS as _BUILTINS
from .alex import Lex
from .aparser import Parser, ASTConverter
from .astate import MAIN_INTERPRETER_STATE
from .avm import Interpreter, Frame, InterpreterWrapper
from .version import AIL_VERSION, AIL_COPYRIGHT, AIL_INSTALL_TIME

from ..objects import function
from ..objects import string
from ..objects import null

from ..py_runtime.namespace import fill_namespace
from ..py_runtime.exceptions import print_py_traceback

from . import aobjects as objs, error, tokentype as tokent

import os

try:
    import readline
except ImportError:
    pass

error.ERR_NOT_EXIT = True
error.THROW_ERROR_TO_PYTHON = True

_MORE_KEYWORD = ('is', 'then', 'do', 'try', 'finally')
_END_KEYWORD = ('loop', 'end', 'endif', 'wend', 'catch')

_VER_STR = '%s' % AIL_VERSION if AIL_VERSION else ''
_WELCOME_STR = \
'''AIL %s (Python %s)
Type 'help(...)', '$help', 'copyright()', 'python_copyright()' to get more information, 'exit()' to exit.
''' % (
        _VER_STR, 
        sys.version
)

_SH_HELP_STR = \
'''AIL shell commands:
    $help   get commands help
    $exit   exit shell forcibly
    $break  break more mode forcibly
    $edit   editor mode
'''


def _sh_exit():
    sys.exit(0)


def _sh_copyright():
    return AIL_COPYRIGHT


def _py_copyright():
    return copyright()


_SHELL_NAMESPACE = {
    'exit': objs.convert_to_ail_object(_sh_exit),
    'copyright': objs.convert_to_ail_object(_sh_copyright),
    'python_copyright': objs.convert_to_ail_object(_py_copyright),
}

_SHELL_PYC_NAMESPACE = {
    'copyright': _sh_copyright,
    'python_copyright': copyright,
}

fill_namespace(_SHELL_PYC_NAMESPACE)


class Shell:
    def __init__(self):
        self.__buffer = []

        self.ps1 = '>> '
        self.ps2 = '.. '
        self.ps3 = '> '

        self.__more_level = 0

        self.__main_frame = Frame()

        self.__lexer = Lex()
        self.__parser = Parser()
        self.__compiler = Compiler(filename='<shell>', name='<string>')
        self.__converter = ASTConverter()
        
        self.__globals = _SHELL_NAMESPACE
        self.__pyc_globals = {}
        self.__pyc_globals.update(_SHELL_PYC_NAMESPACE)

    def __get_more_line_state(self, line: str) -> int:
        """
        :return : -1 end more | 0 normal | 1 start more
        """

        ts = Lex().lex(line)

        ignore_more = False
        hold_on_more = 0

        for index, tok in enumerate(ts.token_list):
            if tok.ttype == tokent.AIL_IDENTIFIER:
                if tok.value in _MORE_KEYWORD:
                    return 1
                if tok.value in _END_KEYWORD:
                    return -1
            elif tok.ttype == tokent.AIL_COLON and index == len(ts.token_list) - 1:
                return 1

        return hold_on_more

    @staticmethod
    def __print_welcome_text():
        print(_WELCOME_STR)

    def __run_single_line_pyc(self, line: str, block: bool=False):
        t = self.__lexer.lex(line, '<shell>')
        t = self.__parser.parse(t, line, '<shell>', True)
        n = self.__converter.convert_single(t)
        c = compile(n, '<shell>', 'single')
        
        try:
            interpreter = MAIN_INTERPRETER_STATE.global_interpreter
            MAIN_INTERPRETER_STATE.global_interpreter = InterpreterWrapper()
            exec(c, self.__pyc_globals)
        except Exception:
            print_py_traceback()
        finally:
            MAIN_INTERPRETER_STATE.global_interpreter = interpreter

    def __run_single_line_ail(self, line: str, block=False):
        single_line = not block

        t = self.__lexer.lex(line, '<shell>')
        t = self.__parser.parse(t, line, '<shell>')
        cobj = self.__compiler.compile(t, single_line=single_line).code_object
        
        cobj.is_main = True
        self.__main_frame.code = cobj
        self.__main_frame.varnames = cobj.varnames
        self.__main_frame.consts = cobj.consts
        
        MAIN_INTERPRETER_STATE.global_interpreter.exec(
            cobj, self.__main_frame, globals=self.__globals)

        if self.__main_frame.stack:
            tof = self.__main_frame.stack.pop()
            if tof is not null.null and tof is not None:
                print(repr(tof))

        MAIN_INTERPRETER_STATE.frame_stack.clear()

    __run_single_line = __run_single_line_pyc

    def __run_block(self):
        self.__run_single_line('\n'.join(self.__buffer), True)

        self.__buffer = []

    def __read_temp_file(self):
        return open(self.__temp_name).read()

    def run_shell(self):
        self.__run_shell()

    def __run_shell(self):
        self.__print_welcome_text()

        ps = self.ps1

        in_more = False
        in_edit = False
        run_buf = False

        while True:
            try:
                if run_buf:
                    run_buf = False
                    self.__run_block()
                
                line = input(ps)
                
                if not in_edit:
                    more = self.__get_more_line_state(line)

                if line == '$exit':
                    break

                elif line == '$break':
                    self.__buffer.clear()
                    self.__more_level = 0
                    in_more = False
                    ps = self.ps1
                    continue

                elif line == '$edit':
                    self.__buffer.clear()
                    self.__more_level = 0
                    in_edit = True
                    in_more = True
                    ps = self.ps3
                    print('(editor mode, ^C - cancel, ^D - run code.)')

                elif line == '$help':
                    print(_SH_HELP_STR)
                    continue

                elif more == 1:
                    self.__more_level += 1
                    in_more = True
                    ps = self.ps2
                    self.__buffer.append(line)

                elif more == -1:
                    self.__more_level -= 1 if self.__more_level > 0 else 0
                    self.__buffer.append(line)

                    if self.__more_level == 0:
                        in_more = False
                        ps = self.ps1
                        self.__run_block()

                elif self.__more_level >= 0:
                    if in_more:
                        self.__buffer.append(line)
                    else:
                        self.__run_single_line(line)

            except error.BuiltinAILRuntimeError as e:
                in_more = False
                print(str(e), end='')
                self.__main_frame.stack = []
                self.__buffer = []

            except EOFError as e:
                if not in_edit:
                    print()
                    break
                in_edit = False
                in_more = False
                ps = self.ps1
                self.__more_level = 0
                run_buf = True
                print()

            except KeyboardInterrupt as e:
                in_more = False
                if in_edit:
                    in_edit = False
                    ps = self.ps1

                print('\n%s' % str(type(e).__name__))
                self.__buffer = []

            self.__main_frame.variable['__temp__'] = '\n'.join(self.__buffer)


if __name__ == '__main__':
    Shell().run_shell()
