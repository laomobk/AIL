import sys

from .acompiler import Compiler
from .abuiltins import BUILTINS as _BUILTINS
from .alex import Lex
from .aparser import Parser
from .astate import MAIN_INTERPRETER_STATE
from .avm import Interpreter, Frame
from .version import AIL_VERSION, AIL_COPYRIGHT

from ..objects import function
from ..objects import string
from ..objects import null

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


def _sh_exit():
    sys.exit(0)


def _sh_copyright():
    return AIL_COPYRIGHT


_SHELL_NAMESPACE = {
    'exit': objs.convert_to_ail_object(_sh_exit),
    'copyright': objs.convert_to_ail_object(_sh_copyright),
}


class Shell:
    def __init__(self):
        self.__buffer = []

        self.ps1 = '>> '
        self.ps2 = '.. '

        self.__more_level = 0

        self.__main_frame = Frame()

        self.__lexer = Lex()
        self.__parser = Parser()
        self.__compiler = Compiler(filename='<shell>', name='<string>')
        
        self.__globals = _SHELL_NAMESPACE

    def __get_more_line_state(self, line: str) -> int:
        """
        :return : -1 end more | 0 normal | 1 start more
        """

        ts = Lex().lex(line)

        ignore_more = False
        hold_on_more = 0

        for tok in ts.token_list:
            if tok.ttype == tokent.AIL_IDENTIFIER:
                if tok.value in _MORE_KEYWORD:
                    return 1
                if tok.value in _END_KEYWORD:
                    return -1
            elif tok.ttype == tokent.AIL_COLON:
                return 1
            elif tok.ttype == tokent.AIL_LLBASKET:
                if hold_on_more == 0:
                    return 1
                return 0
            elif tok.ttype == tokent.AIL_LRBASKET:
                hold_on_more = -1

        return hold_on_more

    @staticmethod
    def __print_welcome_text():
        v = ''

        try:
            v = AIL_VERSION
        except KeyError:
            pass

        print('AIL shell %s' % ('(AIL version = %s)' % v) if v else '')
        print('Type \'exit()\' to exit.\n')

    def __run_single_line(self, line: str, block=False):
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
        MAIN_INTERPRETER_STATE.frame_stack.clear()

        if self.__main_frame.stack:
            tof = self.__main_frame.stack.pop()
            if tof is not null.null and tof is not None:
                print(repr(tof))

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

        while True:
            try:
                line = input(ps)

                more = self.__get_more_line_state(line)

                if line == '!exit!':
                    break

                if line == '!break!':
                    self.__buffer.clear()
                    self.__more_level = 0
                    in_more = False
                    ps = self.ps1
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

            except error._AILRuntimeError as e:
                in_more = False
                print(str(e), end='')
                self.__main_frame.stack = []
                self.__buffer = []

            except EOFError as e:
                print()
                break

            except KeyboardInterrupt as e:
                in_more = False
                print('\n%s' % str(type(e).__name__))
                self.__buffer = []

            self.__main_frame.variable['__temp__'] = '\n'.join(self.__buffer)


if __name__ == '__main__':
    Shell().run_shell()
